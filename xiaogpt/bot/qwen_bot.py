"""Qwen bot"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin


class QwenBot(ChatHistoryMixin, BaseBot):
    name = "Qian Wen"

    def __init__(self, qwen_key: str) -> None:
        import dashscope
        from dashscope.api_entities.dashscope_response import Role

        self.history = []
        dashscope.api_key = qwen_key

    @classmethod
    def from_config(cls, config):
        return cls(qwen_key=config.qwen_key)

    async def ask(self, query, **options):
        from dashscope import Generation
        from dashscope.api_entities.dashscope_response import Role

        # from https://help.aliyun.com/zh/dashscope/developer-reference/api-details
        self.history.append({"role": Role.USER, "content": query})

        response = Generation.call(
            Generation.Models.qwen_turbo,
            messages=self.history,
            result_format="message",  # set the result to be "message" format.
        )
        if response.status_code == HTTPStatus.OK:
            # append result to messages.
            content = response.output.choices[0]["message"]["content"]
            self.history.append(
                {
                    "role": response.output.choices[0]["message"]["role"],
                    "content": content,
                }
            )
            # keep last five
            first_history = self.history.pop(0)
            self.history = [first_history] + self.history[-5:]
            print(content)
            return content
        else:
            print(
                "Request id: %s, Status code: %s, error code: %s, error message: %s"
                % (
                    response.request_id,
                    response.status_code,
                    response.code,
                    response.message,
                )
            )
            # we need to pop the wrong history
            print(f"Will pop the wrong question {query}")
            self.history.pop()
            return "没有返回"

    async def ask_stream(self, query: str, **options: Any):
        from dashscope import Generation
        from dashscope.api_entities.dashscope_response import Role

        self.history.append({"role": Role.USER, "content": query})
        responses = Generation.call(
            Generation.Models.qwen_turbo,
            messages=self.history,
            result_format="message",  # set the result to be "message" format.
            stream=True,
            incremental_output=True,  # get streaming output incrementally
        )
        full_content = ""  # with incrementally we need to merge output.
        role = None
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]["message"]["content"]
                full_content += content
                if not role:
                    role = response.output.choices[0]["message"]["role"]
                print(content, end="")
                yield content
            else:
                print(
                    "Request id: %s, Status code: %s, error code: %s, error message: %s"
                    % (
                        response.request_id,
                        response.status_code,
                        response.code,
                        response.message,
                    )
                )
        self.history.append({"role": role, "content": full_content})
        first_history = self.history.pop(0)
        self.history = [first_history] + self.history[-5:]
