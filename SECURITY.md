# Security Notes

本仓库的目标是让多个 Agent 通过受控 MCP 接口共享同一个 Manus Memory 数据库。仓库中不应出现真实 token、数据库文件、用户记忆内容或 `.env` 文件。

## 不应提交的内容

| 类型 | 示例 | 处理方式 |
|---|---|---|
| MCP token | `MEMORY_API_TOKEN=...` | 只放在服务器 `.env` 或目标平台 Secret。 |
| SQLite 数据库 | `data/memory.db` | 只保留在服务器本地，默认被 `.gitignore` 排除。 |
| 明文密码或 API Key | `sk-...`、`ghp_...`、OAuth token | 不进入记忆，不进入仓库。 |
| 私钥与恢复码 | SSH private key、recovery codes | 不读取、不保存、不上传。 |

## 共享给外部 Agent 的推荐方式

外部 Agent 应只拿到 MCP endpoint、认证方式和 Skill 文档。真实 token 应通过私密渠道传递，并尽量使用该平台的 Secret 管理功能。

```text
Endpoint: http://35.198.242.144:8765/mcp
Header: Authorization: Bearer <MEMORY_API_TOKEN>
Skill: skills/manus-memory/SKILL.md
```

## 长期加固建议

当前服务已经支持 Bearer Token，但如果要长期给多个外部 Agent 使用，建议逐步增加以下能力。

| 加固项 | 目的 |
|---|---|
| HTTPS 反向代理 | 避免 HTTP 明文传输 token。 |
| 多 token 与权限分级 | 给不同 Agent 独立凭证，便于撤销和审计。 |
| IP 白名单或 VPN | 限制可访问 MCP endpoint 的来源。 |
| 审计日志 | 追踪哪个 Agent 保存、更新或归档了哪些记录。 |
| 定期 token 轮换 | 降低长期凭证泄露风险。 |
