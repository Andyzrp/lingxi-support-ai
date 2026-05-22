-- =============================================
-- 智能客服系统 PostgreSQL 建表SQL (v2.0)
-- 基于实际数据库结构导出更新
-- =============================================

SET client_encoding = 'UTF8';

-- 1. admins 管理员表
CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    role SMALLINT NOT NULL DEFAULT 1,
    status SMALLINT NOT NULL DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_admins_username ON admins (username);
CREATE INDEX idx_admins_role ON admins (role);
CREATE INDEX idx_admins_status ON admins (status);

-- 2. users 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    phone VARCHAR(20),
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_status ON users (status);

-- 3. products 商品表
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    category VARCHAR(100),
    images JSONB,
    status SMALLINT NOT NULL DEFAULT 1,
    created_by BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_products_status ON products (status);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_created_at ON products (created_at);
ALTER TABLE products ADD CONSTRAINT fk_products_created_by FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE RESTRICT;

-- 4. orders 订单表
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    order_no VARCHAR(64) NOT NULL,
    user_id BIGINT NOT NULL,
    product_id BIGINT,
    product_name VARCHAR(200) NOT NULL,
    product_price NUMERIC(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    total_amount NUMERIC(10,2) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    logistics_no VARCHAR(100),
    logistics_company VARCHAR(100),
    logistics_status VARCHAR(50),
    address JSONB,
    paid_at TIMESTAMP,
    shipped_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_orders_order_no ON orders (order_no);
CREATE INDEX idx_orders_user_id ON orders (user_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_created_at ON orders (created_at);
CREATE INDEX idx_orders_user_status ON orders (user_id, status);
ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE orders ADD CONSTRAINT fk_orders_product_id FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;

-- 5. knowledge_bases 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    item_count INT DEFAULT 0,
    vector_status SMALLINT DEFAULT 0,
    last_import_at TIMESTAMP,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_kb_status ON knowledge_bases (vector_status);
CREATE INDEX idx_kb_created_at ON knowledge_bases (created_at);

-- 6. knowledge_items 知识条目表
CREATE TABLE IF NOT EXISTS knowledge_items (
    id BIGSERIAL PRIMARY KEY,
    knowledge_base_id BIGINT NOT NULL,
    external_id VARCHAR(100),
    category VARCHAR(200),
    title VARCHAR(120) NOT NULL,
    answer_type SMALLINT NOT NULL DEFAULT 0,
    answer_content TEXT,
    vector_id VARCHAR(100),
    tags JSONB,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ki_knowledge_base_id ON knowledge_items (knowledge_base_id);
CREATE INDEX idx_ki_external_id ON knowledge_items (external_id);
CREATE INDEX idx_ki_category ON knowledge_items (category);
CREATE INDEX idx_ki_status ON knowledge_items (status);
CREATE INDEX idx_ki_base_status ON knowledge_items (knowledge_base_id, status);
ALTER TABLE knowledge_items ADD CONSTRAINT fk_ki_knowledge_base_id FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE RESTRICT;

-- 7. knowledge_similar_questions 相似问法表
CREATE TABLE IF NOT EXISTS knowledge_similar_questions (
    id BIGSERIAL PRIMARY KEY,
    knowledge_item_id BIGINT NOT NULL,
    question VARCHAR(200) NOT NULL,
    vector_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ksq_knowledge_item_id ON knowledge_similar_questions (knowledge_item_id);
CREATE INDEX idx_ksq_vector_id ON knowledge_similar_questions (vector_id);
ALTER TABLE knowledge_similar_questions ADD CONSTRAINT fk_ksq_knowledge_item_id FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id) ON DELETE RESTRICT;

-- 8. bots Bot表
CREATE TABLE IF NOT EXISTS bots (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    knowledge_base_id BIGINT,
    match_threshold FLOAT DEFAULT 0.85,
    no_answer_count INT DEFAULT 3,
    auto_transfer SMALLINT DEFAULT 1,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_bots_knowledge_base_id ON bots (knowledge_base_id);
CREATE INDEX idx_bots_status ON bots (status);
ALTER TABLE bots ADD CONSTRAINT fk_bots_knowledge_base_id FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE RESTRICT;

-- 9. bot_keywords 关键词干预表
CREATE TABLE IF NOT EXISTS bot_keywords (
    id BIGSERIAL PRIMARY KEY,
    bot_id BIGINT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    match_type SMALLINT NOT NULL DEFAULT 1,
    actions JSONB NOT NULL,
    priority INT DEFAULT 0,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_bk_bot_id ON bot_keywords (bot_id);
CREATE INDEX idx_bk_priority ON bot_keywords (priority);
CREATE INDEX idx_bk_status ON bot_keywords (status);
CREATE INDEX idx_bk_bot_status ON bot_keywords (bot_id, status);
ALTER TABLE bot_keywords ADD CONSTRAINT fk_bk_bot_id FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE RESTRICT;

-- 10. agents Agent表
CREATE TABLE IF NOT EXISTS agents (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    current_version_id BIGINT,
    draft_version_id BIGINT,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agents_status ON agents (status);
CREATE INDEX idx_agents_current_version ON agents (current_version_id);
CREATE INDEX idx_agents_draft_version ON agents (draft_version_id);

-- 11. agent_versions Agent版本表
CREATE TABLE IF NOT EXISTS agent_versions (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT NOT NULL,
    version_no VARCHAR(20) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0,
    published_at TIMESTAMP,
    remark VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_av_agent_id ON agent_versions (agent_id);
CREATE INDEX idx_av_status ON agent_versions (status);
CREATE INDEX idx_av_published_at ON agent_versions (published_at);
CREATE INDEX idx_av_agent_status ON agent_versions (agent_id, status);
ALTER TABLE agent_versions ADD CONSTRAINT fk_av_agent_id FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT;

-- 补充agents表的version外键
ALTER TABLE agents ADD CONSTRAINT fk_agents_current_version FOREIGN KEY (current_version_id) REFERENCES agent_versions(id) ON DELETE RESTRICT;
ALTER TABLE agents ADD CONSTRAINT fk_agents_draft_version FOREIGN KEY (draft_version_id) REFERENCES agent_versions(id) ON DELETE RESTRICT;

-- 12. agent_configs Agent配置表
CREATE TABLE IF NOT EXISTS agent_configs (
    id BIGSERIAL PRIMARY KEY,
    agent_version_id BIGINT NOT NULL,
    knowledge_base_id BIGINT,
    system_prompt TEXT,
    human_prompt TEXT,
    model_type SMALLINT DEFAULT 0,
    model_params JSONB,
    rag_threshold FLOAT DEFAULT 0.75,
    context_rounds INT DEFAULT 3,
    emotion_detection SMALLINT DEFAULT 1,
    emotion_keywords JSONB,
    complaint_keywords JSONB,
    auto_transfer SMALLINT DEFAULT 1,
    auto_transfer_count INT DEFAULT 3,
    staff_names JSONB,
    tools_config JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_ac_version_id ON agent_configs (agent_version_id);
CREATE INDEX idx_ac_knowledge_base_id ON agent_configs (knowledge_base_id);
ALTER TABLE agent_configs ADD CONSTRAINT fk_ac_agent_version_id FOREIGN KEY (agent_version_id) REFERENCES agent_versions(id) ON DELETE RESTRICT;
ALTER TABLE agent_configs ADD CONSTRAINT fk_ac_knowledge_base_id FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE RESTRICT;

-- 13. channels 渠道表
CREATE TABLE IF NOT EXISTS channels (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    type SMALLINT NOT NULL DEFAULT 0,
    language VARCHAR(20) DEFAULT 'zh-CN',
    access_mode SMALLINT DEFAULT 0,
    bot_id BIGINT,
    agent_id BIGINT,
    channel_token VARCHAR(100) NOT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_channels_token ON channels (channel_token);
CREATE INDEX idx_channels_type ON channels (type);
CREATE INDEX idx_channels_bot_id ON channels (bot_id);
CREATE INDEX idx_channels_agent_id ON channels (agent_id);
CREATE INDEX idx_channels_status ON channels (status);
ALTER TABLE channels ADD CONSTRAINT fk_channels_bot_id FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE RESTRICT;
ALTER TABLE channels ADD CONSTRAINT fk_channels_agent_id FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT;

-- 14. channel_configs 渠道配置表
CREATE TABLE IF NOT EXISTS channel_configs (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    config_type VARCHAR(20) NOT NULL,
    title VARCHAR(100),
    content TEXT,
    image_url VARCHAR(500),
    link_url VARCHAR(500),
    extra JSONB,
    sort_order INT NOT NULL DEFAULT 0,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_channel_configs_channel_id ON channel_configs (channel_id, config_type, sort_order);
ALTER TABLE channel_configs ADD CONSTRAINT fk_channel_configs_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE;

-- 15. conversations 会话表
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    conversation_no VARCHAR(64) NOT NULL,
    channel_id BIGINT,
    user_id BIGINT,
    username VARCHAR(50),
    agent_id BIGINT,
    bot_id BIGINT,
    session_type SMALLINT DEFAULT 0,
    current_mode SMALLINT DEFAULT 0,
    staff_name VARCHAR(50),
    is_transferred SMALLINT DEFAULT 0,
    transfer_at TIMESTAMP,
    transfer_reason SMALLINT,
    is_resolved SMALLINT DEFAULT 0,
    no_answer_count INT DEFAULT 0,
    message_count INT DEFAULT 0,
    round_count INT DEFAULT 0,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration INT,
    first_response_at TIMESTAMP,
    close_reason SMALLINT,
    evaluated SMALLINT DEFAULT 0,
    eval_score SMALLINT,
    eval_tags JSONB,
    eval_comment TEXT,
    eval_resolved SMALLINT,
    eval_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    eval_pushed_at TIMESTAMP
);
CREATE UNIQUE INDEX idx_conv_no ON conversations (conversation_no);
CREATE INDEX idx_conv_channel_id ON conversations (channel_id);
CREATE INDEX idx_conv_user_id ON conversations (user_id);
CREATE INDEX idx_conv_agent_id ON conversations (agent_id);
CREATE INDEX idx_conv_session_type ON conversations (session_type);
CREATE INDEX idx_conv_is_transferred ON conversations (is_transferred);
CREATE INDEX idx_conv_is_resolved ON conversations (is_resolved);
CREATE INDEX idx_conv_started_at ON conversations (started_at);
CREATE INDEX idx_conv_ended_at ON conversations (ended_at);
CREATE INDEX idx_conv_evaluated ON conversations (evaluated);
CREATE INDEX idx_conv_channel_started ON conversations (channel_id, started_at);
CREATE INDEX idx_conv_user_started ON conversations (user_id, started_at);
CREATE INDEX idx_conv_channel_resolved ON conversations (channel_id, is_resolved, started_at);
CREATE INDEX idx_conversations_status ON conversations (status);
CREATE INDEX idx_conversations_eval_pushed ON conversations (eval_pushed_at) WHERE eval_pushed_at IS NULL AND status = 'closed';
ALTER TABLE conversations ADD CONSTRAINT fk_conv_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE RESTRICT;
ALTER TABLE conversations ADD CONSTRAINT fk_conv_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE conversations ADD CONSTRAINT fk_conv_agent_id FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT;
ALTER TABLE conversations ADD CONSTRAINT fk_conv_bot_id FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE RESTRICT;

-- 16. ai_conversation_details AI会话明细表
CREATE TABLE IF NOT EXISTS ai_conversation_details (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    channel_id BIGINT,
    channel_type VARCHAR(50),
    channel_name VARCHAR(100),
    user_id BIGINT,
    round_index INT NOT NULL DEFAULT 1,
    user_message TEXT,
    bot_answer TEXT,
    agent_answer TEXT,
    answer_source SMALLINT,
    is_resolved SMALLINT DEFAULT 0,
    is_transferred SMALLINT DEFAULT 0,
    is_no_answer SMALLINT DEFAULT 0,
    is_clicked SMALLINT DEFAULT 0,
    is_liked SMALLINT DEFAULT 0,
    is_disliked SMALLINT DEFAULT 0,
    dislike_reason SMALLINT,
    knowledge_item_id BIGINT,
    match_score FLOAT,
    emotion_detected SMALLINT DEFAULT 0,
    tools_called JSONB,
    response_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_acd_conv_round ON ai_conversation_details (conversation_id, round_index);
CREATE INDEX idx_acd_channel_id ON ai_conversation_details (channel_id);
CREATE INDEX idx_acd_user_id ON ai_conversation_details (user_id);
CREATE INDEX idx_acd_is_resolved ON ai_conversation_details (is_resolved);
CREATE INDEX idx_acd_is_transferred ON ai_conversation_details (is_transferred);
CREATE INDEX idx_acd_is_no_answer ON ai_conversation_details (is_no_answer);
CREATE INDEX idx_acd_knowledge_item_id ON ai_conversation_details (knowledge_item_id);
CREATE INDEX idx_acd_answer_source ON ai_conversation_details (answer_source);
CREATE INDEX idx_acd_created_at ON ai_conversation_details (created_at);
ALTER TABLE ai_conversation_details ADD CONSTRAINT fk_acd_conversation_id FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT;
ALTER TABLE ai_conversation_details ADD CONSTRAINT fk_acd_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE RESTRICT;
ALTER TABLE ai_conversation_details ADD CONSTRAINT fk_acd_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE ai_conversation_details ADD CONSTRAINT fk_acd_knowledge_item_id FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id) ON DELETE RESTRICT;

-- 17. messages 消息记录表
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    sender_type SMALLINT NOT NULL,
    sender_name VARCHAR(50),
    content_type SMALLINT NOT NULL DEFAULT 0,
    content TEXT,
    extra JSONB,
    is_read SMALLINT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_msg_conversation_id ON messages (conversation_id);
CREATE INDEX idx_msg_sender_type ON messages (sender_type);
CREATE INDEX idx_msg_content_type ON messages (content_type);
CREATE INDEX idx_msg_created_at ON messages (created_at);
CREATE INDEX idx_msg_conv_created ON messages (conversation_id, created_at);
ALTER TABLE messages ADD CONSTRAINT fk_msg_conversation_id FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT;

-- 18. annotation_records 数据标注表
CREATE TABLE IF NOT EXISTS annotation_records (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    message_id BIGINT,
    ai_detail_id BIGINT,
    annotation_type SMALLINT NOT NULL,
    annotation_tags JSONB,
    annotation_note TEXT,
    knowledge_item_id BIGINT,
    correct_answer TEXT,
    annotated_by BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ar_conversation_id ON annotation_records (conversation_id);
CREATE INDEX idx_ar_message_id ON annotation_records (message_id);
CREATE INDEX idx_ar_ai_detail_id ON annotation_records (ai_detail_id);
CREATE INDEX idx_ar_annotation_type ON annotation_records (annotation_type);
CREATE INDEX idx_ar_annotated_by ON annotation_records (annotated_by);
CREATE INDEX idx_ar_created_at ON annotation_records (created_at);
CREATE UNIQUE INDEX uq_annotation_message_id ON annotation_records (message_id);
ALTER TABLE annotation_records ADD CONSTRAINT fk_ar_conversation_id FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT;
ALTER TABLE annotation_records ADD CONSTRAINT fk_ar_message_id FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE RESTRICT;
ALTER TABLE annotation_records ADD CONSTRAINT fk_ar_ai_detail_id FOREIGN KEY (ai_detail_id) REFERENCES ai_conversation_details(id) ON DELETE RESTRICT;
ALTER TABLE annotation_records ADD CONSTRAINT fk_ar_annotated_by FOREIGN KEY (annotated_by) REFERENCES admins(id) ON DELETE RESTRICT;
ALTER TABLE annotation_records ADD CONSTRAINT fk_ar_knowledge_item_id FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id) ON DELETE RESTRICT;

-- 19. system_configs 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_sc_config_key ON system_configs (config_key);

-- 20. daily_statistics 每日统计表
CREATE TABLE IF NOT EXISTS daily_statistics (
    id BIGSERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    channel_id BIGINT NOT NULL,
    total_sessions INT DEFAULT 0,
    bot_sessions INT DEFAULT 0,
    agent_sessions INT DEFAULT 0,
    transferred_sessions INT DEFAULT 0,
    resolved_sessions INT DEFAULT 0,
    resolve_rate FLOAT DEFAULT 0,
    transfer_rate FLOAT DEFAULT 0,
    avg_round_count FLOAT DEFAULT 0,
    avg_duration FLOAT DEFAULT 0,
    peak_hour SMALLINT,
    peak_session_count INT DEFAULT 0,
    no_answer_count INT DEFAULT 0,
    top_no_answer JSONB,
    eval_count INT DEFAULT 0,
    avg_eval_score FLOAT DEFAULT 0,
    avg_response_ms FLOAT,
    intent_distribution JSONB DEFAULT '{}',
    source_distribution JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_ds_date_channel ON daily_statistics (stat_date, channel_id);
CREATE INDEX idx_ds_stat_date ON daily_statistics (stat_date);
CREATE INDEX idx_ds_channel_id ON daily_statistics (channel_id);
ALTER TABLE daily_statistics ADD CONSTRAINT fk_ds_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE RESTRICT;

-- 插入预置数据
INSERT INTO system_configs (config_key, config_value, description) VALUES
('session_timeout', '{"value": 300}', '会话超时秒数，默认5分钟'),
('eval_push_delay', '{"value": 300}', '评价推送延迟秒数'),
('default_no_answer_reply', '{"value": "很抱歉小疆没能理解您的问题，您可以点击下方按钮转接人工服务"}', '默认无答案回复话术')
ON CONFLICT (config_key) DO NOTHING;
