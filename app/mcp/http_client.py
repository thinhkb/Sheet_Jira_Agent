from __future__ import annotations

import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.mcp.base import MCPToolClient


class HttpMCPClient(MCPToolClient):
    def __init__(self, url: str, name: str = "http-mcp"):
        self.url = url
        self.name = name
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def connect(self) -> None:
        if self._session is not None:
            return

        self._stack = AsyncExitStack()
        try:
            read, write, _ = await self._stack.enter_async_context(
                streamablehttp_client(self.url)
            )
            session = await self._stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self._session = session
        except Exception:
            if self._stack is not None:
                try:
                    await self._stack.aclose()
                except BaseException:
                    pass
            self._stack = None
            self._session = None
            raise

    async def close(self) -> None:
        if self._stack is not None:
            try:
                await self._stack.aclose()
            except BaseException:
                # swallow cleanup/cancel errors when shutting down streamable HTTP client
                pass

        self._stack = None
        self._session = None

    async def list_tools(self):
        resp = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in resp.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]):
        result = await self._session.call_tool(tool_name, arguments)

        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return structured

        content = getattr(result, "content", None)
        if content:
            first = content[0]
            text = getattr(first, "text", None)

            if text is not None:
                try:
                    parsed = json.loads(text)

                    # nếu tool trả {"result": "...json string..."}
                    if isinstance(parsed, dict) and "result" in parsed and isinstance(parsed["result"], str):
                        inner = parsed["result"].strip()
                        try:
                            return json.loads(inner)
                        except Exception:
                            return parsed

                    return parsed
                except Exception:
                    return text

            return str(first)

        return None