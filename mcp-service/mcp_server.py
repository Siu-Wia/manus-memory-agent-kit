from __future__ import annotations

import os
import secrets
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from store import MemoryStore

mcp = FastMCP("Manus Memory")
store = MemoryStore()


def _bearer_token_from_headers() -> str | None:
    try:
        authorization = get_http_headers(include={"authorization"}).get("authorization", "")
    except Exception:
        authorization = ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    return None


def require_token(api_token: str | None = None) -> None:
    expected = os.environ.get("MEMORY_API_TOKEN", "").strip()
    if not expected:
        raise ValueError("MEMORY_API_TOKEN is not configured on the server")
    supplied = (api_token or "").strip() or _bearer_token_from_headers()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise ValueError("invalid api_token or bearer token")


@mcp.tool
def save_memory(
    type: str,
    title: str,
    content: str,
    api_token: str | None = None,
    tags: list[str] | str | None = None,
    source_task: str = "",
    sensitivity: str = "private",
) -> dict[str, Any]:
    """Save a durable personal memory. Do not store raw passwords, API keys, or tokens; use sensitivity='secret_reference' for references to where secrets live."""
    require_token(api_token)
    return store.save_memory(
        type=type,
        title=title,
        content=content,
        tags=tags,
        source_task=source_task,
        sensitivity=sensitivity,
    )


@mcp.tool
def search_memory(
    query: str = "",
    api_token: str | None = None,
    type: str | None = None,
    tags: list[str] | str | None = None,
    sensitivity: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search saved memories by keyword, type, tag, and sensitivity."""
    require_token(api_token)
    return store.search_memories(
        query=query,
        type=type,
        tags=tags,
        sensitivity=sensitivity,
        limit=limit,
    )


@mcp.tool
def get_memory(id: str, api_token: str | None = None) -> dict[str, Any] | None:
    """Get a saved memory by id."""
    require_token(api_token)
    return store.get_memory(id)


@mcp.tool
def update_memory(
    id: str,
    api_token: str | None = None,
    title: str | None = None,
    content: str | None = None,
    type: str | None = None,
    tags: list[str] | str | None = None,
    source_task: str | None = None,
    sensitivity: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Update an existing memory. Use status='archived' instead of deleting ordinary records."""
    require_token(api_token)
    return store.update_memory(
        id=id,
        title=title,
        content=content,
        type=type,
        tags=tags,
        source_task=source_task,
        sensitivity=sensitivity,
        status=status,
    )


@mcp.tool
def list_recent_memories(limit: int = 10, api_token: str | None = None) -> list[dict[str, Any]]:
    """List the most recently created active memories."""
    require_token(api_token)
    return store.list_recent_memories(limit=limit)


@mcp.tool
def memory_stats(api_token: str | None = None) -> dict[str, Any]:
    """Return count and category statistics for the memory database."""
    require_token(api_token)
    return store.stats()


if __name__ == "__main__":
    host = os.environ.get("MEMORY_MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MEMORY_MCP_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port)
