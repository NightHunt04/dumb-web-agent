from ..executor import AgentExecutor
from ..state import AgentState
from ...message import SystemMessage, UserMessage
from ..utils import extract_json
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from colorama import Fore, Style
from datetime import datetime
from json import JSONDecodeError
import asyncio
import json
import os

class AgentGraph:
    """
    Manages the stateful, cyclical execution of the web agent using a LangGraph state machine.

    This class defines the core logic loop of the agent:
    1. The agent thinks about the next step (`model_node`).
    2. A router (`_router`) decides whether to act or to finish.
    3. The agent acts upon the web page using a tool (`tool_node`).
    4. The agent prepares a final response (`output_node`).

    The graph structure ensures a continuous loop of `model_node` -> `tool_node` -> `model_node`
    until the task is completed, at which point it routes to the `output_node` and ends.

    Attributes:
        _executor (AgentExecutor): An instance containing the tools, model, and browser state.
        _agent_state (AgentState): The TypedDict class defining the graph's state structure.
        _graph (CompiledStateGraph): The compiled, runnable LangGraph object.
    """

    def __init__(self, executor: AgentExecutor, agent_state: AgentState) -> None:
        self._executor = executor
        self._agent_state = agent_state 
        self._graph = self.create_graph()
    
    async def model_node(self, state: AgentState) -> AgentState:
        """
        The "brain" of the agent. It decides the next action based on the current state.

        This node builds a comprehensive prompt including the user's query, a summary of
        previous actions, and the current state of the web page's DOM. It then calls the
        language model to get the next `thought`, `tool_name`, and `tool_args`.

        Args:
            state (AgentState): The current state of the graph.

        Returns:
            dict: A dictionary containing the `response` from the model to update the state.
        """

        system_prompt = SystemMessage(content = self._executor._system_prompt).to_dict()
        user_prompt = UserMessage(content = f'User Query: {state["input"]}').to_dict()
        model_messages = [system_prompt, user_prompt]
        self._executor._model.messages = model_messages

        if state.get('previous_actions'):
            history = []
            for ind, action in enumerate(state['previous_actions']):
                # if len(action) == 4:
                thought = action.get('thought')
                tool_call = action.get('tool_name')
                tool_args = action.get('tool_args')
                tool_response = action.get('tool_response')
                
                if isinstance(tool_response, list):
                    response_summary = f"Successfully scraped {len(tool_response)} items."
                else:
                    response_summary = str(tool_response)[:500] 

                if ind == len(state['previous_actions']) - 1:
                    history.append(f"LAST ACTION:\nThought: {thought}\nTool Call: {tool_call}\nTool Args: {tool_args}\nResponse: {response_summary}")
                else:
                    history.append(f"Step {ind + 1}: Called tool: `{tool_call}`\nArgs: {tool_args}")
                
            history_str = "\n".join(history)
            self._executor._model.add_message(UserMessage(content = f'Previous Actions Summary:\n{history_str}').to_dict())
            self._executor._model.add_message(UserMessage(content = f"Current interactive elements on the page:\n{state.get('page_state').get('interactive_elements')}").to_dict())
            # self._executor._model.add_message(UserMessage(content = f"Current informative elements on the page:\n{state.get('page_state').get('informative_elements')}").to_dict())
            # self._executor._model.add_message(UserMessage(content = f"Current scrollable elements on the page:\n{state.get('page_state').get('scrollable_elements')}").to_dict())

        try:
            response = await self._executor._model.generate()
            # response_content = response['choices'][0]['message']['content']
            response_content = response.choices[0].message.content
            json_response = extract_json(response_content)

            print(Fore.CYAN + Style.BRIGHT + f'Iteration: {self._executor._iterations}' + Style.RESET_ALL)
            print(Fore.GREEN + Style.BRIGHT + f'Model thought: {json_response.get("thought")}' + Style.RESET_ALL)

            if json_response is not None:
                return { 'response': json_response }
            else: 
                return { 
                    'response': {
                        'tool_name': '',
                        'tool_args': {},
                        'thought': 'The response from the model was not a valid JSON object. Please try again.',
                        'observation': 'The response from the model was not a valid JSON object. Please try again.'
                    } 
                }
        except Exception as e:
            return { 
                'response': {
                    'tool_name': '',
                    'tool_args': {},
                    'thought': f'An error occurred while generating a response: {str(e)}',
                    'observation': f'An error occurred while generating a response: {str(e)}'
                } 
            }
        
    async def tool_node(self, state: AgentState) -> dict:
        """
        It executes the tool call planned by the model_node.
        Calls the tool from the given tool_call along with the tool_args provided by the model_node.

        Args:
            state (AgentState): The current state of the graph.

        Returns:
            dict: A dictionary with updates for `page_state`, `previous_actions`, and `scraped_data`.
        """

        tool_name = state.get('response', {}).get('tool_name')
        tool_args = state.get('response', {}).get('tool_args', {})

        result = await self._executor._execute_tool(tool_name, tool_args, state)
        tool_response = f"Error: Tool '{tool_name}' not found or failed to execute."

        scraped_data_accumulator = state.get('scraped_data', [])
        if result:
            tool_response = result.tool_response
            scraped_data_accumulator = result.scraped_data_accumulator

        page_state_dict = {}
        try:
            dom_state = await self._executor.dom.get_state()
            page_state_dict = {
                'interactive_elements': self._executor.dom.format_elements_for_prompt(dom_state.get('interactive_elements', [])),
                'informative_elements': self._executor.dom.format_elements_for_prompt(dom_state.get('informative_elements', [])),
                'scrollable_elements': self._executor.dom.format_elements_for_prompt(dom_state.get('scrollable_elements', []))
            }
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + '❗' + f"Error getting DOM state: {e}" + Style.RESET_ALL)

        new_action = {
            'thought': state.get('response', {}).get('thought', ''),
            'tool_name': tool_name,
            'tool_args': tool_args,
            'tool_response': tool_response
        }
        all_actions = state.get('previous_actions', [])
        all_actions.append(new_action)

        # screenshot at each step
        if state.get('screenshot_each_step'):
            path = os.path.join(os.path.dirname(__file__), '../../../screenshots/')
            if not os.path.exists(path):
                os.makedirs(path)
            await self._executor._page.screenshot(path=os.path.join(path, f'screenshot_{self._executor._session}_{self._executor._iterations}.png'))

        return {
            "page_state": page_state_dict,
            "previous_actions": all_actions,
            "scraped_data": scraped_data_accumulator
        }

    async def output_node(self, state: AgentState) -> AgentState:
        """
        The final node in the graph. It prepares the agent's definitive final answer for the user.

        It implements the "Data-First" architecture:
        1. It first checks if any data has been collected in the `scraped_data` field.
        2. If data exists, it returns that data directly, providing a fast and efficient
           path for scraping tasks. It formats the output based on the data type.
        3. If no data exists, it calls the LLM to generate a human-readable
           summary of the agent's actions.

        Args:
            state (AgentState): The final state of the graph.

        Returns:
            dict: A dictionary containing the final `output` for the user.
        """

        steps = []
        if state.get('memorize'):
            MEMORY_PATH_DIR = os.path.join(os.path.dirname(__file__), '../../memory')
            MEMORY_PATH = os.path.join(MEMORY_PATH_DIR, 'memory.json')

            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + '* Saving successful steps to the memory' + Style.RESET_ALL)

            if not os.path.exists(MEMORY_PATH_DIR):
                os.makedirs(MEMORY_PATH_DIR)

            if os.path.exists(MEMORY_PATH):
                try:
                    with open(MEMORY_PATH, 'r') as f:
                        memory = json.load(f)
                except JSONDecodeError as e:
                    print(Fore.RED + Style.BRIGHT + '❗' + f"Error loading memory: {e}" + Style.RESET_ALL)
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + '* Resetting memory' + Style.RESET_ALL)
                    memory = []
            else:
                memory = []

            steps = []
            for action in state.get('previous_actions', []):
                if 'Error' not in action['tool_response']:
                    steps.append({
                        'thought': action['thought'],
                        'tool_call': action['tool_name'],
                        'tool_args': action['tool_args'],
                        'tool_response': action['tool_response'] if isinstance(action['tool_response'], str) else "Scraped data"
                    })

            memory.append({
                'session': self._executor._session,
                'input': state.get('input'),
                'steps': steps,
                'created_at': datetime.now().isoformat()
            })

            try:
                with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
                    json.dump(memory, f, indent=4, ensure_ascii=False)
                
                print(Fore.GREEN + Style.BRIGHT + '* Steps memorized successfully')
                print(Fore.GREEN + Style.BRIGHT + '* Memory path: ' + MEMORY_PATH + Style.RESET_ALL)
                print(Fore.GREEN + Style.BRIGHT + '* Session: ' + self._executor._session + Style.RESET_ALL)
            except JSONDecodeError as e:
                print(Fore.RED + Style.BRIGHT + '❗' + f"Error saving memory: {e}" + Style.RESET_ALL)

        if state.get('scraped_data'):
            if isinstance(state.get('scraped_data')[0], dict):
                return { 
                    'output': state.get('scraped_data'), 
                    'memorized_steps': steps 
                }
            else:
                return { 
                    'output': '\n'.join(state.get('scraped_data') if state.get('scraped_data') else []), 
                    'memorized_steps': steps 
                }

        try:
            system_prompt = SystemMessage(content=self._executor._output_prompt).to_dict()
            # history = "\n".join([f"Step {i+1}: {action[0]}" for i, action in enumerate(state.get('previous_actions', []))])
            history = "\n".join([f"Step {i + 1}: {action['thought']}" for i, action in enumerate(state.get('previous_actions', []))])

            messages = [
                system_prompt,
                UserMessage(content=f'User Query: {state.get("input")}').to_dict(),
                UserMessage(content=f'Summary of Actions Taken:\n{history}').to_dict()
            ]
            
            self._executor._model.messages = messages
            response = await self._executor._model.generate()
            response_content = response['choices'][0]['message']['content']
            final_output = json.loads(response_content).get("response", "Task completed.")

            return {
                'output': final_output, 
                'memorized_steps': steps
            }
        except Exception as e:
            return { 
                'response': f'An error occurred while generating a response: {str(e)}', 
                'memorized_steps': steps 
            }

    async def _router(self, state: AgentState) -> AgentState:
        """
        A conditional edge that directs the flow of the graph after the model_node.

        Args:
            state (AgentState): The current state of the graph, containing the latest `response`.

        Returns:
            str: The name of the next node to execute ('call_tool' or 'call_output').
        """

        if state.get('wait_between_actions') > 0:
            if state.get('verbose'):
                print(Fore.YELLOW + Style.BRIGHT + f'Waiting for {state.get('wait_between_actions')} seconds' + Style.RESET_ALL)
            await asyncio.sleep(state.get('wait_between_actions'))

        self._executor._iterations += 1
        tool_name = state.get('response', {}).get('tool_name', '').lower().strip()
        if tool_name == 'finish':
            return 'call_output'
        return 'call_tool'

    def create_graph(self) -> CompiledStateGraph:
        graph = StateGraph(AgentState)
        graph.add_node('model_node', self.model_node)
        graph.add_node('tool_node', self.tool_node)
        graph.add_node('output_node', self.output_node)
        
        graph.add_conditional_edges(
            'model_node',
            self._router,
            {
                'call_tool': 'tool_node',
                'call_output': 'output_node'
            }
        )
        graph.add_edge('tool_node', 'model_node')
        graph.add_edge('output_node', END)
        graph.set_entry_point('model_node')

        return graph.compile()
