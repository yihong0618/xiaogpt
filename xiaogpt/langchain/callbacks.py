from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler


class AsyncIteratorCallbackHandler(AsyncCallbackHandler):
    """Callback handler that returns an async iterator."""

    @property
    def always_verbose(self) -> bool:
        return True

    def __init__(self) -> None:
        self.queue = asyncio.Queue()
        self.done = asyncio.Event()

    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if parent_run_id is None:
            self.done.clear()

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        if token is not None and token != "":
            print(token, end="", flush=True)
            self.queue.put_nowait(token)

    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if parent_run_id is None:
            self.done.set()

    async def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if parent_run_id is None:
            self.done.set()

    async def aiter(self) -> AsyncIterator[str]:
        while not self.queue.empty() or not self.done.is_set():
            token_task = asyncio.create_task(self.queue.get())
            done_task = asyncio.create_task(self.done.wait())
            try:
                done, _ = await asyncio.wait(
                    [token_task, done_task], return_when=asyncio.FIRST_COMPLETED
                )
                # Both tasks may finish together; keep the final queued token.
                if token_task in done:
                    yield token_task.result()
            finally:
                for task in (token_task, done_task):
                    if not task.done():
                        task.cancel()
                await asyncio.gather(token_task, done_task, return_exceptions=True)
