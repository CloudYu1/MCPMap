#!/bin/bash

# SSL 证书申请脚本（使用 Let's Encrypt）

set -e

DOMAIN=${1:-your-domain.com}
EMAIL=${2:-your-email@example.com}

echo "=== 为 $DOMAIN 申请 SSL 证书 ==="

# 安装 certbot（如果未安装）
if ! command -v certbot &> /dev/null; then
    echo "安装 certbot..."
    apt-get update
    apt-get install -y certbot
fi

# 申请证书
certbot certonly --standalone -d $DOMAIN --agree-tos -m $EMAIL --non-interactive

# 复制证书到项目目录
mkdir -p docker/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem docker/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem docker/ssl/

echo "=== SSL 证书已保存到 docker/ssl/ ==="
echo "记得更新 docker/nginx.conf 中的 server_name 为: $DOMAIN"
