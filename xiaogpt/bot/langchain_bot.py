from __future__ import annotations

import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.utils import split_sentences

from xiaogpt.langchain.chain import agent_search
from xiaogpt.langchain.stream_call_back import streaming_call_queue


class LangChainBot(BaseBot):
    def __init__(
        self,
    ) -> None:
        # todo，建议在langchain内实现
        self.history = []

    @classmethod
    def from_config(cls, config):
        return cls()

    async def ask(self, query, **options):
        # todo，目前仅支持stream
        raise Exception("The bot does not support it. Please use 'ask_stream'.")

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
            # 处理异常的代码
            print("An error occurred:", str(e))
