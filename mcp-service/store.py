from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "memory.db"
VALID_SENSITIVITY = {"public", "private", "secret_reference"}
VALID_STATUS = {"active", "archived"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_tags(tags: list[str] | str | None) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        raw = [part.strip() for part in tags.replace("，", ",").split(",")]
    else:
        raw = [str(part).strip() for part in tags]
    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not item:
            continue
        tag = item.lower().replace(" ", "-")
        if tag not in seen:
            result.append(tag)
            seen.add(tag)
    return result


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = json.loads(item.get("tags") or "[]")
    return item


class MemoryStore:
    def __init__(self, db_path: str | os.PathLike[str] | None = None) -> None:
        self.db_path = Path(db_path or os.environ.get("MEMORY_DB_PATH") or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    source_task TEXT NOT NULL DEFAULT '',
                    sensitivity TEXT NOT NULL DEFAULT 'private',
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
                CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
                CREATE INDEX IF NOT EXISTS idx_memories_sensitivity ON memories(sensitivity);
                CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
                CREATE INDEX IF NOT EXISTS idx_memories_updated_at ON memories(updated_at);
                """
            )

    def save_memory(
        self,
        type: str,
        title: str,
        content: str,
        tags: list[str] | str | None = None,
        source_task: str = "",
        sensitivity: str = "private",
    ) -> dict[str, Any]:
        type = (type or "note").strip().lower().replace(" ", "_")
        title = (title or "").strip()
        content = (content or "").strip()
        source_task = (source_task or "").strip()
        sensitivity = (sensitivity or "private").strip()
        if not title:
            raise ValueError("title is required")
        if not content:
            raise ValueError("content is required")
        if sensitivity not in VALID_SENSITIVITY:
            raise ValueError(f"sensitivity must be one of {sorted(VALID_SENSITIVITY)}")
        now = utc_now()
        item = {
            "id": str(uuid.uuid4()),
            "type": type,
            "title": title,
            "content": content,
            "tags": normalize_tags(tags),
            "source_task": source_task,
            "sensitivity": sensitivity,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (id, type, title, content, tags, source_task, sensitivity, status, created_at, updated_at)
                VALUES (:id, :type, :title, :content, :tags, :source_task, :sensitivity, :status, :created_at, :updated_at)
                """,
                {**item, "tags": json.dumps(item["tags"], ensure_ascii=False)},
            )
        return item

    def get_memory(self, id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (id,)).fetchone()
        return row_to_dict(row) if row else None

    def update_memory(
        self,
        id: str,
        title: str | None = None,
        content: str | None = None,
        type: str | None = None,
        tags: list[str] | str | None = None,
        source_task: str | None = None,
        sensitivity: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_memory(id)
        if not current:
            raise ValueError("memory not found")
        updates: dict[str, Any] = {}
        if title is not None:
            value = title.strip()
            if not value:
                raise ValueError("title cannot be empty")
            updates["title"] = value
        if content is not None:
            value = content.strip()
            if not value:
                raise ValueError("content cannot be empty")
            updates["content"] = value
        if type is not None:
            updates["type"] = type.strip().lower().replace(" ", "_") or "note"
        if tags is not None:
            updates["tags"] = json.dumps(normalize_tags(tags), ensure_ascii=False)
        if source_task is not None:
            updates["source_task"] = source_task.strip()
        if sensitivity is not None:
            if sensitivity not in VALID_SENSITIVITY:
                raise ValueError(f"sensitivity must be one of {sorted(VALID_SENSITIVITY)}")
            updates["sensitivity"] = sensitivity
        if status is not None:
            if status not in VALID_STATUS:
                raise ValueError(f"status must be one of {sorted(VALID_STATUS)}")
            updates["status"] = status
        if not updates:
            return current
        updates["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = :{key}" for key in updates)
        with self.connect() as conn:
            conn.execute(f"UPDATE memories SET {assignments} WHERE id = :id", {**updates, "id": id})
        updated = self.get_memory(id)
        if not updated:
            raise ValueError("memory not found after update")
        return updated

    def search_memories(
        self,
        query: str = "",
        type: str | None = None,
        tags: list[str] | str | None = None,
        sensitivity: str | None = None,
        status: str = "active",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit or 20), 100))
        clauses = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if type:
            clauses.append("type = ?")
            params.append(type.strip().lower().replace(" ", "_"))
        if sensitivity:
            clauses.append("sensitivity = ?")
            params.append(sensitivity)
        q = (query or "").strip()
        if q:
            like = f"%{q}%"
            clauses.append("(title LIKE ? OR content LIKE ? OR source_task LIKE ? OR tags LIKE ?)")
            params.extend([like, like, like, like])
        for tag in normalize_tags(tags):
            clauses.append("tags LIKE ?")
            params.append(f'%"{tag}"%')
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM memories {where} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(row) for row in rows]

    def list_recent_memories(self, limit: int = 10, status: str = "active") -> list[dict[str, Any]]:
        limit = max(1, min(int(limit or 10), 100))
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return [row_to_dict(row) for row in rows]

    def stats(self) -> dict[str, Any]:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM memories").fetchone()["n"]
            by_type = [dict(row) for row in conn.execute("SELECT type, COUNT(*) AS n FROM memories GROUP BY type ORDER BY n DESC")]
            by_status = [dict(row) for row in conn.execute("SELECT status, COUNT(*) AS n FROM memories GROUP BY status ORDER BY n DESC")]
        return {"total": total, "by_type": by_type, "by_status": by_status, "db_path": str(self.db_path)}
