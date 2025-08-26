from .base_tool import BaseTool
from playwright.async_api import Page
from typing import Union, Dict
from pydantic import BaseModel, Field
import random

class ClickElementArgs(BaseModel):
    """Arguments for the ClickElement tool."""
    xpath: str = Field(..., description="XPath of the element to click.")
    x: float = Field(..., description="X coordinate to click at.")
    y: float = Field(..., description="Y coordinate to click at.")

class ClickElementTool(BaseTool):
    name: str = "click_element"
    description: str = "Clicks an element on the page using its coordinates (x and y). Must provide the X and Y coordinates along with the Xpath."
    args_schema: BaseModel = ClickElementArgs
    
    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: ClickElementArgs) -> Union[str, Dict]:
        """
        This tool clicks on element using its coordinates or xpath.
        """
        try:
            if args.xpath:
                # await self.page.locator(f'xpath={args.xpath}').scroll_into_view_if_needed()
                await self.page.locator(f'xpath={args.xpath}').click()
                return f"Successfully clicked at element with xpath: {args.xpath}"
            if args.x is not None and args.y is not None:
                jitter_x = random.uniform(-2, 2)
                jitter_y = random.uniform(-2, 2)
                await self.page.mouse.click(args.x + jitter_x, args.y + jitter_y)
                return f"Successfully clicked at coordinates (x: {args.x}, y: {args.y}) with human-like jitter."
        except Exception as e:
            return {"error": f"Failed to click element: {e}"}