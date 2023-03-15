import openai


class GPT3Bot:
    def __init__(self, openai_key, api_base=None):
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base

    async def ask(self, query):
        data = {
            "prompt": query,
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
        }
        completion = openai.Completion.create(**data)
        return completion["choices"][0]["text"]
