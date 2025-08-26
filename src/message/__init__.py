from abc import ABC

class BaseMessage(ABC):
    def to_dict(self) -> dict[str, str]:
        return {
            'role': self.role,
            'content': self.content
        }

class UserMessage(BaseMessage):
    def __init__(self, content: str) -> None:
        self.role = 'user'
        self.content = content

class AIMessage(BaseMessage):
    def __init__(self, content: str) -> None:
        self.role = 'assistant'
        self.content = content

class SystemMessage(BaseMessage):
    def __init__(self, content: str) -> None:
        self.role = 'system'
        self.content = content