#!/bin/bash

# MCP 天气服务部署脚本

set -e

echo "=== 开始部署 Weather MCP 服务 ==="

# 检查环境变量
if [ -z "$AMAP_API_KEY" ]; then
    echo "错误: 请设置 AMAP_API_KEY 环境变量"
    exit 1
fi

# 创建必要目录
mkdir -p docker/logs

# 停止旧服务
echo "停止旧服务..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# 构建并启动
echo "构建并启动服务..."
docker compose -f docker-compose.prod.yml up --build -d

# 检查状态
echo "检查服务状态..."
sleep 3
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== 部署完成 ==="
echo "服务地址: http://www.jcjyhf.online"
echo "MCP 端点: http://www.jcjyhf.online/mcp"
echo ""
echo "查看日志: docker compose -f docker-compose.prod.yml logs -f"
