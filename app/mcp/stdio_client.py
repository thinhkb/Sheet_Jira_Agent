from __future__ import annotations

import json
import os
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from app.mcp.base import MCPToolClient


class StdioMCPClient(MCPToolClient):
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
        name: str = "mcp-server",
    ) -> None:
        self.command = command
        self.args = args
        self.env = env or {}
        self.name = name

        self._stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None

    async def connect(self) -> None:
        if self._session is not None:
            return

        self._stack = AsyncExitStack()

        merged_env = os.environ.copy()
        merged_env.update(self.env)

        params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=merged_env,
        )

        try:
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._session = session
        except Exception:
            # cleanup trong chính task hiện tại
            if self._stack is not None:
                try:
                    await self._stack.aclose()
                except Exception:
                    pass
            self._stack = None
            self._session = None
            raise

    async def close(self) -> None:
        if self._stack is not None:
            try:
                await self._stack.aclose()
            except Exception:
                pass
        self._stack = None
        self._session = None

    async def list_tools(self) -> list[dict[str, Any]]:
        self._require_session()
        response = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        self._require_session()
        result = await self._session.call_tool(tool_name, arguments=arguments)
        return self._normalize_tool_result(result)

    def _require_session(self) -> None:
        if self._session is None:
            raise RuntimeError(f"{self.name} is not connected. Call connect() first.")

    def _normalize_tool_result(self, result: types.CallToolResult) -> Any:
        if result.structuredContent is not None:
            return result.structuredContent

        if not result.content:
            return None

        blocks: list[Any] = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                blocks.append(self._maybe_parse_json(block.text))
            else:
                blocks.append({"type": getattr(block, "type", "unknown"), "value": str(block)})

        return blocks[0] if len(blocks) == 1 else blocks

    @staticmethod
    def _maybe_parse_json(text: str) -> Any:
        text = text.strip()
        if not text:
            return ""
        try:
            return json.loads(text)
        except Exception:
            return {"result": text}