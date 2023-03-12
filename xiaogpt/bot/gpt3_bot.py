from xiaogpt.config import OPENAI_API_KEY


class GPT3Bot:
    def __init__(self, session, openai_key):
        self.openai_key = openai_key
        self.api_url = "https://api.openai.com/v1/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}",
        }
        # TODO support more models here
        self.data = {
            "prompt": "",
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
        }
        self.session = session

    async def ask(self, query):
        self.data["prompt"] = query
        r = await self.session.post(self.api_url, headers=self.headers, json=self.data)
        print(1111)
        return await r.json()
