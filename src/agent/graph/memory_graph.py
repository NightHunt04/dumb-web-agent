from ..executor import AgentExecutor
from ..state import MemoryState
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from colorama import Fore, Style
import asyncio
import os

class MemoryGraph:
    """
    Manages the deterministic replay of a saved agent session from memory.

    This class constructs a LangGraph state machine designed to execute a pre-recorded
    sequence of tool calls in order, rather than using an LLM to decide on each step.
    It's used for re-running, testing, or demonstrating a previously successful agent task.

    Note: No error response will be sent to LLM if the tool call fails.

    The graph structure is a simple loop that progresses through the saved steps:
    1. Execute the current step (`step_execution_node`).
    2. The router (`_router`) checks if more steps remain.
    3. If yes, loop back to the execution node. If no, proceed to the final output.
    4. Prepare the final response (`final_output_node`).

    Attributes:
        _executor (AgentExecutor): The execution environment for the agent.
        _memory_state (MemoryState): The TypedDict class defining the graph's state.
    """

    def __init__(self, executor: AgentExecutor, memory_state: MemoryState) -> None:
        self._executor = executor
        self._memory_state = memory_state 
    
    async def step_execution_node(self, state: MemoryState) -> MemoryState:
        """
        Executes a single, pre-recorded step from the agent's memory (particularly stored in json format,
        which is nothing but the `previous_actions` but only those whose tool_response does not contain any error).

        This node reads the `tool_call` and `tool_args` for the current step index,
        delegates the execution to the `AgentExecutor`, and updates the state with the
        result. It then increments the step index to prepare for the next iteration.

        Args:
            state (MemoryState): The current state of the graph.

        Returns:
            dict: A dictionary containing the updated `scraped_data`, `step_results`,
                  and the incremented `current_step_index`.
        """

        current_step_index = state.get('current_step_index')
        tool_name = state.get('steps')[current_step_index].get('tool_call')
        tool_args = state.get('steps')[current_step_index].get('tool_args', {})
        tool_response = f"Error: Tool '{tool_name}' not found."

        scraped_data_accumulator = state.get('scraped_data', [])
        result = await self._executor._execute_tool(tool_name, tool_args, state)
        if result:
            tool_response = result.tool_response
            scraped_data_accumulator = result.scraped_data_accumulator

        # screenshot at each step
        if state.get('screenshot_each_step'):
            path = os.path.join(os.path.dirname(__file__), '../../../screenshots/')
            if not os.path.exists(path):
                os.makedirs(path)
            await self._executor._page.screenshot(path=os.path.join(path, f'screenshot_replay_session_{self._executor._session}_{self._executor._iterations}.png'))

        return { 
            'scraped_data': scraped_data_accumulator,
            'step_results': state.get('step_results', []) + [tool_response],
            'current_step_index': state.get('current_step_index') + 1
        }

    async def final_output_node(self, state: MemoryState) -> MemoryState:
        if state.get('scraped_data'):
            if isinstance(state.get('scraped_data')[0], dict):
                return { 'output': state.get('scraped_data') }
            else:
                return { 'output': '\n'.join(state.get('scraped_data') if state.get('scraped_data') else []) }
        return { 'output': state.get('step_results')[-1] }

    async def _router(self, state: MemoryState) -> str:
        if state.get('wait_between_actions') > 0:
            if state.get('verbose'):
                print(Fore.YELLOW + Style.BRIGHT + f'Waiting for {state.get('wait_between_actions')} seconds' + Style.RESET_ALL)
            await asyncio.sleep(state.get('wait_between_actions'))

        self._executor._iterations += 1

        if state.get('current_step_index') < len(state.get('steps')):
            return 'step_execution_node'
        else:
            return 'final_output_node'

    def create_graph(self) -> CompiledStateGraph:
        graph = StateGraph(MemoryState)
        graph.add_node('step_execution_node', self.step_execution_node)
        graph.add_node('final_output_node', self.final_output_node)
        graph.add_conditional_edges(
            'step_execution_node',
            self._router,
            {
                'step_execution_node': 'step_execution_node',
                'final_output_node': 'final_output_node'
            }
        )
        graph.add_edge('final_output_node', END)
        graph.set_entry_point('step_execution_node')

        return graph.compile()