#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from store import MemoryStore  # noqa: E402


def print_json(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local CLI for the Manus Memory database")
    sub = parser.add_subparsers(dest="command", required=True)

    save = sub.add_parser("save", help="Save a memory")
    save.add_argument("--type", default="note")
    save.add_argument("--title", required=True)
    save.add_argument("--content", required=True)
    save.add_argument("--tags", default="")
    save.add_argument("--source-task", default="")
    save.add_argument("--sensitivity", default="private", choices=["public", "private", "secret_reference"])

    search = sub.add_parser("search", help="Search memories")
    search.add_argument("--query", default="")
    search.add_argument("--type", default=None)
    search.add_argument("--tags", default="")
    search.add_argument("--sensitivity", default=None)
    search.add_argument("--limit", type=int, default=20)

    get = sub.add_parser("get", help="Get a memory by id")
    get.add_argument("id")

    recent = sub.add_parser("recent", help="List recent memories")
    recent.add_argument("--limit", type=int, default=10)

    update = sub.add_parser("update", help="Update a memory")
    update.add_argument("id")
    update.add_argument("--title")
    update.add_argument("--content")
    update.add_argument("--type")
    update.add_argument("--tags")
    update.add_argument("--source-task")
    update.add_argument("--sensitivity", choices=["public", "private", "secret_reference"])
    update.add_argument("--status", choices=["active", "archived"])

    sub.add_parser("stats", help="Show database stats")

    args = parser.parse_args()
    store = MemoryStore()

    if args.command == "save":
        print_json(store.save_memory(args.type, args.title, args.content, args.tags, args.source_task, args.sensitivity))
    elif args.command == "search":
        print_json(store.search_memories(args.query, args.type, args.tags, args.sensitivity, limit=args.limit))
    elif args.command == "get":
        print_json(store.get_memory(args.id))
    elif args.command == "recent":
        print_json(store.list_recent_memories(args.limit))
    elif args.command == "update":
        kwargs = {k: v for k, v in {
            "title": args.title,
            "content": args.content,
            "type": args.type,
            "tags": args.tags,
            "source_task": args.source_task,
            "sensitivity": args.sensitivity,
            "status": args.status,
        }.items() if v is not None}
        print_json(store.update_memory(args.id, **kwargs))
    elif args.command == "stats":
        print_json(store.stats())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
