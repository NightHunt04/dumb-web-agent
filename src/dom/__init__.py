from playwright.async_api import Page
from .state import DOMState
from typing import List
import os

class DOM:
    """
    DOM class for managing DOM instances.

    Attributes:
        page (Page): The page instance to use for the DOM
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    async def get_state(self) -> DOMState | Exception:
        try:
            script_path = os.path.join(os.path.dirname(__file__), 'script.js')
            with open(script_path) as f:
                script = f.read()
            
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            all_elements = await self.page.evaluate(f"""{script}\ngetElements()""") 
            
            return DOMState(
                interactive_elements = all_elements.get('interactiveElements', []),
                informative_elements = all_elements.get('informativeElements', []),
                scrollable_elements = all_elements.get('scrollableElements', [])
            )
        except Exception as e:
            return e

    async def get_interactive_elements(self) -> List[dict]:
        """Returns the raw interactive elements as a list of dictionaries."""
        state = await self.get_state()
        return state.get('interactive_elements', [])

    async def get_informative_elements(self) -> List[dict]:
        """Returns the raw informative elements as a list of dictionaries."""
        state = await self.get_state()
        return state.get('informative_elements', [])

    async def get_scrollable_elements(self) -> List[dict]:
        """Returns the raw scrollable elements as a list of dictionaries."""
        state = await self.get_state()
        return state.get('scrollable_elements', [])

    async def get_formatted_interactive_elements(self) -> str:
        raw_elements = await self.get_state()
        return self.format_elements_for_prompt(raw_elements.get('interactive_elements', []))

    async def get_formatted_informative_elements(self) -> str:
        raw_elements = await self.get_state()
        return self.format_elements_for_prompt(raw_elements.get('informative_elements', []))

    async def get_formatted_scrollable_elements(self) -> str:
        raw_elements = await self.get_state()
        return self.format_elements_for_prompt(raw_elements.get('scrollable_elements', []))

    def format_elements_for_prompt(self, elements: List[dict]) -> str:
        """Helper method to convert a list of element dicts into a string."""
        return '\n'.join([self.to_prompt_string(element, i) for i, element in enumerate(elements)])

    def to_prompt_string(self, element: dict, index: int) -> str:
        if 'content' in element:
            return (f"{index} Tag:{element.get('tag')} Role:{element.get('role')} "
                    f"Content:{element.get('content')} Center:{element.get('center')} Xpath:{element.get('xpath')}")
        elif 'box' in element:
            return (f"{index} Tag:{element.get('tag')} Role:{element.get('role')} "
                    f"Name:{element.get('name')} Attributes:{element.get('attributes')} Box:{element.get('box')} Center:{element.get('center')} Xpath:{element.get('xpath')}")
        else:
            return (f"{index} Tag:{element.get('tag')} Role:{element.get('role')} "
                    f"Name:{element.get('name')} Attributes:{element.get('attributes')} Xpath:{element.get('xpath')}")
