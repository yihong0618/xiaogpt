import openai

from xiaogpt.bot.base_bot import BaseBot


class ChatGPTBot(BaseBot):
    def __init__(self, session, openai_key, api_base=None):
        self.session = session
        self.history = []
        self.api_base = api_base
        self.openai_key = openai_key

    async def ask(self, query):
        openai.api_key = self.openai_key
        if self.api_base:
            openai.api_base = self.api_base
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
