from .base_tool import BaseTool
from playwright.async_api import Page
from typing import Dict, Union
from pydantic import BaseModel
from markdownify import markdownify as md

class GetMarkdownTool(BaseTool):
    name: str = "get_markdown"
    description: str = "Returns the Markdown content of the page."
    args_schema: BaseModel = None

    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self) -> Union[str, Dict]:
        try:
            html = await self.page.locator("body").inner_html()
            markdown = md(html, strip = ["script", "style", "noscript", "iframe", 
            "object", "embed", "link", "meta", "svg", "canvas"])
            return markdown
        except Exception as e:
            return {"error": f"Failed to get Markdown: {e}"}
