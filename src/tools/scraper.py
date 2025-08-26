from .base_tool import BaseTool
from ..dom import DOM
from ..models import BaseModel
from ..message import SystemMessage, UserMessage
from ..agent.utils import build_scraper_prompt
from ..agent.utils import extract_json
from playwright.async_api import Page
from markdownify import markdownify as md
from pydantic import BaseModel, Field
from typing import Dict, Union, Any

class ScraperArgs(BaseModel):
    user_input: str = Field(..., description="""User Query""")

class ScraperTool(BaseTool):
    name: str = "scraper"
    description: str = "Scrapes the whole page based on the user given query content. Note that it will scrape the whole body of the html. It converts the body into markdown format and sends it to the LLM to scrape based on the user query."
    args_schema: BaseModel = ScraperArgs

    def __init__(
            self, 
            page: Page, 
            dom: DOM, 
            model: BaseModel, 
            scraper_response_json_format: Dict[str, Any]
        ):
        super().__init__(
            page = page, 
            dom = dom, 
            model = model,  
            scraper_response_json_format = scraper_response_json_format
        )
        self.last_seen_markdown = ""

    async def run(self, args: ScraperArgs) -> Union[str, Dict]:
        try:
            html = await self.page.locator("body").inner_html()
            current_markdown = md(html, strip = ["script", "style", "noscript", "iframe", "object", "embed", "link", "meta", "svg", "canvas"])
            
            markdown_to_process = ""
            
            # Check if we have previous content and if the new content is an extension of it
            if self.last_seen_markdown and current_markdown.startswith(self.last_seen_markdown):
                # Slice the string to get only the new part that was added
                markdown_to_process = current_markdown[len(self.last_seen_markdown):]
                print("New content detected. Processing only the delta to save context.")
            elif self.last_seen_markdown == current_markdown:
                # The content is an exact duplicate
                return "No new content found; page is identical to the last scrape."
            else:
                # This is the first scrape or a completely different page
                markdown_to_process = current_markdown

            # Avoid sending empty or whitespace-only content to the LLM
            if not markdown_to_process.strip():
                return "No new textual content found to scrape."
            
            # Update the state for the *next* time the tool is called
            self.last_seen_markdown = current_markdown

            system_prompt_template = build_scraper_prompt(
                scraper_output_json_schema = self.scraper_response_json_format
            )

            messages = [
                SystemMessage(content = system_prompt_template).to_dict(),
                UserMessage(content = f'User Query: {args.user_input}').to_dict(),
                UserMessage(content = f'HTML Content in Markdown Format\n: {markdown_to_process}').to_dict(),
            ]

            self.model.messages = messages
            response = await self.model.generate()
            response = response.choices[0].message.content
            # response = response['choices'][0]['message']['content']
            final_response = extract_json(response)
            if not final_response or 'response' not in final_response:
                raise ValueError("LLM failed to return a valid JSON object with a 'response' key.")

            # --- CRITICAL CHANGE ---
            # Only update the 'last_seen_markdown' state AFTER the LLM call and parsing are successful.
            self.last_seen_markdown = current_markdown
            print("Successfully processed new content and updated tool memory.")
            
            return final_response.get('response')
            # return final_response['response']   
        except Exception as e:
            return str(e)