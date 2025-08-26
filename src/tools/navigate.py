from .base_tool import BaseTool
from ..dom import DOM
from typing import Dict, Union
from pydantic import BaseModel, Field
from playwright.async_api import Page

class NavigateArgs(BaseModel):
    """Arguments for the NavigateTool."""
    url: str = Field(..., description="The URL to navigate to.")
    timeout: int = Field(30000, description="Timeout for the navigation in milliseconds. Defaults to 30000 (30 seconds).")

class NavigateTool(BaseTool):
    name: str = "navigate"
    description: str = "Navigates to a specific URL and waits for the page to load."
    args_schema: BaseModel = NavigateArgs

    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: NavigateArgs) -> Union[str, Dict]:
        try:
            await self.page.goto(args.url, timeout=args.timeout)
            await self.page.wait_for_load_state("networkidle")
            return f"Successfully navigated to {args.url}."
        except Exception as e:
            return {"error": f"Failed to navigate to {args.url}: {e}"}