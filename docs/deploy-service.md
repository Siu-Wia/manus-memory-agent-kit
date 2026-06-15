# 部署 Manus Memory MCP 服务

本文用于把 `mcp-service/` 部署到一台 Linux 服务器。对于其他 Agent 共享同一个数据库的场景，通常不需要每个 Agent 自己部署服务；它们只需要连接已有 endpoint。只有当你想迁移服务、复制服务或搭建新环境时，才需要阅读本文。

## 一、安装依赖

```bash
cd mcp-service
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 二、配置环境变量

复制环境变量模板，并生成一个足够长的随机 token。

```bash
cp .env.example .env
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

把生成的 token 写入 `.env`：

```env
MEMORY_API_TOKEN=replace-with-the-generated-token
MEMORY_MCP_HOST=0.0.0.0
MEMORY_MCP_PORT=8765
MEMORY_MCP_URL=http://127.0.0.1:8765/mcp
```

请确保 `.env` 权限足够严格：

```bash
chmod 600 .env
```

## 三、启动服务

开发或临时运行时，可以直接启动：

```bash
set -a
. ./.env
set +a
. .venv/bin/activate
python mcp_server.py
```

生产或长期运行时，建议用 systemd 托管服务。下面是一个模板，路径需要按实际部署目录调整。

```ini
[Unit]
Description=Manus Memory MCP Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/manus-memory/mcp-service
EnvironmentFile=/opt/manus-memory/mcp-service/.env
ExecStart=/opt/manus-memory/mcp-service/.venv/bin/python /opt/manus-memory/mcp-service/mcp_server.py
Restart=always
RestartSec=3
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
```

保存为 `/etc/systemd/system/manus-memory.service` 后运行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now manus-memory.service
sudo systemctl status manus-memory.service --no-pager
```

## 四、验证服务

如果服务运行在本机：

```bash
cd mcp-service
set -a
. ./.env
set +a
python scripts/health_check_mcp.py
```

如果验证远程 endpoint，请先设置 `MEMORY_MCP_URL`：

```bash
export MEMORY_MCP_URL=http://server-ip:8765/mcp
export MEMORY_API_TOKEN='<token-from-secret-store>'
python scripts/health_check_mcp.py
```

## 五、开放网络访问

只有在你确实需要让外部 Agent 访问时，才应开放服务端口。长期使用时建议通过 HTTPS 反向代理、VPN 或防火墙白名单限制访问。不要把 SQLite 数据库文件暴露给外部网络。
