from EdgeGPT import Chatbot, ConversationStyle
from rich import print

from xiaogpt.utils import split_sentences


class EdgeGPTBot:
    def __init__(self, cookie_file, conversation_style="creative", proxy=None):
        self.history = []
        self._bot = Chatbot(proxy=proxy, cookiePath=cookie_file)
        self._wss_link = "wss://sydney.bing.com/sydney/ChatHub"
        self._conversation_style = ConversationStyle.creative
        if conversation_style == "balanced":
            self._conversation_style = ConversationStyle.balanced
        elif conversation_style == "precise":
            self._conversation_style = ConversationStyle.precise

    async def ask(self, query, **options):
        completion = await self._bot.ask(prompt=query, conversation_style=self._conversation_style, wss_link=self._wss_link)
        print(completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])
        return completion["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]

    async def ask_stream(self, query, **options):
        completion = await self._bot.ask_stream(prompt=query, conversation_style=self._conversation_style, wss_link=self._wss_link)

        wrote = 0
        async for final, response in completion:
            if not final:
                sentence = response[wrote:]
                print(sentence, end="")
                wrote = len(response)
                yield sentence
        print()

        #async def text_gen():
        #    wrote = 0
        #    async for response in completion:
        #        text = response[wrote:]
        #        print(text, end="")
        #        wrote = len(response)
        #        yield text

        #try:
        #    async for sentence in split_sentences(text_gen()):
        #        yield sentence
        #finally:
        #    print()
