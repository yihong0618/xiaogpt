"""ChatGLM bot"""
from __future__ import annotations
from typing import Any, AsyncGenerator

import zhipuai
from rich import print

from xiaogpt.bot.base_bot import BaseBot


class GLMBot(BaseBot):
    default_options = {"model": "chatglm_130b"}

    def __init__(
        self,
        glm_key: str,
    ) -> None:
        self.history = []
        zhipuai.api_key = glm_key

    @classmethod
    def from_config(cls, config):
        return cls(glm_key=config.glm_key)

    def ask(self, query, **options):
        ms = []
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        kwargs = {**self.default_options, **options}
        kwargs["prompt"] = ms
        ms.append({"role": "user", "content": f"{query}"})
        try:
            r = zhipuai.model_api.sse_invoke(**kwargs)
        except Exception as e:
            print(str(e))
            return
        message = ""
        for i in r.events():
            message += str(i.data)

        self.history.append([f"{query}", message])
        # only keep 5 history
        first_history = self.history.pop(0)
        self.history = [first_history] + self.history[-5:]
        print(message)
        return message

    def ask_stream(self, query: str, **options: Any):
        raise Exception("GLM do not support stream")
