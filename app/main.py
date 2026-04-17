"""
FastAPI 应用主入口
提供 HTTP 接口和 MCP SSE 端点
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from app.core.config import get_settings
from app.mcp_server import mcp

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== MCP SSE 传输配置 ======================
sse_transport = SseServerTransport("/mcp/messages")

@app.get("/mcp")
async def handle_mcp_connection(request: Request):
    """处理 MCP SSE 连接"""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options(),
        )

# handle_post_message 是 ASGI 应用，需要用 Mount 挂载而不是 add_route
app.router.routes.append(
    Mount("/mcp/messages", app=sse_transport.handle_post_message)
)
# ====================================================================

@app.get("/")
async def root():
    """根路径 - 服务状态检查"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "mcp_endpoint": "/mcp"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )