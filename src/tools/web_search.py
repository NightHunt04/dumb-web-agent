from .base_tool import BaseTool
from pydantic import BaseModel, Field
from ddgs import DDGS

class WebSearchArgs(BaseModel):
    query: str = Field(..., description = "The query to search for on the internet")
    max_results: int = Field(10, description = "The maximum number of results to return")

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = """Searches the internet for information related to the user's query such as finding out any links which are relevant to the user's query. 
    Note that this is only to find out the links and not to scrape the content of the links. 
    Can be useful when the user doesn't specify a website to scrape."""
    args_schema: BaseModel = WebSearchArgs

    def __init__(self):
        super().__init__()

    async def run(self, args: WebSearchArgs) -> str:
        results = DDGS().text(
            query = args.query, 
            max_results = args.max_results,
            safesearch = 'off'
        )
        return str(results)
