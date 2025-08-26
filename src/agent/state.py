from ..dom.state import DOMState
from typing import TypedDict, Optional

class Response(TypedDict):
    tool_name: str
    tool_args: dict
    thought: str
    observation: str

class Action(TypedDict):
    thought: str
    observation: str | None
    tool_call: str | None
    tool_args: dict | None
    tool_response: str | None

class AgentState(TypedDict):
    input: str
    output: str
    previous_actions: list[Action]
    page_state: DOMState | None
    response: Optional[Response]
    scraped_data: list
    verbose: bool
    wait_between_actions: int
    memorize: bool
    memorized_steps: list[Action]
    screenshot_each_step: bool

class MemoryState(TypedDict):
    input: str
    output: str
    steps: list[Action]
    step_results: list[str]
    verbose: bool
    current_step_index: int
    scraped_data: list
    wait_between_actions: int
    screenshot_each_step: bool