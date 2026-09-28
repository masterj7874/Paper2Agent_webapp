"""Keeps one persistent stdio MCP client per agent (model weights stay loaded between calls) and serialises tool calls
per agent. Uses the FastMCP client library that the generated servers were validated with."""
from __future__ import annotations

import asyncio
import os
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from .config import AgentSpec


class AgentSession:
    def __init__(self, spec: AgentSpec):
        self.spec = spec
        self.client: Client | None = None
        self.lock = asyncio.Lock()
        self.tools: list[dict[str, Any]] = []
        self.status = "stopped"
        self.error: str | None = None

    async def start(self) -> None:
        if self.client is not None:
            return
        env = {**os.environ, **self.spec.env, "MPLBACKEND": "Agg"}
        transport = StdioTransport(command=self.spec.command, args=self.spec.args, env=env, cwd=self.spec.cwd)
        client = Client(transport)
        await client.__aenter__()
        try:
            tools = await client.list_tools()
        except BaseException:
            await client.__aexit__(None, None, None)
            raise
        self.client = client
        self.tools = [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema} for t in tools]
        self.status = "running"
        self.error = None

    async def stop(self) -> None:
        if self.client is not None:
            try:
                await self.client.__aexit__(None, None, None)
            finally:
                self.client = None
                self.status = "stopped"

    async def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        async with self.lock:  # one call at a time per agent (GPU/model state)
            if self.client is None:
                await self.start()
            assert self.client is not None
            try:
                result = await self.client.call_tool(tool, arguments)
            except Exception:
                # a dead server process: restart once and re-raise
                await self.stop()
                raise
            data = getattr(result, "data", None)
            if data is None:
                data = getattr(result, "structured_content", None)
            if data is None:
                data = [getattr(c, "text", str(c)) for c in getattr(result, "content", [])]
            return data


class MCPManager:
    def __init__(self, specs: dict[str, AgentSpec]):
        self.sessions = {name: AgentSession(spec) for name, spec in specs.items()}

    async def start_all(self) -> None:
        async def _start(s: AgentSession):
            try:
                await s.start()
            except Exception as e:  # keep the app up even if one server fails
                s.status, s.error = "error", f"{type(e).__name__}: {e}"
        await asyncio.gather(*(_start(s) for s in self.sessions.values()))

    async def stop_all(self) -> None:
        await asyncio.gather(*(s.stop() for s in self.sessions.values()), return_exceptions=True)

    def get(self, name: str) -> AgentSession:
        if name not in self.sessions:
            raise KeyError(name)
        return self.sessions[name]
