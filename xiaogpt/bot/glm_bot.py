"""ChatGLM bot"""

from __future__ import annotations

from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin


class GLMBot(ChatHistoryMixin, BaseBot):
    name = "Chat GLM"
    default_options = {"model": "chatglm_turbo"}

    def __init__(self, glm_key: str) -> None:
        from zhipuai import ZhipuAI

        self.model = "glm-4"  # Change glm model here

        self.history = []
        self.client = ZhipuAI(api_key=glm_key)

    @classmethod
    def from_config(cls, config):
        return cls(glm_key=config.glm_key)

    def ask(self, query, **options):
        ms = self.get_messages()
        kwargs = {**self.default_options, **options}
        kwargs["model"] = self.model
        ms.append({"role": "user", "content": f"{query}"})
        kwargs["messages"] = ms
        try:
            r = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            print(str(e))
            return
        message = r.choices[0].message.content

        self.add_message(query, message)
        print(message)
        return message

    async def ask_stream(self, query: str, **options: Any):
        ms = self.get_messages()
        kwargs = {**self.default_options, **options}
        kwargs["model"] = self.model
        ms.append({"role": "user", "content": f"{query}"})
        kwargs["messages"] = ms
        kwargs["stream"] = True
        try:
            r = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            print(str(e))
            return
        full_content = ""
        for chunk in r:
            content = chunk.choices[0].delta.content
            full_content += content
            print(content, end="")
            yield content
        self.add_message(query, full_content)
