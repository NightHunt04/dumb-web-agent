from .base_tool import BaseTool
from pydantic import BaseModel, Field
from playwright.async_api import Page
import asyncio

class WaitArgs(BaseModel):
    timeout: int = Field(5, description="Timeout in seconds (default: 5)")
    # wait_for_networkidle: bool = Field(False, description="Wait for network idle")

class WaitTool(BaseTool):
    name: str = "wait"
    description: str = "Waits for a specified amount of time in seconds or wait for network idle"
    args_schema: BaseModel = WaitArgs

    def __init__(self, page: Page):
        super().__init__(page = page)

    async def run(self, args: WaitArgs) -> str:
        try:
            # if args.wait_for_networkidle:
            #     print('waiting for networkidle')
            #     await self.page.wait_for_load_state("networkidle")
            # else:
            await self.page.wait_for_timeout(args.timeout * 1000)
            # await asyncio.sleep(args.timeout)
            return f"Waited for quite some time."
        except Exception as e:
            return f"Error: {e}"
