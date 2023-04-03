import asyncio

from EdgeGPT import Chatbot, ConversationStyle
from rich import print

from xiaogpt.utils import split_sentences


class NewBingBot:
    def __init__(self, proxy=None, bing_cookie_path: str = ""):
        self.history = []
        self._bot = Chatbot(cookiePath=bing_cookie_path, proxy=proxy)

    async def ask(self, query, **options):
        completion = await self._bot.ask(prompt=query, **options)
        print(completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])
        return completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]

    async def ask_stream(self, query, **options):
        raise NotImplementedError("ask_stream not implement")
