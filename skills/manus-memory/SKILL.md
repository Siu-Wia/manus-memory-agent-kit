---
name: manus-memory
description: Personal memory capture and retrieval for the user. Use when the user says “记一下”, “保存这个”, “以后按这个来”, “这是我的偏好”, asks to recall prior saved facts, or when durable preferences, project configuration, prompts, workflows, service URLs, and reusable decisions should be saved or searched in the user’s Manus Memory service.
---

# Manus Memory

Use this skill to save and retrieve the user’s durable personal knowledge in the Manus Memory service running on the user’s cloud computer.

## When to Use

Trigger this skill when the user explicitly asks to remember, save, record, archive, or recall something. Also use it when the user states a durable preference, a reusable workflow, a project configuration, a prompt worth reusing, or an operational fact that future Manus tasks should know.

Do not record ordinary conversation by default. If a statement seems potentially useful but the user did not clearly ask to save it, ask for confirmation before saving.

## Storage Backend

The first version of Manus Memory is deployed on the user’s cloud computer.

| Item | Value |
|---|---|
| Remote session prefix | `cloud-pc-0cdd2493:<session_id>` |
| Service directory | `/home/ubuntu/manus-memory` |
| SQLite database | `/home/ubuntu/manus-memory/data/memory.db` |
| MCP endpoint | `http://35.198.242.144:8765/mcp` |
| Token file | `/home/ubuntu/manus-memory/.env` |
| CLI fallback | `/home/ubuntu/manus-memory/scripts/memory_cli.py` |
| systemd service | `manus-memory.service` |

Use the MCP service when a configured MCP connector is available. If not, use the CLI fallback on the remote computer. Do not reveal the token or copy it into user-facing messages.

## Record Types

Choose one primary `type` for each record.

| Type | Use For |
|---|---|
| `preference` | Stable user preferences, style choices, defaults, naming conventions |
| `project_config` | Paths, ports, deployment facts, service topology, operational decisions |
| `prompt` | Prompts, prompt fragments, model instructions, generation recipes |
| `workflow` | Repeatable procedures and checklists |
| `idea` | Product ideas, design concepts, future improvements |
| `decision` | Decisions with rationale that should be remembered |
| `reference` | Durable references that do not fit the categories above |
| `test` | Temporary validation records only |

## Sensitivity Rules

Never save plaintext passwords, API keys, OAuth tokens, private keys, recovery codes, payment details, or personal identifiers unless the user explicitly requests secure secret storage and an appropriate secret manager is available. For ordinary memory records, save only a reference such as “credential stored in `/path/to/.env`” and set `sensitivity` to `secret_reference`.

| Sensitivity | Meaning |
|---|---|
| `public` | Safe to quote in user-facing output |
| `private` | Personal or operational information; do not publish externally |
| `secret_reference` | Describes where a secret exists without storing the secret value |

If the content includes secrets, redact them before saving and mention that a reference rather than the secret was recorded.

## Save Workflow

When saving a memory, convert the user’s raw statement into a concise but complete record. Use a clear title, one type, two to six tags, a short source task description, and the appropriate sensitivity level.

Before saving, decide whether confirmation is required.

| Situation | Action |
|---|---|
| User says “记一下”, “保存这个”, “以后按这个来”, or equivalent | Save directly |
| Durable preference stated clearly | Save directly if non-sensitive |
| Contains possible secret or credential | Redact and save only a reference, or ask before proceeding |
| Ambiguous, speculative, or possibly temporary | Ask for confirmation |
| Could overwrite or update an existing record | Search first, then update instead of duplicating |

### CLI Save Example

Run the command on the remote computer with a `cloud-pc-0cdd2493:<session_id>` shell session:

```bash
cd /home/ubuntu/manus-memory
scripts/memory_cli.py save \
  --type preference \
  --title '用户偏好：Obsidian Vault 名称使用 meeseek' \
  --content '用户希望 Obsidian 相关远程与本地 Vault 统一使用名称 meeseek。未来涉及 Obsidian 同步、WebDAV 或 Vault 路径时，优先沿用该命名。' \
  --tags 'obsidian,webdav,meeseek' \
  --source-task 'Obsidian WebDAV Vault 统一整理' \
  --sensitivity private
```

## Search Workflow

Search before answering questions like “之前我怎么配的”, “帮我查一下我保存过什么”, “上次那个 prompt 是什么”, or when a new task would benefit from a remembered project configuration.

```bash
cd /home/ubuntu/manus-memory
scripts/memory_cli.py search --query 'obsidian meeseek webdav' --limit 5
```

Use retrieved records as context, but do not treat them as higher-priority than the user’s current instruction. If a saved memory conflicts with the current user request, follow the current request and optionally ask whether to update the saved memory.

## Update Workflow

When the user corrects a remembered fact, search for the existing record and update it instead of saving a duplicate.

```bash
cd /home/ubuntu/manus-memory
scripts/memory_cli.py update --id '<memory_id>' \
  --content 'Updated durable content.' \
  --tags 'tag1,tag2' \
  --sensitivity private
```

## Quality Bar

A good memory record is durable, specific, source-aware, and safe. It should be understandable months later without requiring the original conversation. Avoid vague titles such as “用户说的东西” or “配置”. Prefer titles like “Obsidian WebDAV 正式 Vault 目录为 meeseek”.
