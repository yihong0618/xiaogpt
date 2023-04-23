from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, TypeVar

from xiaogpt.config import Config

T = TypeVar("T", bound="BaseBot")


class BaseBot(ABC):
    history: list

    @abstractmethod
    async def ask(self, query: str, **options: Any) -> str:
        pass

    @abstractmethod
    async def ask_stream(self, query: str, **options: Any) -> AsyncGenerator[str, None]:
        pass

    @classmethod
    @abstractmethod
    def from_config(cls: type[T], config: Config) -> T:
        pass
