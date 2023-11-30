from __future__ import annotations

import asyncio
import os

from langchain.memory import ConversationBufferWindowMemory
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.langchain.callbacks import AsyncIteratorCallbackHandler
from xiaogpt.langchain.chain import agent_search
from xiaogpt.utils import split_sentences


class LangChainBot(BaseBot):
    name = "Lang Chain"

    def __init__(
        self,
        openai_key: str,
        serpapi_api_key: str,
        proxy: str | None = None,
        api_base: str | None = None,
    ) -> None:
        # Set environment indicators
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["SERPAPI_API_KEY"] = serpapi_api_key
        if api_base:
            os.environ["OPENAI_API_BASE"] = api_base
        if proxy:
            os.environ["OPENAI_PROXY"] = proxy
        self.memory = ConversationBufferWindowMemory(return_messages=True)

    def has_history(self) -> bool:
        return len(self.memory.chat_memory.messages) > 0

    def change_prompt(self, new_prompt: str) -> None:
        self.memory.clear()
        self.memory.chat_memory.add_user_message(new_prompt)

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key,
            serpapi_api_key=config.serpapi_api_key,
            proxy=config.proxy,
            api_base=config.api_base,
        )

    async def ask(self, query, **options):
        return await agent_search(query, self.memory)

    async def ask_stream(self, query, **options):
        callback = AsyncIteratorCallbackHandler()
        task = asyncio.create_task(agent_search(query, self.memory, callback))
        try:
            async for message in split_sentences(callback.aiter()):
                yield message
        except Exception as e:
            print("An error occurred:", str(e))
        finally:
            print()
            await task
