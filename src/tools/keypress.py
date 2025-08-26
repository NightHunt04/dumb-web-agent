from .base_tool import BaseTool
from playwright.async_api import Page
from typing import Union, Dict
from pydantic import BaseModel, Field

class PressKeyArgs(BaseModel):
    """Arguments for the PressKeyTool."""
    key: str = Field(..., 
                   description="The key to press. For example 'Enter', 'Tab', 'ArrowDown', 'a', 'b', 'Control+A'.")

class PressKeyTool(BaseTool):
    name: str = "press_key"
    description: str = "Presses a specific key on the keyboard. Useful for submitting forms with 'Enter', navigating menus, or triggering keyboard shortcuts."
    args_schema: BaseModel = PressKeyArgs
    
    def __init__(self, page: Page):
        super().__init__(page)

    async def run(self, args: PressKeyArgs) -> Union[str, Dict]:
        """
        This tool presses a specified key on the keyboard.
        """
        try:
            await self.page.keyboard.press(args.key)
            await self.page.wait_for_load_state("networkidle")
            return f"Successfully pressed the '{args.key}' key."
        except Exception as e:
            return {"error": f"Failed to press key '{args.key}': {e}"}