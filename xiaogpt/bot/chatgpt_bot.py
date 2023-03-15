from revChatGPT.V1 import Chatbot, configure

from xiaogpt.bot.base_bot import BaseBot


class ChatBot(BaseBot):
    def __init__(self) -> None:
        self._bot = Chatbot(configure())
        self.conversation_id = None
        self.parent_id = None

    async def ask(self, query):
        # TODO maybe use v2 to async it here
        if self.conversation_id and self.parent_id:
            data = list(
                self._bot.ask(
                    query,
                    conversation_id=self.conversation_id,
                    parent_id=self.parent_id,
                )
            )[-1]
        else:
            data = list(self._bot.ask(query))[-1]
        if message := data.get("message", ""):
            self.conversation_id = data.get("conversation_id")
            self.parent_id = data.get("parent_id")
            # xiaoai tts did not support space
            return message
        return ""
