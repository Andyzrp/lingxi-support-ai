#!/bin/bash

echo "======================================"
echo "  灵犀客服 - 中间件健康检测"
echo "======================================"

VM_HOST="10.99.216.94"
ALL_OK=true

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
fail() { echo -e "${RED}  ❌ $1${NC}"; ALL_OK=false; }
warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }

echo ""
echo "【Docker 容器状态】"

ssh root@$VM_HOST "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" 2>/dev/null
if [ $? -ne 0 ]; then
  fail "无法连接虚拟机 $VM_HOST，请检查 SSH"
  exit 1
fi

echo ""
echo "【PostgreSQL 连接检测】"

PG_CHECK=$(ssh root@$VM_HOST \
  "docker exec \$(docker ps -qf 'name=postgres') \
   psql -U lingxi -d lingxi_support -c 'SELECT COUNT(*) FROM admins;' 2>&1")

if echo "$PG_CHECK" | grep -q "count"; then
  ok "PostgreSQL 连接正常（lingxi_support 库可访问）"
else
  fail "PostgreSQL 连接失败：$PG_CHECK"
fi

echo ""
echo "【Redis 连接检测】"

REDIS_CHECK=$(ssh root@$VM_HOST \
  "docker exec \$(docker ps -qf 'name=redis') \
   redis-cli ping 2>&1")

if echo "$REDIS_CHECK" | grep -q "PONG"; then
  ok "Redis 连接正常"
else
  fail "Redis 连接失败：$REDIS_CHECK"
fi

echo ""
echo "【Qdrant 连接检测】"

QDRANT_CHECK=$(curl -s --max-time 5 \
  "http://$VM_HOST:6333/healthz" 2>&1)

if echo "$QDRANT_CHECK" | grep -q "ok"; then
  ok "Qdrant HTTP 健康检查正常（6333端口）"
else
  fail "Qdrant 连接失败：$QDRANT_CHECK"
fi

COLLECTION_CHECK=$(curl -s --max-time 5 \
  "http://$VM_HOST:6333/collections/knowledge_items" 2>&1)

if echo "$COLLECTION_CHECK" | grep -q "vectors_count"; then
  VECTOR_COUNT=$(echo $COLLECTION_CHECK | python3 -c \
    "import sys,json; d=json.load(sys.stdin); \
     print(d['result']['vectors_count'])" 2>/dev/null)
  ok "Qdrant knowledge_items 集合存在（向量数：${VECTOR_COUNT:-未知}）"
else
  warn "Qdrant knowledge_items 集合不存在，需要初始化"
fi

echo ""
echo "【Embedding 服务检测】"

EMBED_CHECK=$(curl -s --max-time 5 \
  "http://$VM_HOST:8001/health" 2>&1)

if echo "$EMBED_CHECK" | grep -qi "ok\|healthy\|running"; then
  ok "Embedding 服务正常（bge-small-zh-v1.5，8001端口）"
else
  fail "Embedding 服务异常：$EMBED_CHECK"
fi

echo ""
echo "【本地后端检测】"

BACKEND_CHECK=$(curl -s --max-time 5 \
  "http://localhost:8000/health" 2>&1)

if echo "$BACKEND_CHECK" | grep -qi "ok\|healthy"; then
  ok "FastAPI 后端正常（8000端口）"
else
  warn "FastAPI 后端未启动或无 /health 接口"
fi

echo ""
echo "======================================"
if $ALL_OK; then
  echo -e "${GREEN}  🎉 所有中间件检测通过！${NC}"
else
  echo -e "${RED}  ⚠️  存在异常，请查看上方红色提示！${NC}"
fi
echo "======================================"