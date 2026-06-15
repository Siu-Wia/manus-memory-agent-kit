#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import Client

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
ENDPOINT = os.environ.get("MEMORY_MCP_URL", "http://127.0.0.1:8765/mcp")


def load_env(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing env file: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


async def main() -> None:
    load_env(ENV_PATH)
    token = os.environ.get("MEMORY_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("MEMORY_API_TOKEN is empty")

    report: dict[str, object] = {
        "endpoint": ENDPOINT,
        "checks": [],
    }

    async with Client(ENDPOINT) as client:
        tools = await client.list_tools()
        tool_names = sorted(getattr(t, "name", str(t)) for t in tools)
        required = {
            "save_memory",
            "search_memory",
            "get_memory",
            "update_memory",
            "list_recent_memories",
            "memory_stats",
        }
        missing = sorted(required - set(tool_names))
        report["tool_names"] = tool_names
        report["missing_tools"] = missing
        if missing:
            raise RuntimeError(f"missing tools: {missing}")
        report["checks"].append("tool_list_ok")

        invalid_token_failed = False
        try:
            await client.call_tool("memory_stats", {"api_token": "invalid-token-for-health-check"})
        except Exception:
            invalid_token_failed = True
        report["invalid_token_rejected"] = invalid_token_failed
        if not invalid_token_failed:
            raise RuntimeError("invalid token was not rejected")
        report["checks"].append("auth_rejects_invalid_token")

        stats_before = await client.call_tool("memory_stats", {"api_token": token})
        report["stats_before_type"] = type(stats_before).__name__
        report["checks"].append("stats_ok")

        now = datetime.now(timezone.utc).isoformat()
        saved = await client.call_tool(
            "save_memory",
            {
                "api_token": token,
                "type": "test",
                "title": "MCP 健康检查临时记录",
                "content": f"这是一条由健康检查脚本写入的临时记录，时间：{now}。",
                "tags": ["manus-memory", "health-check"],
                "source_task": "MCP 健康检查",
                "sensitivity": "private",
            },
        )
        saved_data = saved.data if hasattr(saved, "data") else saved
        memory_id = saved_data["id"] if isinstance(saved_data, dict) else None
        if not memory_id:
            raise RuntimeError(f"save did not return id: {saved!r}")
        report["saved_id"] = memory_id
        report["checks"].append("save_ok")

        found = await client.call_tool(
            "search_memory",
            {"api_token": token, "query": "健康检查临时记录", "limit": 5},
        )
        found_data = found.data if hasattr(found, "data") else found
        found_ids = [item.get("id") for item in found_data] if isinstance(found_data, list) else []
        report["search_found_saved"] = memory_id in found_ids
        if memory_id not in found_ids:
            raise RuntimeError("saved memory not found by search")
        report["checks"].append("search_ok")

        got = await client.call_tool("get_memory", {"api_token": token, "id": memory_id})
        got_data = got.data if hasattr(got, "data") else got
        if not isinstance(got_data, dict) or got_data.get("id") != memory_id:
            raise RuntimeError("get_memory returned unexpected result")
        report["checks"].append("get_ok")

        updated = await client.call_tool(
            "update_memory",
            {
                "api_token": token,
                "id": memory_id,
                "status": "archived",
                "content": f"健康检查已完成，此临时记录已归档。时间：{now}。",
            },
        )
        updated_data = updated.data if hasattr(updated, "data") else updated
        report["updated_status"] = updated_data.get("status") if isinstance(updated_data, dict) else None
        if report["updated_status"] != "archived":
            raise RuntimeError("update_memory did not archive the temporary record")
        report["checks"].append("update_ok")

        recent = await client.call_tool("list_recent_memories", {"api_token": token, "limit": 3})
        recent_data = recent.data if hasattr(recent, "data") else recent
        if not isinstance(recent_data, list):
            raise RuntimeError("list_recent_memories did not return a list")
        report["recent_count"] = len(recent_data)
        report["checks"].append("recent_ok")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
