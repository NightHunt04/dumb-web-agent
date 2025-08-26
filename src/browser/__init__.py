from .config import BROWSER_ARGS, IGNORE_DEFAULT_ARGS, SECURITY_ARGS
from playwright.async_api import (
    Page, 
    Playwright, 
    Browser, 
    async_playwright, 
    BrowserContext
)
from playwright_stealth import Stealth
from fake_useragent import UserAgent
from typing import Literal

class Browser:
    """
    Browser class for managing browser instances.

    Attributes:
        headless (bool): Whether to run the browser in headless mode
        browser_type (Literal['chrome', 'edge', 'firefox']): The type of browser to use
        user_agent (str): The user agent to use for the browser
        random_user_agent (bool): Whether to use a random user agent
        playwright (Playwright): The Playwright instance
        browser_instance (Browser): The browser instance
        browser_context (BrowserContext): The browser context
        page (Page): The page instance
    """

    def __init__(
        self, 
        headless: bool = False,
        browser_type: Literal['chrome', 'edge', 'firefox'] = 'chrome',
        user_agent: str = None,
        random_user_agent: bool = False,
        executable_path: str = None,
        ws_endpoint: str = None
    ) -> None:
        self.headless = headless
        self.browser_type = browser_type
        self.user_agent = user_agent
        self.random_user_agent = random_user_agent
        self.playwright: Playwright = None
        self.browser_instance: Browser = None
        self.browser_context: BrowserContext = None
        self.page: Page = None
        self.executable_path = executable_path
        self.ws_endpoint = ws_endpoint

        if self.random_user_agent:
            if browser_type == 'chrome':
                self.user_agent = UserAgent().chrome
            elif browser_type == 'firefox':
                self.user_agent = UserAgent().firefox
            elif browser_type == 'edge':
                self.user_agent = UserAgent().edge

    async def __aenter__(self) -> Browser:
        """
        Initializes the browser when using the `async with` statement.
        """
        return await self.init_browser()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the browser when the context manager is to be exited.
        """
        await self.close_browser()
    
    async def init_browser(self) -> Browser:
        self.playwright = await async_playwright().start()

        if self.ws_endpoint:
            browser_instance = await self.playwright.chromium.connect(self.ws_endpoint, timeout=30000)

        else:
            if self.browser_type == 'chrome':
                browser_instance = await self.playwright.chromium.launch(
                    headless = self.headless, 
                    args = SECURITY_ARGS + BROWSER_ARGS,
                    ignore_default_args = IGNORE_DEFAULT_ARGS,
                )
            elif self.browser_type == 'edge':
                browser_instance = await self.playwright.chromium.launch(
                    headless = self.headless, 
                    args = BROWSER_ARGS,
                    ignore_default_args = IGNORE_DEFAULT_ARGS,
                )
            elif self.browser_type == 'firefox':
                browser_instance = await self.playwright.firefox.launch(
                    headless = self.headless, 
                    args = BROWSER_ARGS,
                    ignore_default_args = IGNORE_DEFAULT_ARGS,
                )
    
        self.browser_context = await browser_instance.new_context(
            user_agent = self.user_agent
        )

        stealth = Stealth()
        await stealth.apply_stealth_async(self.browser_context)
        self.page = await self.browser_context.new_page()
        await self.page.goto('about:blank') # default page to be opened
        await self.page.wait_for_load_state('domcontentloaded')

        return self

    async def close_browser(self) -> None:
        """
        Closes the browser instance and releases resources.
        """

        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
                self.page = None

            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None

            if self.browser_instance:
                await self.browser_instance.close_browser()
                self.browser_instance = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Error closing browser: {e}")