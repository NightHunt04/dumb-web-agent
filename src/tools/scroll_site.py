from .base_tool import BaseTool
from typing import Dict, Union, Optional
from pydantic import BaseModel, Field
from playwright.async_api import Page
import asyncio

class ScrollSiteArgs(BaseModel):
    """Arguments for the ScrollSiteTool."""
    distance: float = Field(400, description = "Distance to scroll in pixels. Defaults to 400.")
    direction: str = Field('down', description = "Direction of the scroll. Can be 'up' or 'down'. Defaults to 'down'.")
    timeout: Optional[int] = Field(None, description = "Timeout for the scroll in milliseconds. Defaults to 30000 (30 seconds).")

class ScrollSiteTool(BaseTool):
    name: str = "scroll_site"
    description: str = "Scrolls the page to the bottom and waits for the page to load."
    args_schema: BaseModel = ScrollSiteArgs

    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: ScrollSiteArgs) -> Union[str, Dict]:
        try:
            if args.direction.lower().strip() == 'down':
                await self.page.evaluate(f"window.scrollBy(0, {args.distance})")
                result_message = f"Page scrolled down by {args.distance} pixels."
            elif args.direction.lower().strip() == 'up':
                await self.page.evaluate(f"window.scrollBy(0, -{args.distance})")
                result_message = f"Page scrolled up by {args.distance} pixels."
            else:
                return {"error": "Invalid scroll direction. Use 'up' or 'down'."}

            await self.page.wait_for_load_state("networkidle")
            if args.timeout:
                await asyncio.sleep(args.timeout / 1000)
            return result_message
        except Exception as e:
            return {"error": str(e)}