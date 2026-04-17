# Weather MCP Service

基于 **MCP（Model Context Protocol）** 协议的天气查询服务，通过 HTTP/SSE 方式对外提供实时天气和天气预报查询能力。支持 Qoder 等 LLM 平台以 MCP 协议集成调用。

天气数据来源于 **高德地图天气 API**。

## 功能

- **实时天气查询** - 输入城市名，返回温度、湿度、风向、风力等实时天气信息
- **天气预报查询** - 输入城市名，返回未来 3 天的天气预报
- **城市编码自动解析** - 通过高德地理编码 API 自动将城市名转换为编码，并使用内存字典缓存
- **SSE 流式通信** - 支持 MCP 客户端通过 SSE 建立持久连接

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    LLM 平台（Qoder 等）                   │
│                  通过 SSE 连接 MCP 端点                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/SSE
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  Nginx（Docker 容器）                      │
│              反向代理 + SSE 支持 (端口 80)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ proxy_pass
                       ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI + MCP Server（Docker 容器）           │
│                                                          │
│  GET  /          → 服务状态                                │
│  GET  /health    → 健康检查                                │
│  GET  /mcp       → SSE 连接端点（MCP 客户端连接入口）        │
│  POST /mcp/messages → MCP 消息处理                        │
│                                                          │
│  MCP Tools:                                              │
│    - query_weather(city)   → 实时天气                      │
│    - query_forecast(city)  → 天气预报（3天）                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
                       ▼
┌──────────────────────────────────────────────────────────┐
│                 高德地图 API                               │
│  - 地理编码 API（城市名 → 城市编码）                        │
│  - 天气查询 API（实况 + 预报）                              │
└──────────────────────────────────────────────────────────┘
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| MCP 框架 | FastMCP + mcp SDK |
| SSE 传输 | SseServerTransport (mcp.server.sse) |
| HTTP 客户端 | httpx（异步） |
| 配置管理 | Pydantic Settings |
| 天气 API | 高德地图 |
| 容器化 | Docker + Docker Compose |
| 反向代理 | Nginx |
| Python 版本 | 3.11 |

## 项目结构

```
MCPMap/
├── app/                          # 应用代码
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口，SSE 端点挂载，路由注册
│   ├── mcp_server.py             # MCP 工具定义（query_weather、query_forecast）
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # 配置管理，使用 Pydantic Settings 读取环境变量
│   └── services/
│       ├── __init__.py
│       └── weather.py            # 高德天气服务，城市编码缓存，天气查询/预报
├── docker/
│   └── nginx.conf                # Nginx 反向代理配置，SSE 支持（关闭缓冲）
├── scripts/
│   ├── deploy.sh                 # 一键部署脚本
│   └── ssl.sh                    # SSL 证书申请脚本（Let's Encrypt）
├── .env                          # 环境变量（不提交到 Git）
├── .env.example                  # 环境变量示例
├── Dockerfile                    # Docker 镜像构建（Python 3.11-slim）
├── docker-compose.yml            # 本地开发用 Docker Compose
├── docker-compose.prod.yml       # 生产环境 Docker Compose（含 Nginx）
└── requirements.txt              # Python 依赖
```

### 文件说明

| 文件 | 说明 |
|------|------|
| `app/main.py` | FastAPI 应用主入口。注册 `/mcp` SSE 连接端点和 `/mcp/messages` POST 消息处理路由，配置 CORS 中间件 |
| `app/mcp_server.py` | 使用 FastMCP 定义两个 MCP 工具：`query_weather`（实时天气）和 `query_forecast`（天气预报） |
| `app/core/config.py` | 基于 Pydantic Settings 的配置管理，支持 `.env` 文件和环境变量，使用 `lru_cache` 实现单例 |
| `app/services/weather.py` | 高德天气服务封装。包含城市编码查询（带内存字典缓存）、实时天气查询、天气预报查询及格式化输出 |
| `docker/nginx.conf` | Nginx 配置，反向代理到 FastAPI 服务，关键配置：`proxy_buffering off` 和 `proxy_cache off`（SSE 必需） |
| `Dockerfile` | 基于 `python:3.11-slim` 构建镜像，使用清华 pip 镜像源加速依赖安装 |
| `docker-compose.prod.yml` | 生产环境编排，包含 weather-mcp 服务和 nginx 反向代理两个容器 |
| `docker-compose.yml` | 本地开发用，仅启动 weather-mcp 服务，直接暴露 8000 端口 |
| `scripts/deploy.sh` | 一键部署脚本，自动停止旧服务、构建镜像、启动容器 |
| `scripts/ssl.sh` | Let's Encrypt SSL 证书申请脚本（可选） |
| `.env.example` | 环境变量模板，包含高德 API Key、应用配置、CORS 等 |
| `requirements.txt` | Python 依赖清单 |

## 部署指南

### 前提条件

- 一台 Linux 服务器（如阿里云 ECS）
- 已安装 Docker 和 Docker Compose Plugin
- 已申请 [高德地图 API Key](https://lbs.amap.com/)
- 域名已解析到服务器 IP

### 第一步：上传项目

在本地将项目打包并上传到服务器：

```bash
# 本地打包（PowerShell）
Compress-Archive -Path "app", "docker", "scripts", "requirements.txt", "Dockerfile", "docker-compose.prod.yml", ".env" -DestinationPath "mcp-weather.zip" -Force

# 上传到服务器（通过 XShell 的 rz 或 scp）
scp mcp-weather.zip root@your-server-ip:/opt/
```

### 第二步：解压项目

```bash
cd /opt
unzip -o mcp-weather.zip -d weather-mcp
cd weather-mcp
```

### 第三步：检查 Docker Compose

```bash
# 确认 docker compose 可用
docker compose version

# 如果未安装，执行：
yum install -y docker-compose-plugin
```

### 第四步：设置环境变量

```bash
export AMAP_API_KEY=你的高德API_Key
```

### 第五步：执行部署

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 第六步：验证服务

```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 测试健康检查
curl http://你的域名/health
# 预期返回: {"status":"healthy"}

# 测试根路径
curl http://你的域名/
# 预期返回: {"name":"Weather MCP Service","version":"1.0.0","status":"running","mcp_endpoint":"/mcp"}

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

### 第七步：在 Qoder 中连接 MCP

在 Qoder 中添加 MCP 服务：

- **类型**: SSE
- **URL**: `http://你的域名/mcp`

连接成功后即可使用 `query_weather` 和 `query_forecast` 工具查询天气。

## 本地开发

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 常用运维命令

```bash
# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看实时日志
docker compose -f docker-compose.prod.yml logs -f

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 停止服务
docker compose -f docker-compose.prod.yml down

# 重新构建并启动
docker compose -f docker-compose.prod.yml up --build -d
```
