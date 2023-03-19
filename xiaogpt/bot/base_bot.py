from abc import ABC, abstractmethod


class BaseBot(ABC):
    @abstractmethod
    async def ask(self, query):
        pass

    @abstractmethod
    async def ask_stream(self, query):
        pass
