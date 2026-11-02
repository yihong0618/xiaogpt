"""Exercise the Republic-backed chat bot offline, mocking only the HTTP transport."""

import json
import unittest
from unittest.mock import patch

import httpx2

from xiaogpt.bot import MAX_HISTORY_MESSAGES, Chatbot
from xiaogpt.config import Config


def completion(payload: dict) -> httpx2.Response:
    if payload.get("stream"):
        chunks = [
            {"choices": [{"index": 0, "delta": {"content": text}}]}
            for text in ("你好。", "今天", "不错！")
        ]
        chunks.append({"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        body = "".join(
            f"data: {json.dumps({'id': 'x', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'test', **c})}\n\n"
            for c in chunks
        )
        return httpx2.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body + "data: [DONE]\n\n",
        )
    return httpx2.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
        },
    )


class ChatbotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []

        async def respond(transport, request):
            self.requests.append((request, json.loads(request.content)))
            return completion(self.requests[-1][1])

        patcher = patch.object(
            httpx2.AsyncHTTPTransport, "handle_async_request", respond
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_bot(self, **options) -> Chatbot:
        config = Config(
            model="openai:test-model",
            api_key="test",
            api_base="https://llm.example/v1",
            api_format="chat",
            **options,
        )
        bot = Chatbot(config)
        self.addAsyncCleanup(bot.close)
        return bot

    async def test_ask_and_stream_keep_history(self):
        bot = self.make_bot(gpt_options={"temperature": 0.5})
        self.assertEqual(bot.name, "test-model")
        self.assertEqual(await bot.ask("first", **bot.config.gpt_options), "ok")
        self.assertEqual(
            [part async for part in bot.ask_stream("second")],
            ["你好。", "今天不错！"],
        )
        request, first = self.requests[0]
        self.assertEqual(str(request.url), "https://llm.example/v1/chat/completions")
        self.assertEqual(request.headers["authorization"], "Bearer test")
        self.assertEqual(first["model"], "test-model")
        self.assertEqual(first["temperature"], 0.5)
        _, second = self.requests[1]
        self.assertEqual(
            [(m["role"], m["content"]) for m in second["messages"]],
            [
                ("system", bot.config.prompt),
                ("user", "first"),
                ("assistant", "ok"),
                ("user", "second"),
            ],
        )
        self.assertEqual(len(bot.history), 4)

    async def test_prompt_change_and_history_limit(self):
        bot = self.make_bot()
        for index in range(8):
            await bot.ask(str(index))
        bot.config.prompt = "new prompt"
        await bot.ask("last")
        messages = self.requests[-1][1]["messages"]
        self.assertEqual(messages[0], {"role": "system", "content": "new prompt"})
        self.assertEqual(len(messages), MAX_HISTORY_MESSAGES + 2)
        self.assertEqual(len(bot.history), MAX_HISTORY_MESSAGES)

    async def test_proxy(self):
        bot = self.make_bot(proxy="http://localhost:8888")
        self.assertEqual(await bot.ask("hello"), "ok")


class ConfigTests(unittest.TestCase):
    def test_legacy_gpt_options_model(self):
        config = Config(gpt_options={"model": "gpt-4o", "temperature": 1})
        self.assertEqual(config.model, "openai:gpt-4o")
        self.assertEqual(config.gpt_options, {"temperature": 1})
        config = Config(gpt_options={"model": "deepseek:deepseek-chat"})
        self.assertEqual(config.model, "deepseek:deepseek-chat")

    def test_invalid_model(self):
        with self.assertRaises(ValueError):
            Config(model="gpt-4o")

    def test_openai_key_fallback(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            self.assertEqual(Config().api_key, "env-key")
            self.assertEqual(Config(model="deepseek:deepseek-chat").api_key, "")


class DoubaoProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_doubao_request(self):
        requests = []

        async def respond(transport, request):
            requests.append((request, json.loads(request.content)))
            return completion(requests[-1][1])

        with patch.object(httpx2.AsyncHTTPTransport, "handle_async_request", respond):
            bot = Chatbot(
                Config(
                    model="doubao:ep-test",
                    api_key="test",
                    gpt_options={"reasoning_effort": "none", "max_tokens": 100},
                )
            )
            self.addAsyncCleanup(bot.close)
            self.assertEqual(await bot.ask("hello", **bot.config.gpt_options), "ok")
        request, body = requests[0]
        self.assertEqual(
            str(request.url),
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        )
        self.assertEqual(request.headers["authorization"], "Bearer test")
        self.assertEqual(body["model"], "ep-test")
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertEqual(body["max_tokens"], 100)
        self.assertNotIn("reasoning_effort", body)

    def test_ark_api_key_fallback(self):
        with patch.dict("os.environ", {"ARK_API_KEY": "ark-key"}):
            self.assertEqual(Config(model="doubao:ep-test").api_key, "ark-key")
