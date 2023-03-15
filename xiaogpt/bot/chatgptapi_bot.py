import openai

from xiaogpt.bot.base_bot import BaseBot


class ChatGPTBot(BaseBot):
    def __init__(self, openai_key, api_base=None):
        self.history = []
        openai.api_key = openai_key
        if api_base:
            openai.api_base = api_base

    async def ask(self, query):
        ms = []
        for h in self.history:
            ms.append({"role": "user", "content": h[0]})
            ms.append({"role": "assistant", "content": h[1]})
        ms.append({"role": "user", "content": f"{query}"})
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=ms)
        message = (
            completion["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )
        self.history.append([f"{query}", message])
        # only keep 5 history
        self.history = self.history[-5:]
        return message
