import asyncio

from EdgeGPT import Chatbot, ConversationStyle
from rich import print

from xiaogpt.utils import split_sentences


class EdgeGPTBot:
    def __init__(self, proxy=None, cookiePath: str = ""):
        self.history = []
        self._bot = Chatbot(cookiePath=cookiePath, proxy=proxy)

    async def ask(
        self,
        query,
        wss_link="wss://sydney.bing.com/sydney/ChatHub",
        conversation_style=ConversationStyle.creative,
        **options,
    ):
        completion = await self._bot.ask(
            prompt=query, wss_link=wss_link, conversation_style=conversation_style
        )
        print(completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])
        return completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]

    async def ask_stream(self, query, **options):
        raise NotImplementedError("ask_stream not implement")
