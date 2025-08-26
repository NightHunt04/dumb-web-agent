from ..dom import DOM
from ..browser import Browser
from ..tools.register import get_tool_classes
from .state import AgentState, MemoryState
from .utils import extract_json, read_markdown_file
from playwright.async_api import Page
from typing import Optional, Dict, Any, List
from pydantic import Field, ValidationError, BaseModel
from colorama import Fore, Style
import inspect
import asyncio
import json
import os

# These tools wont be available for the agent
# The name of the tools must be the same, i.e. the name of the file of the tool
IGNORE_TOOLS = ['scroll_and_scrape', 'get_html', 'get_markdown']

class ToolExecutionResult(BaseModel):
    tool_response: List | Dict | str | None
    scraped_data_accumulator: List[Dict | str | None]

class AgentExecutor:
    """
    Agent Executor
    It contains the instances which are to be used when running the agent.
    Tools are being dynamically initialized over here, which will be called based on the graph.

    Attributes:
        model (BaseModel): The model instance to use for the agent
        browser (Browser): The browser instance to use for the agent
        page (Page): The page instance to use for the agent
        iterations (int): The number of iterations the agent has run
        messages (List[BaseMessage]): The messages to be sent to the model
        dom (DOM): The DOM instance to use for the agent
        scraper_response_json_format (Optional[Dict[str, Any]]): The JSON format to use for the scraper response
        session (str): The session ID for the agent
    """

    def __init__(
            self, 
            model: BaseModel = Field(..., description="Model to use for agent"), 
            browser: Browser = Field(..., description="Browser to use for agent"), 
            scraper_response_json_format: Optional[Dict[str, Any]] = None,
            session: str = ''
        ) -> None:
        self._model = model
        self._browser = browser
        self._page = None
        self._iterations = 0
        self._messages = []
        self.dom = None
        self._scraper_response_json_format = scraper_response_json_format
        self._session = session
        self._tools = []
        self._system_prompt = ''
        self._output_prompt = ''

    def _finish_initialization(self, page: Page) -> None:
        """
        Finish the initialization of the agent executor.
        """

        self._page = page
        self.dom = DOM(page = self._page)

        available_dependencies = {
            "page": self._page,
            "dom": self.dom,
            "model": self._model,
            "scraper_response_json_format": self._scraper_response_json_format
        }

        self.tools = []
        markdown_list = []
        for tool_class in get_tool_classes():
            sig = inspect.signature(tool_class.__init__)
            tool_kwargs = {}

            if tool_class.name in IGNORE_TOOLS:
                continue

            markdown_list.append(f"- {tool_class.name}: {tool_class.description}")
            args_schema = tool_class.args_schema

            if args_schema and args_schema.model_fields:
                for field_name, field_info in args_schema.model_fields.items():
                    if field_info.is_required():
                        req_or_default = "required"
                    else:   
                        req_or_default = f"default = {field_info.default}"
                    
                    arg_type = field_info.annotation.__name__
                    arg_desc = field_info.description or ""
                    
                    markdown_list.append(f"    - Args: `{field_name}` ({arg_type}, {req_or_default}) - {arg_desc}")

            for param in sig.parameters.values():
                if param.name in available_dependencies:
                    tool_kwargs[param.name] = available_dependencies[param.name]
            
            self.tools.append(tool_class(**tool_kwargs))

        tools_markdown = "\n".join(markdown_list)
        system_prompt_template = read_markdown_file(os.path.join(os.path.dirname(__file__), '../prompts', 'system.md'))
        final_system_prompt = system_prompt_template.replace("TOOL_REGISTRY", tools_markdown)
        output_prompt_template = read_markdown_file(os.path.join(os.path.dirname(__file__), '../prompts', 'output.md'))

        # initialize prompts
        self._system_prompt = final_system_prompt
        self._output_prompt = output_prompt_template

        print(Fore.LIGHTWHITE_EX + "Tools:")
        for tool in self.tools:
            print(f"- {tool.name}")
        print(Style.RESET_ALL + Fore.LIGHTRED_EX + 'Ignored tools:')
        for tool in IGNORE_TOOLS:
            print(f"- {tool}")
        print(Style.RESET_ALL)

    async def close(self):
        """Public method to close the browser manually."""
        if self._browser.page and not self._browser.page.is_closed():
            await self._browser.close_browser()
        else:
            print("Browser is already closed.")

    async def _execute_tool(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        state: AgentState | MemoryState
    ) -> ToolExecutionResult | None:
        """
        This method is being used both in the agent graph and memory graph.
        It executes the tool based on the tool name and tool args.

        Args:
            tool_name (str): The name of the tool to execute
            tool_args (Dict[str, Any]): The arguments to pass to the tool
            state (AgentState | MemoryState): The state of the agent

        Returns:
            ToolExecutionResult | None: The result of the tool execution
        """

        if state.get('verbose'):
            print(Fore.YELLOW + Style.BRIGHT + f'Executing tool: {tool_name}' + Style.RESET_ALL)
            print('Tool args:')
            print('\n'.join(f"{key}: {item}" for key, item in tool_args.items()))
            print(Style.RESET_ALL)

        found_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                found_tool = tool
                break

        if found_tool:
            try:
                args_model = found_tool.args_schema(**tool_args)
                tool_response = await found_tool.run(args=args_model)

                if state.get('verbose'):
                    print(Fore.GREEN + Style.BRIGHT + f'Tool response: {str(tool_response)}' + Style.RESET_ALL, '\n')
                    print(Fore.LIGHTYELLOW_EX + 'Waiting for networkidle...' + Style.RESET_ALL)
                
                await self._page.wait_for_load_state("networkidle", timeout=10000)

                if state.get('wait_between_actions'):
                    if state.get('verbose'):
                        print(Fore.LIGHTYELLOW_EX + 'Waiting for ' + str(state.get('wait_between_actions')) + ' seconds...' + Style.RESET_ALL)
                    await asyncio.sleep(state.get('wait_between_actions'))

            except ValidationError as e:
                tool_response = f"Error: Tool argument validation error: {e}"
            except Exception as e:
                tool_response = f"Error: Error executing tool '{tool_name}': {e}"
        
            scraped_data_accumulator = state.get('scraped_data', [])
            if tool_name in ["scraper", "scroll_and_scrape"]:
                try:
                    if self._scraper_response_json_format or isinstance(tool_response, (dict, list)):
                        if isinstance(tool_response, (dict, list)):
                            newly_scraped_data = tool_response
                        elif isinstance(tool_response, str):
                            newly_scraped_data = extract_json(tool_response)
                        
                        if not isinstance(newly_scraped_data, list):
                            newly_scraped_data = [newly_scraped_data]
                        
                        existing_items_set = {json.dumps(item, sort_keys=True) for item in scraped_data_accumulator if isinstance(item, dict)}
                        unique_new_items = []
                        for item in newly_scraped_data:
                            if isinstance(item, dict):
                                item_fingerprint = json.dumps(item, sort_keys=True)
                                if item_fingerprint not in existing_items_set:
                                    unique_new_items.append(item)
                                    existing_items_set.add(item_fingerprint)
                        if unique_new_items:
                            scraped_data_accumulator.extend(unique_new_items)
                            if state.get('verbose'):
                                print(Fore.WHITE + Style.BRIGHT + f"Implicitly saved {len(unique_new_items)} new JSON items. Total items: {len(scraped_data_accumulator)}.\n" + Style.RESET_ALL)
                    else:
                        if isinstance(tool_response, str) and tool_response not in scraped_data_accumulator and isinstance(tool_response, str):
                            if state.get('verbose'):
                                print(Fore.WHITE + Style.BRIGHT + f"Implicitly saved new string summary. Total items: {len(scraped_data_accumulator)}.\n" + Style.RESET_ALL)
                            scraped_data_accumulator.append(tool_response)
                except Exception as e:
                    print(Fore.RED + Style.BRIGHT + '❗' + f"Could not automatically save scraper output: {e}" + Style.RESET_ALL)

            return ToolExecutionResult(
                tool_response=tool_response,
                scraped_data_accumulator=scraped_data_accumulator
            )
        return None