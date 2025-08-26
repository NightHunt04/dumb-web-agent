from abc import ABC, abstractmethod
from ..dom import DOM
from ..dom.state import DOMState
from ..models import BaseModel
from typing import Dict, Any, Optional    
from playwright.async_api import Page

class BaseTool(ABC):
    """
    Abstract base class for tools.

    Args:
        page (Optional[Page]): The page to use for the tool
        dom (Optional[DOM]): The DOM to use for the tool
        dom_state (Optional[DOMState]): The DOM state to use for the tool
        model (Optional[BaseModel]): The model to use for the tool
        scraper_response_json_format (Optional[Dict[str, Any]]): The scraper response JSON format to use for the tool
    """

    def __init__(
            self, 
            page: Optional[Page] = None, 
            dom: Optional[DOM] = None, 
            dom_state: Optional[DOMState] = None,
            model: Optional[BaseModel] = None,
            scraper_response_json_format: Optional[Dict[str, Any]] = None,
        ) -> None:
        self.page = page
        self.dom = dom
        self.dom_state = dom_state
        self.model = model
        self.scraper_response_json_format = scraper_response_json_format    

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the tool
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Returns the description of the tool
        """
        pass

    @property
    @abstractmethod
    def args_schema(self) -> Dict[str, Any]:
        """
        Returns the argument's schema of the tool
        """
        pass

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        Runs the tool
        """
        pass

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema of the tool
        """
        return {
            "name": self.name,
            "description": self.description,
            "args": self.args_schema
        }