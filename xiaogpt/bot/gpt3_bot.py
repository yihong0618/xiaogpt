import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.utils import split_sentences


class GPT3Bot(BaseBot):
    def __init__(self, openai_key, api_base=None, proxy=None):
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base
        if proxy:
            openai.proxy = proxy
        self.history = []

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key, api_base=config.api_base, proxy=config.proxy
        )

    async def ask(self, query, **options):
        data = {
            "prompt": query,
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
            **options,
        }
        completion = await openai.Completion.acreate(**data)
        print(completion["choices"][0]["text"])
        return completion["choices"][0]["text"]

    async def ask_stream(self, query, **options):
        data = {
            "prompt": query,
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
            "stream": True,
            **options,
        }
        completion = await openai.Completion.acreate(**data)

        async def text_gen():
            async for event in completion:
                text = event["choices"][0]["text"]
                print(text, end="")
                yield text

        try:
            async for sentence in split_sentences(text_gen()):
                yield sentence
        finally:
            print()
