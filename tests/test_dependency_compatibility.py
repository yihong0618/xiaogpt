"""Exercise upgraded SDKs offline, mocking only their HTTP transports."""

import asyncio
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
from google import genai
from google.genai import types
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from xiaogpt.bot.chatgptapi_bot import ChatGPTBot
from xiaogpt.bot.gemini_bot import GeminiBot
from xiaogpt.bot.jiekou_bot import JiekouBot
from xiaogpt.bot.langchain_bot import LangChainBot
from xiaogpt.bot.llama_bot import LlamaBot
from xiaogpt.bot.moonshot_bot import MoonshotBot
from xiaogpt.bot.ppio_bot import PPIOBot
from xiaogpt.bot.yi_bot import YiBot
from xiaogpt.langchain.chain import agent_search
from xiaogpt.langchain.callbacks import AsyncIteratorCallbackHandler
from xiaogpt.langchain.examples.email.mail_summary_tools import MailSummaryTool


class OpenAICompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_completion_and_stream_with_proxy(self):
        bots = [
            ChatGPTBot("test"),
            ChatGPTBot("test", api_base="https://test.openai.azure.com"),
            JiekouBot("test"),
            PPIOBot("test"),
            MoonshotBot("test"),
            YiBot("test"),
            LlamaBot("test"),
        ]
        requests = []

        async def respond(transport, request):
            payload = json.loads(request.content)
            requests.append(payload)
            if payload.get("stream"):
                chunk = {
                    "id": "test",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "test",
                    "choices": [{"index": 0, "delta": {"content": "stream!"}}],
                }
                return httpx.Response(
                    200,
                    headers={"content-type": "text/event-stream"},
                    content=f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n",
                )
            return httpx.Response(
                200,
                json={
                    "id": "test",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "test",
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": "ok"}}
                    ],
                },
            )

        with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", respond):
            for bot in bots:
                with self.subTest(bot=bot.name, endpoint=bot.api_base):
                    bot.proxy = "http://localhost:8888"
                    self.assertEqual(await bot.ask("hello"), "ok")
                    self.assertEqual(
                        [part async for part in bot.ask_stream("again")], ["stream!"]
                    )
                    self.assertEqual(requests[-1]["messages"][1]["content"], "ok")
                    self.assertTrue(bot.has_history())


class GeminiCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_messages_streaming_history_and_custom_endpoint(self):
        requests = []
        original_client = genai.Client

        def respond(request):
            requests.append((str(request.url), json.loads(request.content)))
            candidate = {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}
            if "streamGenerateContent" in request.url.path:
                empty = {"candidates": [{"content": {"parts": []}}]}
                return httpx.Response(
                    200,
                    headers={"content-type": "text/event-stream"},
                    content=f"data: {json.dumps(empty)}\n\ndata: {json.dumps(candidate)}\n\n",
                )
            return httpx.Response(200, json=candidate)

        def make_client(**kwargs):
            http_client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
            self.addAsyncCleanup(http_client.aclose)
            options = kwargs.get("http_options") or types.HttpOptions()
            kwargs["http_options"] = options.model_copy(
                update={"httpx_async_client": http_client}
            )
            return original_client(**kwargs)

        bot = GeminiBot("test", "gemini.example", "custom-model")
        with patch.object(genai, "Client", side_effect=make_client):
            self.assertEqual(await bot.ask("first"), "hello")
            self.assertTrue(bot.has_history())
            bot.change_prompt("new prompt")
            self.assertEqual(
                [part async for part in bot.ask_stream("second")], ["hello"]
            )
            for index in range(8):
                await bot.ask(str(index))
        url, body = requests[1]
        self.assertTrue(url.startswith("https://gemini.example/"))
        self.assertIn("custom-model:streamGenerateContent", url)
        self.assertEqual(
            [c["role"] for c in body["contents"]], ["user", "model", "user"]
        )
        self.assertEqual(body["contents"][0]["parts"][0]["text"], "new prompt")
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 4096)
        self.assertEqual(len(body["safetySettings"]), 4)
        self.assertLessEqual(len(bot.history), 6)

    def test_endpoint_with_scheme_and_default_endpoint(self):
        bot = GeminiBot("test", "https://gemini.example/", "custom")
        self.assertEqual(
            bot.client_options["http_options"].base_url, "https://gemini.example"
        )
        self.assertNotIn("http_options", GeminiBot("test", "", "custom").client_options)


class LangChainCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_survives_nested_chain_completion(self):
        model = FakeListChatModel(responses=["complete answer!"])
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("xiaogpt.langchain.chain.ChatOpenAI", return_value=model),
            patch(
                "xiaogpt.langchain.chain.SerpAPIWrapper",
                return_value=SimpleNamespace(run=lambda query: "search result"),
            ),
        ):
            bot = LangChainBot("test", "test")

            async def collect():
                return "".join([part async for part in bot.ask_stream("hello")])

            self.assertEqual(await asyncio.wait_for(collect(), 5), "complete answer!")

    async def test_callback_drains_final_tokens_and_ignores_child_end(self):
        callback = AsyncIteratorCallbackHandler()
        await callback.on_chain_end({}, run_id=uuid4(), parent_run_id=uuid4())
        self.assertFalse(callback.done.is_set())
        await callback.on_llm_new_token("last token")
        await callback.on_chain_end({}, run_id=uuid4())
        self.assertEqual([token async for token in callback.aiter()], ["last token"])

    async def test_agent_and_conversation_memory(self):
        model = FakeMessagesListChatModel(responses=[AIMessage(content="answer")])
        with patch.dict(os.environ, {}, clear=False):
            bot = LangChainBot("test", "test")
            with (
                patch("xiaogpt.langchain.chain.ChatOpenAI", return_value=model),
                patch(
                    "xiaogpt.langchain.chain.SerpAPIWrapper",
                    return_value=SimpleNamespace(run=lambda query: "search result"),
                ),
            ):
                self.assertEqual(await agent_search("hello", bot.memory), "answer")
            self.assertTrue(bot.has_history())
            bot.change_prompt("new prompt")
            self.assertEqual(len(bot.memory.chat_memory.messages), 1)
            self.assertEqual(bot.memory.chat_memory.messages[0].content, "new prompt")
        self.assertEqual(MailSummaryTool().name, "MailSumary")
