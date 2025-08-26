from .base_tool import BaseTool
from ..dom import DOM
from playwright.async_api import Page
from typing import Dict, Union
from pydantic import BaseModel, Field

class InjectCodeArgs(BaseModel):
    """Arguments for the InjectCode tool."""
    code: str = Field(..., description="The code to inject into the page.")

class InjectCodeTool(BaseTool):
    name: str = "inject_code"
    description: str = "Injects code into the page."
    args_schema: BaseModel = InjectCodeArgs
    
    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: InjectCodeArgs) -> Union[str, Dict]:
        try:
            js_response = await self.page.evaluate(args.code)
            return f"Code injected and gave this response\n: {js_response}"
        except Exception as e:
            return {"error": str(e)}