我来输出完整的项目需求和设计文档，使用Markdown格式，结构清晰便于其他模型理解：

```markdown
# 智能客服系统 - 完整需求与设计文档

## 文档说明
- 版本：v1.0
- 技术栈：Python + Vue3
- 部署方式：私有化部署
- 开发方式：一人独立开发
- 目标：电商场景智能客服，通过Bot+Agent双层拦截提升AI解决率

---

# 一、项目概述

## 1.1 背景
- 业务场景：电商
- 日峰值会话量：3万+
- 当前AI解决率：40%
- 目标：通过Bot+Agent双层拦截机制显著提升解决率

## 1.2 系统模块
系统分为三大模块：
1. 简易电商前台（Mock商城）
2. 智能客服对话系统（Bot+Agent双层拦截）
3. 后台管理平台

---

# 二、模块一：简易电商前台

## 2.1 功能列表
- 用户注册/登录（用户名+密码）
- 个人中心
- 商品列表页
- 商品详情页
- 模拟下单（生成真实订单数据）
- 订单查询

## 2.2 数据来源
- 商品数据：管理员在后台录入
- 订单数据：用户在前台模拟下单生成

## 2.3 客服入口
- 页面右下角悬浮客服按钮
- 点击进入独立对话页面
- 进入对话时自动携带用户信息：
  - 用户ID
  - 登录状态
  - 最近订单信息
  - 当前页面信息

---

# 三、模块二：智能客服对话系统

## 3.1 整体对话流程

```
用户发送消息
    ↓
第一层：Bot（FAQ知识库拦截）
├── 关键词干预（最高优先级）
├── 标准问答（BM25+Embedding混合检索）
└── 匹配不上 → 进入第二层
    ↓
第二层：Agent（大模型工作流拦截）
├── 意图识别
├── 情绪检测
├── 工具调用
├── 大模型生成回答
└── 答不上 → 提示转人工
    ↓
兜底：转人工（模拟）
└── 身份切换为人工客服（仍是AI回答，换人设和Prompt）
```

## 3.2 Bot层

### 3.2.1 技能列表（按优先级）

#### 第一优先级：关键词干预
- 关键词由运营在后台维护
- 匹配方式：精确匹配 或 包含匹配
- 触发动作（可多选组合）：
  - 返回固定话术
  - 推荐相关FAQ列表
  - 自动转人工

#### 第二优先级：标准问答
- 检索方式：BM25 + Embedding混合检索
  - BM25权重：0.3
  - 向量相似度权重：0.7
- Embedding模型：bge-small-zh（私有化部署）
- 向量数据库：Qdrant
- 匹配对象：标准问题 + 所有相似问法全部向量化
- 相似度阈值：可配置，默认0.85
- 返回答案：HTML富文本渲染，图片为外链，浏览器自行处理

#### 兜底：转人工触发
- 主动触发：用户点击转人工按钮
- 自动触发（可配置）：
  - 连续N次匹配不上（默认3次）
  - 情绪激动检测（关键词+大模型）

### 3.2.2 知识库数据结构
每条知识记录包含：
- 知识ID
- 所属类目（多级，用/分隔，仅后台筛选用，不参与匹配）
- 知识标题（标准问题，不超过120字）
- 相似问法（多个，每个不超过50字，平均5条）
- 答案类型（纯文本/富文本）
- 答案内容（HTML格式，图片为外链）
- 标签（最多10个）

向量化策略：
- 标准问题向量化
- 每个相似问法向量化
- 所有向量关联同一知识ID
- 预计总向量数：7000条 × 6 ≈ 42000条

### 3.2.3 知识库导入规则
- 支持Excel导入
- 后端自动分批处理（每批1000条）
- 用户只需上传一个Excel，分批逻辑后端自动处理
- 增量更新策略：
  - 有知识ID → 更新对应记录
  - 无知识ID → 插入新记录
- 导入后自动重建向量索引
- 前端实时显示导入进度

Excel表头字段（导入时处理的字段）：
- 知识ID、类目、知识标题、相似问法、答案类型（网页）、答案内容（网页）、标签

## 3.3 Agent层

### 3.3.1 技术框架
- Agent框架：LangGraph
- 大模型：DeepSeek / Qwen（私有化部署，调用本地API）
- 上下文窗口：128K-1M

### 3.3.2 工作流节点
1. 意图识别节点
2. 情绪检测节点（关键词+大模型）
3. RAG检索节点（知识库兜底）
4. 工具调用节点
5. 生成回答节点
6. 置信度判断节点

### 3.3.3 工具调用（Mock数据）
- 查询订单信息（使用电商前台真实订单数据）
- 查询物流状态（mock固定几个状态）
- 发起退款（修改订单状态为退款中）
- 查询商品信息

### 3.3.4 上下文管理
每次请求携带：
- 系统Prompt（角色设定）
- 用户信息摘要（用户基本信息+最近订单）
- 最近3轮对话历史
- 当前检索到的相关内容

存储方案：Redis（会话级别）

## 3.4 身份切换机制

### 3.4.1 切换触发条件
主动触发：
- 用户点击转人工按钮

自动触发（可配置）：
- 连续N次答不上（默认3次）
- 情绪激动检测命中
- 投诉关键词命中

### 3.4.2 切换规则
- 同一会话只能切换一次（机器人→人工）
- 切换后对话记录完整保留
- 上下文连续不中断，用户无需重复描述问题
- 随机从名字库分配客服名称

### 3.4.3 人工客服模式
- 身份：随机从名字库分配客服名称
- 回复风格：口语化、有温度感
- 背后仍是大模型回答（换人设和Prompt）
- 界面展示：头像+名称切换

## 3.5 会话生命周期
```
用户点击客服按钮 → 创建新会话
    ↓
用户和AI多轮对话（都在同一会话内）
    ↓
5分钟无新消息 → 推送评价卡片 + 会话结束
    ↓
用户提交评价 → 评价信息写入会话记录
    ↓
用户再次发消息 → 创建新会话
```

## 3.6 评价机制
- 触发：会话内5分钟无新消息自动推送评价卡片
- 推送评价后会话同时结束
- 收集信息：
  - 是否解决
  - 评价分数（1-5星）
  - 评价标签（答非所问/太简单/太复杂/格式问题等）
  - 评价留言

---

# 四、模块三：后台管理平台

## 4.1 Agent管理

### 4.1.1 Agent配置项
- 基础信息（名称、描述）
- 系统Prompt（机器人模式）
- 人工客服Prompt（人工模式）
- 绑定知识库
- RAG阈值
- 模型选择（DeepSeek/Qwen）
- 模型参数（temperature、top_p、max_tokens）
- 情绪检测开关及关键词
- 投诉关键词列表
- 自动切换触发条件（连续答不上次数）
- 客服名字库
- 工具调用配置（开启/关闭各工具）

### 4.1.2 版本管理规则
- 同一时间只能有一个草稿
- 草稿在测试渠道验证
- 发布后正式渠道自动生效
- 旧版本归档保留可查看
- 支持回滚到历史版本
- 可创建多个Agent，各自独立版本管理
- 同一Agent只有最新发布版本生效

### 4.1.3 工作流展示
- 静态流程图展示（让人一眼看懂当前流程）
- 关键节点参数可在页面配置

## 4.2 Bot管理
- 关联知识库
- 匹配阈值配置（默认0.85）
- 连续答不上N次阈值配置（默认3次）
- 自动转人工开关
- 关键词干预管理：
  - 新增/编辑/删除关键词组
  - 配置匹配方式（精确/包含）
  - 配置触发动作（可多选组合：固定话术/推荐FAQ/转人工）
  - 优先级配置

## 4.3 渠道管理

### 4.3.1 渠道类型
- 测试渠道：仅管理员可访问，用于验证新版本
- 正式渠道：真实用户使用

### 4.3.2 渠道配置项
- 渠道名称/描述
- 语种设置
- 用户访问模式（登录/访客）
- 关联Bot（一个）
- 关联Agent（一个）
- 渠道Token（唯一标识）

### 4.3.3 渠道与Agent关系
- 一个渠道绑定一个Bot和一个Agent
- 可以创建多个Agent供不同渠道选择绑定
- 同一Agent不同版本可分别用于测试/正式渠道

### 4.3.4 发布流程
```
草稿 → 绑定测试渠道验证
    ↓
验证通过 → 发布新版本
    ↓
正式渠道自动切换到最新发布版本
```

## 4.4 知识库管理
- 可创建多个知识库
- 每个Agent可绑定不同知识库
- Excel批量导入（后端自动分批，每批1000条）
- 前端实时显示导入进度
- 增量更新（有ID更新，无ID插入）
- 单条增删改查
- 按类目筛选
- 按标签筛选
- 更新后自动重建向量索引
- 检索效果测试（输入问题查看匹配结果和相似度分数）

## 4.5 会话管理

### 实时监控
- 当前在线会话数
- 每条会话状态（Bot中/Agent中/已转人工）
- 异常会话标记

### 历史记录查询
- 按用户查询
- 按时间查询
- 按状态查询（已解决/转人工）
- 对话详情查看

### 数据标注
- 标记好的回答，沉淀到知识库
- 标记差的回答，作为优化素材

## 4.6 数据报表

### 核心指标
- 日/周/月会话量趋势
- AI解决率
- 转人工率
- 平均会话轮数
- 峰值时段分析

### 问题分析
- Top未解决问题（反映知识库盲点）
- 高频工具调用统计

### 统计方式
- 定时任务每天生成统计数据（daily_statistics表）
- 查询快，有一天延迟

## 4.7 系统配置
- 自动切换触发条件配置
- 情绪关键词词库维护
- 投诉词库维护
- 商品数据管理（管理员录入商品）
- 会话超时时间配置（默认5分钟）
- 评价推送延迟配置（默认5分钟）

---

# 五、技术选型

## 5.1 后端
- 框架：FastAPI（Python，异步，适合高并发）
- Agent框架：LangGraph
- Embedding模型：bge-small-zh（私有化部署）
- 向量数据库：Qdrant
- 关系数据库：PostgreSQL
- 缓存：Redis（会话上下文存储）
- 任务队列：Celery（异步重建索引等耗时任务）
- 大模型：DeepSeek / Qwen（本地私有化API调用）

## 5.2 前端
- 框架：Vue3
- UI库：Element Plus（后台管理页面）
- 对话组件：自研（商城悬浮窗 + 独立对话页面）
- 图表库：ECharts（数据报表）

## 5.3 部署
- 容器化：Docker + Docker Compose
- 网关：Nginx
- 进程管理：Supervisor

---

# 六、数据库设计

## 6.1 表清单（共19张表）

### 电商前台（3张）
- users：用户表
- products：商品表
- orders：订单表

### 知识库（3张）
- knowledge_bases：知识库表
- knowledge_items：知识条目表
- knowledge_similar_questions：相似问法表

### Bot（2张）
- bots：Bot表
- bot_keywords：关键词干预表

### Agent（3张）
- agents：Agent表
- agent_versions：Agent版本表
- agent_configs：Agent配置表

### 渠道（1张）
- channels：渠道表

### 对话系统（4张）
- conversations：会话表
- ai_conversation_details：AI会话明细表
- messages：消息记录表
- annotation_records：数据标注表

### 系统（3张）
- admins：管理员表
- system_configs：系统配置表
- daily_statistics：每日统计表

## 6.2 核心表结构

### users 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| username | varchar(50) | 用户名，唯一 |
| password_hash | varchar(255) | 密码哈希 |
| nickname | varchar(50) | 昵称 |
| avatar | varchar(255) | 头像URL |
| phone | varchar(20) | 手机号 |
| status | smallint | 0禁用/1正常 |
| created_at | timestamp | 注册时间 |
| updated_at | timestamp | 更新时间 |

### products 商品表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| name | varchar(200) | 商品名称 |
| description | text | 商品描述 |
| price | decimal(10,2) | 价格 |
| stock | int | 库存 |
| category | varchar(100) | 分类 |
| images | jsonb | 商品图片列表 |
| status | smallint | 0下架/1上架 |
| created_by | bigint | 创建管理员ID |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### orders 订单表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| order_no | varchar(64) | 订单号，唯一 |
| user_id | bigint | 用户ID |
| product_id | bigint | 商品ID |
| product_name | varchar(200) | 商品名称快照 |
| product_price | decimal(10,2) | 下单时价格快照 |
| quantity | int | 购买数量 |
| total_amount | decimal(10,2) | 订单总金额 |
| status | smallint | 0待付款/1已付款/2已发货/3已收货/4退款中/5已退款/6已取消 |
| logistics_no | varchar(100) | 物流单号 |
| logistics_company | varchar(100) | 物流公司 |
| logistics_status | varchar(50) | 待发货/已发货/运输中/已签收 |
| address | jsonb | 收货地址快照 |
| paid_at | timestamp | 付款时间 |
| shipped_at | timestamp | 发货时间 |
| completed_at | timestamp | 完成时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### knowledge_bases 知识库表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| name | varchar(100) | 知识库名称 |
| description | varchar(500) | 描述 |
| item_count | int | 知识条目数量 |
| vector_status | smallint | 0未建立/1建立中/2已完成/3失败 |
| last_import_at | timestamp | 最后导入时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### knowledge_items 知识条目表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| knowledge_base_id | bigint | 所属知识库ID |
| external_id | varchar(100) | 原系统知识ID |
| category | varchar(200) | 类目（多级用/分隔，仅后台筛选） |
| title | varchar(120) | 标准问题 |
| answer_type | smallint | 0纯文本/1富文本 |
| answer_content | text | 答案内容（HTML格式） |
| vector_id | varchar(100) | Qdrant中的向量ID |
| tags | jsonb | 标签列表 |
| status | smallint | 0禁用/1启用 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### knowledge_similar_questions 相似问法表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| knowledge_item_id | bigint | 所属知识条目ID |
| question | varchar(50) | 相似问法内容 |
| vector_id | varchar(100) | Qdrant中的向量ID |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### bots Bot表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| name | varchar(100) | Bot名称 |
| description | varchar(500) | 描述 |
| knowledge_base_id | bigint | 关联知识库ID |
| match_threshold | float | 匹配相似度阈值，默认0.85 |
| no_answer_count | int | 连续答不上N次触发转人工，默认3 |
| auto_transfer | smallint | 0否/1是，默认1 |
| status | smallint | 0禁用/1启用 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### bot_keywords 关键词干预表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| bot_id | bigint | 所属Bot ID |
| keyword | varchar(100) | 关键词 |
| match_type | smallint | 0精确/1包含 |
| actions | jsonb | 触发动作组合，示例：{"transfer":true,"reply":"话术","recommend_ids":[1,2,3]} |
| priority | int | 优先级，数字越小越高 |
| status | smallint | 0禁用/1启用 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### agents Agent表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| name | varchar(100) | Agent名称 |
| description | varchar(500) | 描述 |
| current_version_id | bigint | 当前生效版本ID |
| draft_version_id | bigint | 当前草稿版本ID |
| status | smallint | 0禁用/1启用 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### agent_versions Agent版本表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| agent_id | bigint | 所属Agent ID |
| version_no | varchar(20) | 版本号，如v1.0 |
| status | smallint | 0草稿/1已发布/2已归档 |
| published_at | timestamp | 发布时间 |
| remark | varchar(500) | 版本备注 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### agent_configs Agent配置表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| agent_version_id | bigint | 关联版本ID，唯一 |
| knowledge_base_id | bigint | 关联知识库ID |
| system_prompt | text | 机器人模式系统Prompt |
| human_prompt | text | 人工客服模式Prompt |
| model_type | smallint | 0DeepSeek/1Qwen |
| model_params | jsonb | 模型参数，示例：{"temperature":0.7,"top_p":0.9,"max_tokens":2048} |
| rag_threshold | float | RAG检索阈值，默认0.75 |
| context_rounds | int | 上下文保留轮数，默认3 |
| emotion_detection | smallint | 情绪检测开关，0关/1开 |
| emotion_keywords | jsonb | 情绪关键词列表 |
| complaint_keywords | jsonb | 投诉关键词列表 |
| auto_transfer | smallint | 自动转人工开关，0关/1开 |
| auto_transfer_count | int | 连续答不上N次触发，默认3 |
| staff_names | jsonb | 客服名字库列表 |
| tools_config | jsonb | 工具调用配置，示例：{"query_order":true,"query_logistics":true,"refund":true,"query_product":true} |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### channels 渠道表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| name | varchar(100) | 渠道名称 |
| description | varchar(500) | 描述 |
| type | smallint | 0测试/1正式 |
| language | varchar(20) | 语种，默认zh-CN |
| access_mode | smallint | 0需登录/1允许访客 |
| bot_id | bigint | 关联Bot ID |
| agent_id | bigint | 关联Agent ID |
| channel_token | varchar(100) | 渠道唯一标识Token |
| status | smallint | 0禁用/1启用 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### conversations 会话表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| conversation_no | varchar(64) | 会话编号，唯一 |
| channel_id | bigint | 渠道ID |
| user_id | bigint | 用户ID，访客可为空 |
| username | varchar(50) | 用户名快照 |
| agent_id | bigint | 使用的Agent ID |
| bot_id | bigint | 使用的Bot ID |
| session_type | smallint | 0机器人会话/1人工会话/2机器人转人工 |
| current_mode | smallint | 0Bot/1Agent/2人工 |
| staff_name | varchar(50) | 分配的客服名称 |
| is_transferred | smallint | 0否/1是 |
| transfer_at | timestamp | 转人工时间 |
| transfer_reason | smallint | 0用户主动/1连续答不上/2情绪激动/3关键词触发 |
| is_resolved | smallint | 0否/1是 |
| no_answer_count | int | 连续未答上次数 |
| message_count | int | 消息总数 |
| round_count | int | 对话轮次 |
| started_at | timestamp | 会话开始时间 |
| ended_at | timestamp | 会话结束时间 |
| duration | int | 会话时长（秒） |
| first_response_at | timestamp | 首次响应时间 |
| close_reason | smallint | 0超时自动关闭/1用户主动关闭/2系统关闭 |
| evaluated | smallint | 0否/1是 |
| eval_score | smallint | 评价分数1-5星 |
| eval_tags | jsonb | 评价标签列表 |
| eval_comment | text | 评价留言 |
| eval_resolved | smallint | 评价是否解决，0否/1是 |
| eval_at | timestamp | 评价时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### ai_conversation_details AI会话明细表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigserial | 主键 |
| conversation_id | bigint | 会话ID |
| channel_id | bigint | 渠道ID |
| channel_type | varchar(50) | 渠道类型快照 |
| channel_name | varchar(100) | 渠道名称快照 |
| user_id | bigint | 用户ID |
| round_index | int | 第几轮对话 |
| user_message | text | 用户原声 |
| bot_answer | text | Bot回答内容 |
| agent_answer | text | Agent回答内容 |
| answer_source | smallint | 0Bot FAQ/1关键词干预/2Agent/3人工模式 |
| is_resolved | smallint | 本轮是否解决 |
| is_transferred | smallint | 本轮是否触发转人工 |
| is_no_answer | smallint | 本轮是否无答案 |
| is_clicked | smallint | 推荐答案是否点击 |
| is_liked | smallint | 是否点赞 |
| is_disliked | smallint | 是否点踩 |
| dislike_reason | smallint | 0答非所问/1太简单/2太复杂/3格式问题 |
| knowledge_item_id | bigint | 命中的知识条目ID |
| match_score | float | 匹配相似度分数 |
| emotion_detected | smallint | 是否检测到情绪 |
| tools_called | jsonb | 本轮调用的工具列