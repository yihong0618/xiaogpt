"""ChatGLM bot"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.config import Config
from xiaogpt.utils import split_sentences


class DoubaoBot(ChatHistoryMixin, BaseBot):
    name = "豆包"
    default_options = {"model": "skylark-chat"}  # 根据官方示例修改默认模型

    def __init__(self, api_key: str) -> None:
        from volcenginesdkarkruntime import Ark  # 引入官方 SDK
        
        self.api_key = api_key
        self.history = []
        self.client = Ark(api_key=api_key)  # 初始化客户端

    @classmethod
    def from_config(cls, config: Config):
        return cls(api_key=config.volc_api_key)  # 假设配置文件中有 volc_api_key 字段

    def _get_data(self, query: str, **options: Any):
        options = {**self.default_options, **options}
        model = options.pop("model")
        ms = self.get_messages()
        ms.append({"role": "user", "content": query})
        return {"model": model, "messages": ms}

    async def ask(self, query, **options):
        data = self._get_data(query, **options)
        try:
            completion = self.client.chat.completions.create(**data)
            message = completion.choices[0].message.content
            self.add_message(query, message)
            print(message)
            return message
        except Exception as e:
            print(str(e))
            return

    async def ask_stream(self, query: str, **options: Any):
        data = self._get_data(query, **options)
        data["stream"] = True

        try:
            full_content = ""
            for chunk in self.client.chat.completions.create(**data):
                content = chunk.choices[0].delta.content
                if content:
                    full_content += content
                    print(content, end="", flush=True)
                    yield content
            print()
            self.add_message(query, full_content)
        except Exception as e:
            print(str(e))
            return
