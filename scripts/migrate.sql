-- migrate.sql
-- 执行方式：
-- psql -h 10.99.216.94 -p 5432 -U lingxi -d lingxi_support -f migrate.sql

-- ==================== 前置检查 ====================
\echo '======================================'
\echo '  灵犀客服 - 数据库迁移脚本 v3.0'
\echo '======================================'

-- ==================== 电商前台（3张表）====================

CREATE TABLE IF NOT EXISTS users (
    id           BIGSERIAL    PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname     VARCHAR(100),
    avatar       VARCHAR(500),
    phone        VARCHAR(20),
    status       SMALLINT     NOT NULL DEFAULT 1,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id           BIGSERIAL      PRIMARY KEY,
    name         VARCHAR(200)   NOT NULL,
    description  TEXT,
    price        DECIMAL(10,2)  NOT NULL,
    stock        INTEGER        NOT NULL DEFAULT 0,
    category     VARCHAR(100),
    images       JSONB          DEFAULT '[]',
    status       SMALLINT       NOT NULL DEFAULT 1,
    created_at   TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id             BIGSERIAL      PRIMARY KEY,
    order_no       VARCHAR(50)    NOT NULL UNIQUE,
    user_id        BIGINT         NOT NULL REFERENCES users(id),
    product_id     BIGINT         NOT NULL REFERENCES products(id),
    product_name   VARCHAR(200)   NOT NULL,
    product_price  DECIMAL(10,2)  NOT NULL,
    quantity       INTEGER        NOT NULL DEFAULT 1,
    total_amount   DECIMAL(10,2)  NOT NULL,
    status         SMALLINT       NOT NULL DEFAULT 0,
    address        JSONB,
    logistics_no   VARCHAR(100),
    logistics_company VARCHAR(100),
    logistics_tracks  JSONB       DEFAULT '[]',
    refund_reason  TEXT,
    refund_remark  TEXT,
    refund_at      TIMESTAMP,
    created_at     TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP      NOT NULL DEFAULT NOW()
);

\echo '✅ 电商前台表创建完成'

-- ==================== 知识库（3张表）====================

CREATE TABLE IF NOT EXISTS knowledge_bases (
    id          BIGSERIAL    PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    item_count  INTEGER      DEFAULT 0,
    status      SMALLINT     NOT NULL DEFAULT 1,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id             BIGSERIAL    PRIMARY KEY,
    base_id        BIGINT       NOT NULL REFERENCES knowledge_bases(id),
    title          VARCHAR(500) NOT NULL,
    category       VARCHAR(100),
    answer_type    VARCHAR(20)  DEFAULT 'text',
    answer_content TEXT,
    tags           JSONB        DEFAULT '[]',
    status         SMALLINT     NOT NULL DEFAULT 1,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_similar_questions (
    id         BIGSERIAL    PRIMARY KEY,
    item_id    BIGINT       NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    question   VARCHAR(500) NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

\echo '✅ 知识库表创建完成'

-- ==================== Bot（2张表）====================

CREATE TABLE IF NOT EXISTS bots (
    id                   BIGSERIAL    PRIMARY KEY,
    name                 VARCHAR(200) NOT NULL,
    knowledge_base_id    BIGINT       REFERENCES knowledge_bases(id),
    similarity_threshold DECIMAL(3,2) DEFAULT 0.85,
    no_answer_reply      TEXT,
    status               SMALLINT     NOT NULL DEFAULT 1,
    created_at           TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bot_keywords (
    id         BIGSERIAL    PRIMARY KEY,
    bot_id     BIGINT       NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    keyword    VARCHAR(200) NOT NULL,
    match_type VARCHAR(20)  NOT NULL DEFAULT 'contains',
    actions    JSONB        NOT NULL DEFAULT '[]',
    priority   INTEGER      NOT NULL DEFAULT 0,
    status     SMALLINT     NOT NULL DEFAULT 1,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

\echo '✅ Bot表创建完成'

-- ==================== Agent（3张表）====================

CREATE TABLE IF NOT EXISTS agents (
    id                  BIGSERIAL    PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    current_version_id  BIGINT,
    draft_version_id    BIGINT,
    status              SMALLINT     NOT NULL DEFAULT 1,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_versions (
    id                   BIGSERIAL    PRIMARY KEY,
    agent_id             BIGINT       NOT NULL REFERENCES agents(id),
    version_no           VARCHAR(50)  NOT NULL,
    model_type           VARCHAR(100),
    system_prompt        TEXT,
    human_prompt         TEXT,
    temperature          DECIMAL(3,2) DEFAULT 0.7,
    max_tokens           INTEGER      DEFAULT 1024,
    tools_config         JSONB        DEFAULT '{}',
    no_answer_threshold  INTEGER      DEFAULT 3,
    transfer_keywords    JSONB        DEFAULT '[]',
    status               VARCHAR(20)  DEFAULT 'draft',
    published_at         TIMESTAMP,
    created_at           TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_configs (
    id               BIGSERIAL PRIMARY KEY,
    agent_version_id BIGINT    NOT NULL REFERENCES agent_versions(id),
    system_prompt    TEXT,
    human_prompt     TEXT,
    model_type       VARCHAR(100),
    tools_config     JSONB     DEFAULT '{}',
    temperature      DECIMAL(3,2) DEFAULT 0.7,
    max_tokens       INTEGER   DEFAULT 1024,
    staff_names      JSONB     DEFAULT '[]',
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

\echo '✅ Agent表创建完成'

-- ==================== 渠道（2张表）====================

CREATE TABLE IF NOT EXISTS channels (
    id            BIGSERIAL    PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    description   TEXT,
    type          VARCHAR(50)  DEFAULT 'test',
    language      VARCHAR(20)  DEFAULT 'zh',
    access_mode   VARCHAR(20)  DEFAULT 'public',
    bot_id        BIGINT       REFERENCES bots(id),
    agent_id      BIGINT       REFERENCES agents(id),
    channel_token VARCHAR(100) NOT NULL UNIQUE,
    status        SMALLINT     NOT NULL DEFAULT 1,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_configs (
    id          SERIAL       PRIMARY KEY,
    channel_id  INTEGER      NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    config_type VARCHAR(20)  NOT NULL,
    title       VARCHAR(200),
    content     TEXT,
    image_url   VARCHAR(500),
    link_url    VARCHAR(500),
    extra       JSONB,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    status      SMALLINT     NOT NULL DEFAULT 1,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_configs_channel_id
    ON channel_configs (channel_id, config_type, sort_order);

\echo '✅ 渠道表创建完成'

-- ==================== 对话系统（4张表）====================

CREATE TABLE IF NOT EXISTS conversations (
    id                BIGSERIAL    PRIMARY KEY,
    conversation_no   VARCHAR(50)  NOT NULL UNIQUE,
    channel_id        BIGINT       REFERENCES channels(id),
    user_id           BIGINT       REFERENCES users(id),
    username          VARCHAR(100),
    agent_id          BIGINT       REFERENCES agents(id),
    bot_id            BIGINT       REFERENCES bots(id),
    session_type      SMALLINT     DEFAULT 0,
    current_mode      SMALLINT     DEFAULT 0,
    staff_name        VARCHAR(100),
    is_transferred    BOOLEAN      DEFAULT FALSE,
    transfer_at       TIMESTAMP,
    transfer_reason   SMALLINT,
    is_resolved       SMALLINT     DEFAULT 0,
    no_answer_count   INTEGER      DEFAULT 0,
    message_count     INTEGER      DEFAULT 0,
    round_count       INTEGER      DEFAULT 0,
    started_at        TIMESTAMP,
    ended_at          TIMESTAMP,
    duration          INTEGER,
    first_response_at TIMESTAMP,
    close_reason      SMALLINT,
    evaluated         SMALLINT     DEFAULT 0,
    eval_score        SMALLINT,
    eval_tags         JSONB,
    eval_comment      VARCHAR(500),
    eval_resolved     SMALLINT,
    eval_at           TIMESTAMP,
    status            VARCHAR(20)  DEFAULT 'active',
    created_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL    PRIMARY KEY,
    conversation_id BIGINT       NOT NULL REFERENCES conversations(id),
    sender_type     SMALLINT     NOT NULL DEFAULT 0,
    sender_name     VARCHAR(100),
    content_type    SMALLINT     DEFAULT 0,
    content         TEXT,
    extra           JSONB,
    is_read         SMALLINT     DEFAULT 0,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS ai_conversation_details (
    id                BIGSERIAL PRIMARY KEY,
    conversation_id   BIGINT    NOT NULL REFERENCES conversations(id),
    message_id        BIGINT    REFERENCES messages(id),
    node_type         VARCHAR(50),
    answer_source     VARCHAR(50),
    response_ms       INTEGER,
    model             VARCHAR(100),
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS annotation_records (
    id              BIGSERIAL    PRIMARY KEY,
    conversation_id BIGINT       NOT NULL REFERENCES conversations(id),
    message_id      BIGINT       REFERENCES messages(id),
    annotator_id    BIGINT       REFERENCES admins(id),
    label           VARCHAR(20)  NOT NULL DEFAULT 'neutral',
    correct_answer  TEXT,
    remark          TEXT,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (message_id, annotator_id)
);

\echo '✅ 对话系统表创建完成'

-- ==================== 系统（3张表）====================

CREATE TABLE IF NOT EXISTS admins (
    id            BIGSERIAL    PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname      VARCHAR(100),
    role          SMALLINT     NOT NULL DEFAULT 1,
    status        SMALLINT     NOT NULL DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_configs (
    id         BIGSERIAL    PRIMARY KEY,
    key        VARCHAR(100) NOT NULL UNIQUE,
    value      TEXT,
    desc_text  VARCHAR(500),
    created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_statistics (
    id                  BIGSERIAL    PRIMARY KEY,
    stat_date           DATE         NOT NULL,
    channel_id          INTEGER      DEFAULT 0,
    total_sessions      INTEGER      DEFAULT 0,
    bot_sessions        INTEGER      DEFAULT 0,
    agent_sessions      INTEGER      DEFAULT 0,
    human_sessions      INTEGER      DEFAULT 0,
    resolved_sessions   INTEGER      DEFAULT 0,
    transferred_sessions INTEGER     DEFAULT 0,
    resolve_rate        DECIMAL(5,4) DEFAULT 0,
    transfer_rate       DECIMAL(5,4) DEFAULT 0,
    avg_response_ms     INTEGER      DEFAULT 0,
    avg_rounds          DECIMAL(5,2) DEFAULT 0,
    avg_duration        INTEGER      DEFAULT 0,
    peak_hour           SMALLINT,
    no_answer_count     INTEGER      DEFAULT 0,
    satisfaction_score  DECIMAL(3,2) DEFAULT 0,
    evaluation_count    INTEGER      DEFAULT 0,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (stat_date, channel_id)
);

\echo '✅ 系统表创建完成'

-- ==================== 初始化数据 ====================

INSERT INTO admins (username, password_hash, nickname, role, status)
VALUES (
    'admin',
    '$5$rounds=535000$lingxi$8K9mN2pQ3rS4tU5vW6xY7zA8bC9dE0fG1hI2jK3lM4n',
    '超级管理员',
    0,
    1
) ON CONFLICT (username) DO NOTHING;

INSERT INTO knowledge_bases (name, description, status)
VALUES ('电商通用知识库', '覆盖退款/物流/订单/商品场景', 1)
ON CONFLICT DO NOTHING;

INSERT INTO bots (name, knowledge_base_id, similarity_threshold, no_answer_reply, status)
VALUES (
    '电商客服Bot',
    1,
    0.85,
    '抱歉，我暂时无法准确回答您的问题，正在为您转接人工客服...',
    1
) ON CONFLICT DO NOTHING;

INSERT INTO agents (name, description, status)
VALUES ('电商客服Agent', '处理电商售后全场景', 1)
ON CONFLICT DO NOTHING;

INSERT INTO channels (name, channel_token, bot_id, agent_id, type, status)
VALUES (
    '商城测试渠道',
    'LrDSr5ZRFjCu0mBunFxOTiMTTVeZ8m7xCJhqygIfHmw',
    1,
    1,
    'test',
    1
) ON CONFLICT (channel_token) DO NOTHING;

INSERT INTO products (name, description, price, stock, category, images, status)
VALUES
    ('iPhone 15 Pro',        'A17 Pro芯片，钛金属边框',   7999.00, 100, '手机数码', '["https://picsum.photos/400/400?random=1"]', 1),
    ('AirPods Pro',          '主动降噪，H2芯片',           1899.00, 200, '手机数码', '["https://picsum.photos/400/400?random=2"]', 1),
    ('iPad Air M2',          'M2芯片，轻薄便携',           4799.00,  80, '手机数码', '["https://picsum.photos/400/400?random=3"]', 1),
    ('Apple Watch Series 9', 'S9芯片，健康监测',           2999.00, 150, '穿戴设备', '["https://picsum.photos/400/400?random=4"]', 1),
    ('机械键盘 Cherry轴',    'Cherry红轴，RGB背光',         599.00,  300, '电脑外设', '["https://picsum.photos/400/400?random=5"]', 1),
    ('27英寸4K显示器',       'IPS面板，HDR400',            2499.00,  60, '电脑外设', '["https://picsum.photos/400/400?random=6"]', 1),
    ('4K网络摄像头',         'Sony传感器，自动对焦',         899.00,   5, '电脑外设', '["https://picsum.photos/400/400?random=7"]', 1),
    ('65W氮化镓充电器',      '多口快充，折叠插头',           199.00,  500, '配件',   '["https://picsum.photos/400/400?random=8"]', 1)
ON CONFLICT DO NOTHING;

UPDATE channels SET bot_id = 1 WHERE bot_id IS NULL;
UPDATE channels SET agent_id = 1 WHERE agent_id IS NULL;

\echo '✅ 初始化数据插入完成'

-- ==================== 索引优化 ====================

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_channel_id
    ON conversations (channel_id, status);

CREATE INDEX IF NOT EXISTS idx_conversations_status
    ON conversations (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_user_id
    ON orders (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_knowledge_items_base_id
    ON knowledge_items (base_id, status);

CREATE INDEX IF NOT EXISTS idx_daily_statistics_date
    ON daily_statistics (stat_date DESC, channel_id);

\echo '✅ 索引创建完成'

-- ==================== 验证结果 ====================
\echo ''
\echo '【数据库表清单】'
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(quote_ident(tablename))) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

\echo ''
\echo '【初始数据验证】'
SELECT 'admins'     AS table_name, COUNT(*) AS count FROM admins
UNION ALL
SELECT 'products',                 COUNT(*)           FROM products
UNION ALL
SELECT 'channels',                 COUNT(*)           FROM channels
UNION ALL
SELECT 'bots',                     COUNT(*)           FROM bots
UNION ALL
SELECT 'agents',                   COUNT(*)           FROM agents
UNION ALL
SELECT 'knowledge_bases',          COUNT(*)           FROM knowledge_bases;

\echo ''
\echo '======================================'
\echo '  数据库迁移完成！'
\echo '======================================'