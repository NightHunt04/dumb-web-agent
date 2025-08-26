from .__init__ import BaseModel
from litellm import acompletion
from ..message import (
    UserMessage, 
    SystemMessage, 
    AIMessage
)
from typing import List, Union, Any

class GeminiProvider(BaseModel):
    """
    Gemini model for generating text completion

    Args:
        api_key (str): The API key for the Gemini model
        model (str): The model to use for text completion
        max_tokens (int): The maximum number of tokens to generate
        reasoning_effort (str): The reasoning effort to use for text completion
        temperature (float): The temperature to use for text completion
        top_p (float): The top_p to use for text completion
    """
    
    def __init__(
            self, 
            api_key: str, 
            model: str = 'gemini-2.5-flash', 
            max_tokens: int = 19334,
            reasoning_effort: str = 'disable',  
            temperature: float = 0.4,
            top_p: float = 1.0
        ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        self.top_p = top_p
        self._messages = []
        self.provider = 'gemini/'

    @property
    def messages(self) -> List[Any]:
        return self._messages

    @messages.setter
    def messages(self, messages: List[Union[AIMessage, UserMessage, SystemMessage]]):
        self._messages = messages

    def add_message(self, message: Union[AIMessage, UserMessage, SystemMessage]):
        self._messages.append(message)

    async def generate(self) -> str:
        """
        Generates text completion from Gemini model

        Args:
            query (str): The input query to generate completion for

        Returns:
            str: The generated text completion
        """
               
        response = await acompletion(
            model = self.provider + self.model,
            messages = self.messages,
            max_tokens = self.max_tokens,
            api_key = self.api_key,
            reasoning_effort = self.reasoning_effort,
            response_format = { "type": "json_object" },
            stream = False,
            temperature = self.temperature,
            top_p = self.top_p,
            timeout = 10000,
        )
        return response
    
    def configure(
        self, 
        api_key: str | None = None, 
        model: str | None = None, 
        max_tokens: int | None = None, 
        reasoning_effort: str | None = None, 
        temperature: float | None = None, 
        top_p: float | None = None
    ) -> None:
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens
        if reasoning_effort:
            self.reasoning_effort = reasoning_effort
        if temperature:
            self.temperature = temperature
        if top_p:
            self.top_p = top_p