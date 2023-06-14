from __future__ import annotations

import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.utils import split_sentences


class ChatGPTBot(BaseBot):
    default_options = {"model": "gpt-3.5-turbo-0613"}

    def __init__(
        self,
        openai_key: str,
        api_base: str | None = None,
        proxy: str | None = None,
        deployment_id: str | None = None,
    ) -> None:
        self.history = []
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base
            # if api_base ends with openai.azure.com, then set api_type to azure
            if api_base.endswith(("openai.azure.com/", "openai.azure.com")):
                openai.api_type = "azure"
                openai.api_version = "2023-03-15-preview"
                self.default_options = {
                    **self.default_options,
                    "engine": deployment_id,
                }
        if proxy:
            openai.proxy = proxy

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key,
            api_base=config.api_base,
            proxy=config.proxy,
            deployment_id=config.deployment_id,
        )

    async def ask(self, query, **options):
        ms = []
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        ms.append({"role": "user", "content": f"{query}"})
        kwargs = {**self.default_options, **options}
        completion = await openai.ChatCompletion.acreate(messages=ms, **kwargs)
        message = (
            completion["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )
        self.history.append([f"{query}", message])
        # only keep 5 history
        first_history = self.history.pop(0)
        self.history = [first_history] + self.history[-5:]
        print(message)
        return message

    async def ask_stream(self, query, **options):
        ms = []
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        ms.append({"role": "user", "content": f"{query}"})
        kwargs = {"model": "gpt-3.5-turbo", **options}
        if openai.api_type == "azure":
            kwargs["deployment_id"] = self.deployment_id
        completion = await openai.ChatCompletion.acreate(
            messages=ms, stream=True, **kwargs
        )

        async def text_gen():
            async for event in completion:
                chunk_message = event["choices"][0]["delta"]
                if "content" not in chunk_message:
                    continue
                print(chunk_message["content"], end="")
                yield chunk_message["content"]

        message = ""
        try:
            async for sentence in split_sentences(text_gen()):
                message += sentence
                yield sentence
        finally:
            print()
            self.history.append([f"{query}", message])
            first_history = self.history.pop(0)
            self.history = [first_history] + self.history[-5:]
