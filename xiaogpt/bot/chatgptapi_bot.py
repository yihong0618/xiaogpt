import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.utils import split_sentences


class ChatGPTBot(BaseBot):
    def __init__(self, openai_key, api_base=None, proxy=None):
        self.history = []
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base
        if proxy:
            openai.proxy = proxy

    async def ask(self, query, **options):
        ms = []
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        ms.append({"role": "user", "content": f"{query}"})
        completion = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo", messages=ms, **options
        )
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
        completion = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo", messages=ms, stream=True, **options
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
