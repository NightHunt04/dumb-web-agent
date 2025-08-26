from .base_tool import BaseTool
from typing import Dict, Union
from pydantic import BaseModel, Field
from playwright.async_api import Page
import random
import asyncio

class ClickAndTypeArgs(BaseModel):
    """Arguments for the ClickAndTypeTool."""
    xpath: str = Field(..., description="XPath of the element to click.")
    text: str = Field(..., description="The text to type into the element.")
    x: float = Field(..., description="The x coordinate to click before typing.")
    y: float = Field(..., description="The y coordinate to click before typing.")

class ClickAndTypeTool(BaseTool):
    name: str = "click_and_type_text"
    description: str = "Clicks on an element using its XPath or coordinates and types text into it."
    args_schema: BaseModel = ClickAndTypeArgs

    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: ClickAndTypeArgs) -> Union[str, Dict]:
        try:
            if args.xpath:
                await self.page.locator(f'xpath={args.xpath}').clear()
                await self.page.locator(f'xpath={args.xpath}').press_sequentially(args.text, delay=random.uniform(50, 150))
                return f"Successfully clicked and typed text into element with xpath using emunium: {args.xpath}"
            else:
                await self.page.locator(f'xpath={args.xpath}').clear()
                await self.page.mouse.click(args.x, args.y)
                await asyncio.sleep(0.5)
                await self.page.keyboard.type(args.text, delay=random.uniform(50, 150))
                return f"Successfully clicked and typed text into element at coordinates (x: {args.x}, y: {args.y}) with human-like jitter."
        except Exception as e:
            return {"error": f"Failed to click and type text into element: {e}"}