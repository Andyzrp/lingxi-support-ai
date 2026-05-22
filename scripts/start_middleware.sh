#!/bin/bash

echo "======================================"
echo "  灵犀客服 - 中间件启动脚本"
echo "======================================"

VM_HOST="10.99.216.94"

ssh root@$VM_HOST << 'REMOTE_SCRIPT'

echo ""
echo "【查看当前容器状态】"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "【启动/重启所有中间件】"

POSTGRES_ID=$(docker ps -aqf "name=postgres")
if [ -n "$POSTGRES_ID" ]; then
  docker start $POSTGRES_ID 2>/dev/null || true
  echo "  ✅ PostgreSQL 已启动"
else
  echo "  ⚠️  PostgreSQL 容器不存在，尝试 docker-compose 启动..."
  cd /opt/middleware && docker-compose up -d postgres 2>/dev/null || \
  docker run -d \
    --name postgres15 \
    --restart unless-stopped \
    -e POSTGRES_USER=lingxi \
    -e POSTGRES_PASSWORD=lingxi123456 \
    -e POSTGRES_DB=lingxi_support \
    -p 5432:5432 \
    -v pgdata:/var/lib/postgresql/data \
    postgres:15-alpine
  echo "  ✅ PostgreSQL 已创建并启动"
fi

REDIS_ID=$(docker ps -aqf "name=redis")
if [ -n "$REDIS_ID" ]; then
  docker start $REDIS_ID 2>/dev/null || true
  echo "  ✅ Redis 已启动"
else
  echo "  ⚠️  Redis 容器不存在，创建中..."
  docker run -d \
    --name redis7 \
    --restart unless-stopped \
    -p 6379:6379 \
    -v redisdata:/data \
    redis:7-alpine \
    redis-server --appendonly yes
  echo "  ✅ Redis 已创建并启动"
fi

QDRANT_ID=$(docker ps -aqf "name=qdrant")
if [ -n "$QDRANT_ID" ]; then
  docker start $QDRANT_ID 2>/dev/null || true
  echo "  ✅ Qdrant 已启动"
else
  echo "  ⚠️  Qdrant 容器不存在，创建中..."
  docker run -d \
    --name qdrant \
    --restart unless-stopped \
    -p 6333:6333 \
    -p 6334:6334 \
    -v qdrantdata:/qdrant/storage \
    qdrant/qdrant
  echo "  ✅ Qdrant 已创建并启动"
fi

EMBED_ID=$(docker ps -aqf "name=embedding")
if [ -n "$EMBED_ID" ]; then
  docker start $EMBED_ID 2>/dev/null || true
  echo "  ✅ Embedding 服务已启动"
else
  echo "  ⚠️  Embedding 容器不存在，请手动启动 encoder 目录"
fi

echo ""
echo "【等待服务就绪（15秒）】"
sleep 15

echo ""
echo "【最终容器状态】"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

REMOTE_SCRIPT

echo ""
echo "======================================"
echo "  中间件启动完成，运行 check_services.sh 验证"
echo "======================================"