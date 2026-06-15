# 给其他 Agent 的 Manus Memory 接入说明

你将接入一个共享的 Manus Memory 数据库。请把它当作用户的长期记忆服务，只保存对未来任务有复用价值的偏好、流程、项目配置、决策记录和可回溯说明。

## 你需要配置的 MCP

| 项目 | 值 |
|---|---|
| MCP 名称 | `manus-memory` |
| Endpoint | `http://35.198.242.144:8765/mcp` |
| 认证方式 | `Authorization: Bearer <MEMORY_API_TOKEN>` |
| 说明 | `<MEMORY_API_TOKEN>` 由用户通过私密方式提供，不应写入普通对话或仓库。 |

## 必读规则

请阅读并遵守仓库中的 `skills/manus-memory/SKILL.md`。它定义了何时保存记忆、怎样检索、如何标记敏感级别，以及什么时候不能保存。

## 工具使用优先级

| 优先级 | 方式 | 说明 |
|---|---|---|
| 1 | MCP 连接器层 Bearer 认证 | 标准方式。Agent 只调用工具，不在工具参数里暴露 token。 |
| 2 | `api_token` 工具参数 | 仅当平台无法配置 MCP Header 时使用。 |
| 3 | 本地 CLI 或 SQLite | 仅限服务维护者，不给普通 Agent 使用。 |

## 常见操作

保存记忆时，优先调用 `save_memory`。记录内容应完整、可检索、可复用，并带上清晰标签。

```json
{
  "type": "preference",
  "title": "用户偏好示例",
  "content": "用户希望长期记忆保存优先通过 MCP 连接器，而不是依赖云电脑本地 CLI。",
  "tags": ["mcp", "memory", "preference"],
  "sensitivity": "private"
}
```

检索记忆时，优先使用短关键词调用 `search_memory`，必要时再用 `get_memory` 获取完整内容。

```json
{
  "query": "mcp memory",
  "limit": 5
}
```

更新或废弃记忆时，调用 `update_memory`，通常将旧记录状态改为 `archived`，不要直接删除底层数据库内容。

```json
{
  "id": "<memory-id>",
  "status": "archived"
}
```

## 禁止事项

不要保存明文密码、API Key、OAuth Token、私钥、恢复码或类似秘密。如果必须记住“某个密钥在哪里”，只保存路径或配置位置，并把 `sensitivity` 设为 `secret_reference`。

| 不应保存 | 可保存的替代表述 |
|---|---|
| `sk-...`、`ghp_...` 等真实 token | “OpenAI token 存在服务器 `.env` 中，变量名为 `OPENAI_API_KEY`。” |
| 账号密码 | “该服务需要用户本人登录，凭证不保存。” |
| 私钥内容 | “SSH 私钥位于用户指定的安全路径，Agent 不读取内容。” |

## 验证方式

接入后请执行一次临时保存、检索和归档。验证记录不应包含真实用户秘密。验证完成后，应使用 `update_memory` 将其状态改为 `archived`，避免污染长期记忆库。
