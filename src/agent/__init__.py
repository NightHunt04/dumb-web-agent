from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def arun(self, query: str):
        pass

    @abstractmethod
    def get_memory(self):
        pass

    @abstractmethod
    async def replay_session(self, session: str):
        pass