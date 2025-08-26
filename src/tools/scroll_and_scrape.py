from .base_tool import BaseTool
from ..dom import DOM
from ..agent.state import AgentState
from ..models import BaseModel
from ..agent.utils import build_scraper_prompt, read_markdown_file, extract_json
from ..message import SystemMessage, UserMessage
from playwright.async_api import Page
from markdownify import markdownify as md
from pydantic import BaseModel, Field
from typing import Dict, Union, Optional, Any
import os
import re

class ScrollAndScrapeArgs(BaseModel):
    """Arguments for the ScrollAndScrapeTool."""
    user_query: str = Field(..., description="The user's original query defining the content to be scraped after scrolling is complete.")
    max_attempts: int = Field(20, description="The maximum number of times to try loading new content by scrolling or clicking a button. Default is 20.")
    # max_scrolls: int = Field(35, description="The maximum number of times to scroll down. Default is 35 increase more if infinite scroll page.")
    scroll_step: int = Field(1000, description="The distance in pixels for each scroll attempt. Default is 1000.")
    wait_timeout: int = Field(15000, description="The maximum time in milliseconds to wait for network requests to settle after a scroll. Default is 15000 (15 seconds).")

class ScrollAndScrapeTool(BaseTool):
    name: str = "scroll_and_scrape"
    description: str = "A powerful, all-in-one tool for extracting all items from a list. It intelligently handles 'Load More' buttons, pagination, and infinite scroll."
    # description: str = "A specialized tool for infinite scroll pages. It repeatedly scrolls down by a specified distance and waits for network activity to stop, ensuring all dynamic content is loaded. It then performs a final scrape based on the user's query. This tool does NOT handle 'Load More' buttons."
    args_schema: BaseModel = ScrollAndScrapeArgs

    def __init__(
            self, 
            page: Page, 
            dom: DOM, 
            model: BaseModel, 
            scraper_response_json_format: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            page=page, 
            dom=dom, 
            model=model, 
            scraper_response_json_format=scraper_response_json_format
        )

    def _is_load_more_element(self, element: Dict[str, Any]) -> bool:
        """
        Determine if an interactive element is a 'load more' or pagination button.
        
        Args:
            element (Dict[str, Any]): The interactive element to check.
        
        Returns:
            bool: True if the element is likely a 'load more' button, False otherwise.
        """
        allowed_tags = ['button', 'a', 'div', 'span']
        
        if element.get('tag', '').lower() not in allowed_tags:
            return False
        
        name = element.get('name', '').lower()
        load_more_patterns = [
            r'load more', 
            r'show more', 
            r'view more', 
            r'^more$', 
            r'^next$'
        ]
        
        for pattern in load_more_patterns:
            if re.search(pattern, name):
                return True
        
        attributes = element.get('attributes', {})
        for key, value in attributes.items():
            if any(indicator in str(key).lower() or indicator in str(value).lower() 
                   for indicator in ['loadmore', 'load-more', 'next', 'pagination']):
                return True
        
        return False

    async def run(self, args: ScrollAndScrapeArgs) -> Union[str, Dict]:
        processed_xpaths = set()
        consecutive_failures = 0
        max_consecutive_failures = 7

        for i in range(args.max_attempts):
            print(f"--- Content Loading Attempt {i + 1}/{args.max_attempts} ---")

            # First, check if the PREVIOUS action loaded new content
            last_known_item_count = len(processed_xpaths)
            current_elements = await self.dom.get_informative_elements()
            for el in current_elements:
                processed_xpaths.add(el.get('xpath'))

            if i > 0 and len(processed_xpaths) == last_known_item_count:
                consecutive_failures += 1
                print(f"No new content loaded. Consecutive failures: {consecutive_failures}/{max_consecutive_failures}.")
                if consecutive_failures >= max_consecutive_failures:
                    print("Max consecutive failures reached. Concluding.")
                    break
            else:
                consecutive_failures = 0

            # --- START: REFINED ACTION HIERARCHY ---
            action_taken = False
            
            # Priority 1: Find and click a "Load More" button from the visible elements
            interactive_elements = await self.dom.get_interactive_elements()
            visible_load_buttons = [el for el in interactive_elements if self._is_load_more_element(el)]
            
            if visible_load_buttons:
                # Try to click the first identified button
                button_to_click = visible_load_buttons[0]
                xpath = button_to_click.get('xpath')
                try:
                    # Use the modern page.locator() method for more robust interaction
                    button_locator = self.page.locator(f"xpath={xpath}")
                    await button_locator.click(timeout=2000)
                    await self.page.wait_for_load_state('networkidle', timeout=5000)
                    print(f"Successfully clicked button: '{button_to_click.get('name')}'")
                    action_taken = True
                except Exception as e:
                    print(f"Found button '{button_to_click.get('name')}' but it was not clickable: {e}")
            
            # Priority 2: If no button was clicked, fall back to scrolling
            if not action_taken:
                print("No interactive button found. Scrolling down.")
                await self.page.mouse.wheel(0, args.scroll_step)
                await self.page.wait_for_timeout(2000)
            # --- END: REFINED ACTION HIERARCHY ---

            # Wait for content to load after either action
            try:
                await self.page.wait_for_load_state('networkidle', timeout=5000)
            except Exception:
                await self.page.wait_for_timeout(3000)
        
        # --- Final Scrape Step ---
        await self.page.wait_for_timeout(args.wait_timeout)
        print("\nContent loading complete. Performing final scrape...")
        html = await self.page.locator("body").inner_html()
        markdown = md(html, strip=["script", "style", "link", "meta"])
        
        system_prompt_template = build_scraper_prompt(self.scraper_response_json_format)
        messages = [
            SystemMessage(content=system_prompt_template).to_dict(),
            UserMessage(content=f'User Query: {args.user_query}').to_dict(),
            UserMessage(content=f'HTML Content in Markdown Format:\n: {markdown}').to_dict(),
        ]
        self.model.messages = messages
        response = await self.model.generate()
        response_content = response['choices'][0]['message']['content']
        final_response = extract_json(response_content)
        return final_response.get('response') if final_response else "Failed to extract JSON from the final response."






    # async def run(self, args: ScrollAndScrapeArgs) -> Union[str, Dict]:
    #     """
    #     Implements the loop of scrolling down, waiting for the network to be idle,
    #     and then scraping the fully loaded content.
    #     """
    #     load_more_elements = set()
    #     consecutive_failuers = 0
    #     max_consecutive_failures = 4
        
    #     try:
    #         for i in range(args.max_scrolls):
    #             print(f"Scroll attempt {i + 1}/{args.max_scrolls}...")

    #             current_interactive_elements = await self.dom.get_interactive_elements()
    #             current_load_more_elements = {
    #                 el for el in current_interactive_elements 
    #                 if self._is_load_more_element(el)
    #             }

    #             # If new load more elements are found, add them to the set
    #             new_load_more_elements = current_load_more_elements - load_more_elements
    #             load_more_elements.update(new_load_more_elements)

    #             # If load more elements are found and haven't been processed, try clicking
    #             if new_load_more_elements:
    #                 for element in new_load_more_elements:
    #                     try:
    #                         # Attempt to click the load more button
    #                         xpath = element.get('xpath')
    #                         load_more_button = await self.page.xpath(xpath)
    #                         if load_more_button:
    #                             await load_more_button[0].click()
    #                             await self.page.wait_for_timeout(2000)
    #                             print(f"Clicked load more button: {element.get('name', 'Unknown')}")
    #                             break
    #                     except Exception as click_error:
    #                         print(f"Could not click load more button: {click_error}")

    #             last_known_item_count = len(processed_xpaths)

    #             current_informative_elements = await self.dom.get_informative_elements()
    #             for el in current_informative_elements:
    #                 processed_xpaths.add(el.get('xpath'))

    #             current_scroll_step = args.scroll_step 
                
    #             if len(processed_xpaths) == last_known_item_count and i > 0:
    #                 consecutive_failuers += 1
    #                 print(f"No new content loaded from the previous scroll. Consecutive failures: {consecutive_failuers}")

    #                 if consecutive_failuers >= max_consecutive_failures:
    #                     print("Maximum consecutive failures reached. Concluding scrolling.")
    #                     break

    #                 print("Escalating scroll distance to try and force load")
    #                 current_scroll_step = args.scroll_step * 2
    #             else:
    #                 consecutive_failuers = 0
                
    #             await self.page.mouse.wheel(0, current_scroll_step)
    #             await self.page.wait_for_timeout(1000)
    #             print(f"Scrolled down by {current_scroll_step} pixels.")
                
    #             try:
    #                 await self.page.wait_for_load_state('load', timeout=args.wait_timeout)
    #                 await self.page.wait_for_timeout(2000)
    #             except Exception as e:
    #                 print(f"Load timed out, falling back to a fixed wait. Error: {e}")
    #                 await self.page.wait_for_timeout(3000)

    #         print("Scrolling complete. Now performing final scrape on all loaded content...")
            
    #         html = await self.page.locator("body").inner_html()
    #         markdown = md(html, strip = ["script", "style", "noscript", "iframe", "object", "embed", "link", "meta", "svg", "canvas"])
            
    #         system_prompt_template = build_scraper_prompt(self.scraper_response_json_format)

    #         messages = [
    #             SystemMessage(content=system_prompt_template).to_dict(),
    #             UserMessage(content=f'User Query: {args.user_query}').to_dict(),
    #             UserMessage(content=f'HTML Content in Markdown Format:\n: {markdown}').to_dict(),
    #         ]

    #         self.model.messages = messages
    #         response = await self.model.generate()
    #         response = response['choices'][0]['message']['content']
    #         final_response = extract_json(response)
    #         return final_response['response']   
    #     except Exception as e:
    #         return f"An error occurred during the scroll and scrape process: {e}"