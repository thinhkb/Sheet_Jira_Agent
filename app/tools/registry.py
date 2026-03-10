from __future__ import annotations

from typing import Any, Callable


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self.tools[name] = fn

    def get_all(self) -> dict[str, Callable[..., Any]]:
        return self.tools