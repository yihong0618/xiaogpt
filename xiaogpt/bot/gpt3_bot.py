import openai
from rich import print

from xiaogpt.utils import split_sentences


class GPT3Bot:
    def __init__(self, openai_key, api_base=None):
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base

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
                print(event["text"], end="")
                yield event["text"]

        try:
            async for sentence in split_sentences(text_gen()):
                yield sentence
        finally:
            print()
