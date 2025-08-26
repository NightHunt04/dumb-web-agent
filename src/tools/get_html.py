from .base_tool import BaseTool
from playwright.async_api import Page
from typing import Dict, Union
from pydantic import BaseModel
from bs4 import BeautifulSoup, Comment

class GetHtmlTool(BaseTool):
    name: str = "get_html"
    description: str = "Returns a cleaned and simplified version of the page's HTML content, optimized for an LLM."
    args_schema: BaseModel = None 

    def __init__(self, page: Page):
        super().__init__(page=page)

    async def run(self) -> Union[str, Dict]:
        try:
            raw_html = await self.page.locator("body").inner_html()
            soup = BeautifulSoup(raw_html, 'html.parser')

            unwanted_tags = ['script', 'style', 'noscript', 'iframe', 'meta', 'svg', 'embed', 'canvas', 'link']
            for tag in soup.find_all(unwanted_tags):
                tag.decompose()
            
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            attributes_to_keep = ['href', 'src', 'alt', 'id', 'title', 'aria-label', 'name', 'for', 'type', 'placeholder', 'value']
            
            for tag in soup.find_all(True):
                current_attrs = list(tag.attrs.items())
                for key, value in current_attrs:
                    if key not in attributes_to_keep:
                        del tag[key]

            self_closing_tags = ['img', 'br', 'hr', 'input']
            for tag in soup.find_all(True):
                if tag.name not in self_closing_tags and not tag.contents and not tag.get_text(strip=True):
                    tag.decompose()
            
            cleaned_html = str(soup.prettify())
            
            return cleaned_html
        except Exception as e:
            return {"error": f"Failed to get and clean HTML: {e}"}