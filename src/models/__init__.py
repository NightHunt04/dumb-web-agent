from abc import ABC, abstractmethod
from typing import List, Any, Union
from ..message import (
    AIMessage, 
    UserMessage, 
    SystemMessage
)

class BaseModel(ABC):
    @property
    @abstractmethod
    def messages(self) -> List[Any]:
        pass

    @messages.setter
    @abstractmethod
    def messages(self, message: List[Union[AIMessage, UserMessage, SystemMessage]]):
        pass

    @abstractmethod
    def add_message(self, message: Union[AIMessage, UserMessage, SystemMessage]):
        pass
    
    @abstractmethod
    async def generate(self, query: str):
        pass

    @abstractmethod
    def configure(self, **kwargs):
        pass