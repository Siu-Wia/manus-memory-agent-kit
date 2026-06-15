# Manus Memory MCP 服务地址与认证配置说明

本文说明如何把其他 Manus 账号、其他 Agent 或支持 MCP 的 AI 产品接入同一个 Manus Memory 数据库。最重要的原则是：**MCP endpoint 是数据库共享入口，Bearer Token 是访问凭证，Skill 是使用规范**。

## 一、需要给其他 Agent 的信息

你给其他 Agent 时，通常提供下面这几类信息即可。真实 token 不应写入仓库、普通文档或聊天记录，而应放进目标平台的 Secret、环境变量或私密连接器配置。

| 配置项 | 当前部署值或填写方式 | 说明 |
|---|---|---|
| MCP 服务地址 | `http://35.198.242.144:8765/mcp` | 当前云电脑上的 Manus Memory MCP endpoint。 |
| 认证 Header 名称 | `Authorization` | 标准 HTTP Authorization 请求头。 |
| 认证 Header 值 | `Bearer <MEMORY_API_TOKEN>` | `<MEMORY_API_TOKEN>` 替换为服务器 `.env` 中的真实 token。 |
| 推荐 Skill | `skills/manus-memory/SKILL.md` | 让 Agent 学会何时保存、如何检索、如何避免保存敏感明文。 |
| 备用方式 | 工具参数 `api_token` | 仅在连接器层无法设置 Header 时使用。 |

## 二、Manus Custom MCP 推荐配置

如果是另一个 Manus 账号接入，推荐在 Manus 的连接器设置里添加一个 Custom MCP。字段名称可能因界面版本不同略有差异，但含义应保持一致。

| 字段 | 建议值 |
|---|---|
| Connector 类型 | Custom MCP |
| 名称 | `manus-memory` |
| Transport | HTTP / Streamable HTTP，按界面支持项选择 |
| URL / Endpoint | `http://35.198.242.144:8765/mcp` |
| Header | `Authorization: Bearer <MEMORY_API_TOKEN>` |
| 是否启用 | 启用 |

配置好以后，目标 Agent 不需要知道云电脑文件系统路径，也不需要访问 SQLite 数据库。它只需要通过 MCP 工具调用即可保存和检索记忆。

## 三、通用 MCP 客户端配置范式

不同 AI 产品的 MCP 配置格式不同。只要它支持 HTTP MCP endpoint 和自定义请求头，就可以按下面的逻辑配置。

```json
{
  "servers": {
    "manus-memory": {
      "type": "http",
      "url": "http://35.198.242.144:8765/mcp",
      "headers": {
        "Authorization": "Bearer ${MEMORY_API_TOKEN}"
      }
    }
  }
}
```

如果目标产品不支持在 MCP 连接器层设置请求头，但允许调用工具时传参，可以临时使用兼容参数：

```json
{
  "type": "workflow",
  "title": "示例记忆",
  "content": "这是一条通过 MCP 工具参数认证保存的示例。",
  "tags": ["example"],
  "sensitivity": "private",
  "api_token": "<MEMORY_API_TOKEN>"
}
```

不过这种方式不如连接器层 Header 安全，因为 token 会进入每次工具调用参数。长期使用时应优先让平台支持 Secret 或 Header 注入。

## 四、服务端认证逻辑

当前 MCP 服务端支持两种认证方式，优先级如下。

| 优先级 | 方式 | 使用场景 |
|---|---|---|
| 1 | 连接器层 `Authorization: Bearer <token>` | 推荐给其他 Agent 的标准方式。 |
| 2 | 工具参数 `api_token` | 兼容旧客户端，或目标平台暂不支持 Header 时使用。 |

服务端会把传入 token 与服务器环境变量 `MEMORY_API_TOKEN` 做常量时间比较。真实 token 保存在云电脑的 `/home/ubuntu/manus-memory/.env` 中，该文件不应提交到 GitHub。

## 五、可用工具说明

| 工具 | 用途 | 常用参数 |
|---|---|---|
| `save_memory` | 保存一条长期记忆。 | `type`、`title`、`content`、`tags`、`source_task`、`sensitivity` |
| `search_memory` | 按关键词、类型、标签或敏感级别检索。 | `query`、`type`、`tags`、`sensitivity`、`limit` |
| `get_memory` | 按 ID 读取完整记录。 | `id` |
| `update_memory` | 更新标题、内容、标签、状态等字段。 | `id`、`title`、`content`、`status` |
| `list_recent_memories` | 查看最近活跃记忆。 | `limit` |
| `memory_stats` | 查看记忆库统计。 | 无必填参数 |

## 六、给其他 Agent 的推荐使用规范

接入 MCP 后，建议把 `skills/manus-memory/SKILL.md` 也给目标 Agent。这个 Skill 的核心规则是：普通保存与检索**优先通过 MCP 连接器**，不要直接写 SQLite，不要默认使用云电脑 CLI。

| 场景 | 推荐行为 |
|---|---|
| 用户说“记一下”“保存这个”“以后按这个来” | 调用 `save_memory`。 |
| 用户问“之前怎么做的”“上次配置是什么” | 调用 `search_memory`，必要时再 `get_memory`。 |
| 发现旧记录过时 | 调用 `update_memory`，一般把旧记录标为 `archived`，不要物理删除。 |
| 涉及密码、API Key、OAuth Token | 不保存明文，只保存“密钥在哪里配置”的引用，并设为 `secret_reference`。 |

## 七、安全建议

当前 endpoint 使用 HTTP 暴露在公网 IP 上，访问控制依赖 Bearer Token。对于更长期或更广泛的共享，建议逐步升级为 HTTPS、私有网络或防火墙白名单。至少应为不同外部 Agent 准备不同 token，便于将来单独撤销权限。

| 风险 | 建议 |
|---|---|
| token 泄露 | 立即轮换 `MEMORY_API_TOKEN`，并重启 MCP 服务。 |
| 多个 Agent 共用同一 token | 改成每个 Agent 单独 token，或在服务端增加多 token 支持。 |
| HTTP 明文传输 | 加反向代理 HTTPS，或改用 VPN/Tailscale/内网访问。 |
| Agent 误存敏感明文 | 使用 Skill 约束，并定期检索 `sensitivity='secret_reference'` 与高风险关键词。 |

## 八、配置后验证

连接器配置完成后，可以让目标 Agent 执行一次无敏感内容的测试保存，再立刻检索并归档。

```json
{
  "type": "workflow",
  "title": "MCP 接入验证",
  "content": "这是一条临时验证记录，确认 Agent 可以通过 MCP 写入和检索 Manus Memory。",
  "tags": ["mcp", "validation"],
  "sensitivity": "private"
}
```

验证成功后，使用 `update_memory` 将该记录状态改为 `archived`。这样可以确认写入链路正常，同时避免测试数据污染长期记忆。
