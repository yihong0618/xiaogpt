"""Extra Republic providers that are not built into Republic."""

from __future__ import annotations

from typing import Any

import republic
from republic import ReasoningEffort
from republic.formats import ChatFormat
from republic.providers import OpenAICompatible


class DoubaoChat(ChatFormat):
    """Volcengine Ark chat completions.

    Ark limits output with ``max_tokens`` and switches thinking on or off with
    ``thinking.type``; ``reasoning_effort="none"`` turns thinking off.
    """

    def max_tokens_fields(self, max_tokens: int) -> dict[str, Any]:
        return {"max_tokens": max_tokens}

    def reasoning_fields(
        self, effort: ReasoningEffort | None, *, include_reasoning: bool
    ) -> dict[str, Any]:
        if effort is None:
            return {}
        return {"thinking": {"type": "disabled" if effort == "none" else "enabled"}}


class Doubao(OpenAICompatible):
    """ByteDance Doubao models on Volcengine Ark.

    The model is a model ID such as ``doubao-seed-1-6-250615`` or an inference
    endpoint ID such as ``ep-xxxx``.
    """

    name = "doubao"
    DEFAULT_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    CHAT_FORMAT = DoubaoChat()


republic.register_provider(Doubao)
