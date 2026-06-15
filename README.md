# Manus Memory Agent Kit

> 我自己的链接 Obsidian 的数据库的 MCP，让所有的 Agent 都可以在我的云服务器上建立 Obsidian 的文档。

这个仓库用于把同一个 **Manus Memory** 数据库共享给其他 Manus 账号、其他 Agent 或支持 MCP 的 AI 产品。核心原则是：**MCP 服务是正式读写入口，Skill 是行为说明书**。其他 Agent 真正访问数据库时应连接 MCP endpoint，并使用独立的 Bearer Token；Skill 只负责告诉 Agent 何时保存、如何命名、如何检索，以及哪些内容不能保存。

> 安全边界：本仓库不包含真实 token、不包含 SQLite 数据库、不包含 `.env` 文件，也不包含任何用户记忆内容。真实密钥只能放在服务器 `.env`、目标 Agent 的私密连接器配置或环境变量中。

## 仓库结构

| 路径 | 用途 |
|---|---|
| `mcp-service/` | Manus Memory MCP 服务端代码，可部署到云电脑或其他服务器。 |
| `mcp-service/.env.example` | 环境变量模板。复制为 `.env` 后填写真实 `MEMORY_API_TOKEN`。 |
| `mcp-service/scripts/health_check_mcp.py` | MCP 健康检查脚本，用于验证工具发现、保存、检索、更新和统计。 |
| `mcp-service/scripts/memory_cli.py` | 本地维护级 CLI，只应由服务维护者使用，不作为外部 Agent 的常规入口。 |
| `skills/manus-memory/SKILL.md` | 给 Manus 或类 Manus Agent 阅读的使用规范。 |
| `docs/mcp-configuration.md` | 给其他 Agent 配置 MCP endpoint 和认证方式的详细说明。 |
| `docs/agent-onboarding.md` | 发给其他 Agent 的精简接入说明。 |

## 当前推荐架构

| 层级 | 角色 | 是否给其他 Agent |
|---|---|---|
| SQLite 数据库 | 最底层真实存储，默认路径为 `data/memory.db`。 | 不给，除非维护。 |
| MCP 服务 | 统一的远程读写接口，提供 `save_memory`、`search_memory` 等工具。 | 给，这是共享数据库的核心。 |
| Skill | 使用规范，告诉 Agent 什么时候保存、怎样保存、怎样避免泄露秘密。 | 可以给，建议和 MCP 配置一起给。 |

## 对其他 Agent 的最小交付物

给另一个 Agent 时，通常只需要提供以下四项信息。**不要把真实 token 写进 GitHub issue、聊天记录或普通文档**；应通过对方平台的 Secret、环境变量或私密连接器配置填写。

| 项目 | 示例 |
|---|---|
| MCP 服务地址 | `http://35.198.242.144:8765/mcp` |
| 认证方式 | `Authorization: Bearer <MEMORY_API_TOKEN>` |
| 必读文档 | `docs/mcp-configuration.md` 与 `skills/manus-memory/SKILL.md` |
| 主要工具 | `save_memory`、`search_memory`、`get_memory`、`update_memory`、`list_recent_memories`、`memory_stats` |

## 快速验证

在服务端或可访问 endpoint 的机器上，可以运行健康检查脚本。该脚本默认使用 `MEMORY_MCP_URL` 和 `MEMORY_API_TOKEN` 环境变量。

```bash
cd mcp-service
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入真实 MEMORY_API_TOKEN 和 MEMORY_MCP_URL
python scripts/health_check_mcp.py
```

如果目标 AI 产品支持 MCP Custom Connector，应优先在连接器层配置 Bearer Header，而不是把 token 作为每次工具调用参数传入。
