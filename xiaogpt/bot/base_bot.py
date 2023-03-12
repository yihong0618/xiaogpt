from abc import ABC, abstractmethod


class BaseBot(ABC):
    def __init__(self, session):
        self.session = session

    @abstractmethod
    async def ask(self, query):
        pass
