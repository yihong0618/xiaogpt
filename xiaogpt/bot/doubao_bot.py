"""Doubao (Volcengine Ark) bot"""

from __future__ import annotations

from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.config import Config
from xiaogpt.utils import split_sentences


class DoubaoBot(ChatHistoryMixin, BaseBot):
    name = "豆包"
    default_options = {"model": "doubao-pro-32k"}

    def __init__(self, api_key: str) -> None:
        from volcenginesdkarkruntime import AsyncArk

        self.api_key = api_key
        self.history = []
        self.client = AsyncArk(api_key=api_key)

    @classmethod
    def from_config(cls, config: Config):
        return cls(api_key=config.volc_api_key)

    def _get_data(self, query: str, **options: Any):
        options = {**self.default_options, **options}
        model = options.pop("model")
        ms = self.get_messages()
        ms.append({"role": "user", "content": query})
        return {"model": model, "messages": ms}

    async def ask(self, query, **options):
        data = self._get_data(query, **options)
        try:
            completion = await self.client.chat.completions.create(**data)
            message = completion.choices[0].message.content
            self.add_message(query, message)
            print(message)
            return message
        except Exception as e:
            print(str(e))
            return ""

    async def ask_stream(self, query: str, **options: Any):
        data = self._get_data(query, **options)
        data["stream"] = True

        try:
            completion = await self.client.chat.completions.create(**data)
        except Exception as e:
            print(str(e))
            return

        async def text_gen():
            async for chunk in completion:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content is None:
                    continue
                print(content, end="", flush=True)
                yield content

        message = ""
        try:
            async for sentence in split_sentences(text_gen()):
                message += sentence
                yield sentence
        finally:
            print()
            self.add_message(query, message)
