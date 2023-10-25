from __future__ import annotations

import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.utils import split_sentences

from xiaogpt.langchain.chain import agent_search
from xiaogpt.langchain.stream_call_back import streaming_call_queue

import os


class LangChainBot(BaseBot):
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
        # Todo，Plan to implement within langchain
        self.history = []

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key,
            serpapi_api_key=config.serpapi_api_key,
            proxy=config.proxy,
            api_base=config.api_base,
        )

    async def ask(self, query, **options):
        # Todo，Currently only supports stream
        raise Exception(
            "The bot does not support it. Please use 'ask_stream，add： --stream'"
        )

    async def ask_stream(self, query, **options):
        agent_search(query)
        try:
            while True:
                if not streaming_call_queue.empty():
                    token = streaming_call_queue.get()
                    print(token, end="")
                    yield token
                else:
                    break
        except Exception as e:
            print("An error occurred:", str(e))
