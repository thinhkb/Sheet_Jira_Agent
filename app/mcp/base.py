from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MCPToolClient(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        raise NotImplementedError