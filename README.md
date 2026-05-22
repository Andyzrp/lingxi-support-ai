# 灵犀智能客服系统

基于 AI 的智能客服系统，支持 Bot + Agent 双层拦截机制，有效提升问题解决率。

## 项目简介

电商场景智能客服系统，通过 Bot（FAQ 知识库）+ Agent（大模型工作流）双层拦截，提升 AI 解决率。

**核心特性**

- 🚀 **Bot + Agent 双层拦截**：FAQ 知识库优先拦截，Agent 处理复杂问题
- 🔍 **混合检索**：BM25 + Embedding 混合检索，提升匹配精度
- 💬 **卡片式回复**：订单、物流、商品等信息以卡片形式展示
- 🔧 **工具调用**：支持订单查询、物流查询、退款申请等工具
- 📊 **数据报表**：会话统计、解决率趋势、满意度分析
- ⚙️ **后台管理**：知识库管理、Bot/Agent 配置、渠道管理等

## 技术架构

### 后端

- **框架**：FastAPI (Python 3.11+)
- **Agent 框架**：LangGraph
- **向量数据库**：Qdrant
- **关系数据库**：PostgreSQL 15
- **缓存/消息队列**：Redis 7
- **异步任务**：Celery
- **Embedding 模型**：bge-small-zh（私有化部署）

### 前端

- **框架**：Vue 3 + Composition API
- **UI 库**：Element Plus
- **状态管理**：Pinia
- **图表**：ECharts
- **构建工具**：Vite

### 部署

- **容器化**：Docker + Docker Compose
- **网关**：Nginx

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户端                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   商城前台    │  │   客服悬浮窗  │  │  独立客服页   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                          │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    FastAPI      │ │   WebSocket     │ │     静态资源     │
│    后端服务      │ │   实时对话       │ │     前端页面     │
│    :8000        │ │                 │ │     :3000       │
└────────┬────────┘ └────────┬────────┘ └─────────────────┘
         │                   │
         └───────────────────┼───────────────────────┐
                             │                       │
         ┌───────────────────┼───────────────────────┤
         │                   │                       │
         ▼                   ▼                       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Redis     │    │ PostgreSQL  │    │   Qdrant    │    │   Celery    │
│  缓存/消息   │    │   关系数据   │    │  向量数据    │    │  异步任务   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 快速开始

### 环境要求

- Docker Desktop 4.0+
- Python 3.11+ (开发模式)
- Node.js 18+ (开发模式)

### Docker 部署（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd lingxi-support-ai

# 启动所有服务
docker-compose up -d

# 初始化数据库
docker-compose exec backend alembic upgrade head

# 访问页面
open http://localhost
```

### 开发模式

**后端**

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 填写必要的配置

# 启动服务
uvicorn app.main:app --reload --port 8000
```

**前端**

```bash
cd frontend

# 安装依赖
npm install

# 启动服务
npm run dev
```

**启动 Celery Worker（异步任务）**

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

**启动 Celery Beat（定时任务调度器）**

```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 3000 | 前端开发服务器 |
| backend | 8000 | 后端 API 服务 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存/消息队列 |
| qdrant | 6333/6334 | Qdrant 向量数据库 |
| nginx | 80 | 反向代理（生产环境） |

## 访问地址

- 前端页面：http://localhost:3000（开发）
- 后端 API：http://localhost:8000/api/v1
- Qdrant 控制台：http://localhost:6333/dashboard

## 默认账号

- 后台管理：admin / admin123
- 商城前台：用户名密码自行注册

## 项目结构

```
lingxi-support-ai/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── agent/         # Agent 工作流
│   │   ├── crud/          # 数据库操作
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── services/      # 业务逻辑
│   │   └── tasks/         # Celery 异步任务
│   ├── alembic/           # 数据库迁移
│   └── main.py            # 应用入口
├── frontend/
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── components/    # 公共组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面视图
│   │   └── router/        # 路由配置
│   └── package.json
├── encoder/               # Embedding 编码服务（可选）
├── nginx/                 # Nginx 配置
├── sql/                   # SQL 脚本
├── docker-compose.yml     # Docker 编排
└── requirements.txt       # Python 依赖
```

## 功能模块

### 1. 商城前台

- 用户注册/登录
- 商品列表/详情
- 模拟下单
- 订单查询
- 客服入口

### 2. 智能客服对话

- **Bot 层**：FAQ 知识库 + 关键词干预
- **Agent 层**：意图识别 → 情绪检测 → RAG → 工具调用 → 大模型生成
- **身份切换**：机器人 → 人工客服
- **卡片展示**：订单/物流/商品等信息卡片

### 3. 后台管理

- **知识库管理**：知识条目增删改查、Excel 批量导入
- **Bot 管理**：关键词干预配置、匹配阈值
- **Agent 管理**：系统 Prompt、模型参数、工具调用配置
- **渠道管理**：测试/正式渠道配置
- **会话管理**：实时监控、历史记录
- **数据报表**：会话量、解决率、满意度

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f celery

# 重启服务
docker-compose restart

# 停止所有服务（保留数据）
docker-compose down

# 停止并清除所有数据
docker-compose down -v
```

## License

MIT License
