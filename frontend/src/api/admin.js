import request from './request'

// ==================== 管理员认证 ====================
export const adminAuthApi = {
  // 管理员登录
  login: (data) => request.post('/admin/auth/login', data),

  // 获取当前管理员信息
  getMe: () => request.get('/admin/auth/me'),

  // 获取管理员列表
  getAdmins: (params) => request.get('/admin/auth/admins', { params }),

  // 创建管理员
  createAdmin: (data) => request.post('/admin/auth/admins', data),

  // 更新管理员
  updateAdmin: (id, data) => request.put(`/admin/auth/admins/${id}`, data),

  // 删除管理员
  deleteAdmin: (id) => request.delete(`/admin/auth/admins/${id}`),
}

// ==================== 知识库管理 ====================
export const knowledgeApi = {
  // 获取知识库列表
  getBases: (params) => request.get('/knowledge/bases', { params }),

  // 创建知识库
  createBase: (data) => request.post('/knowledge/bases', data),

  // 更新知识库
  updateBase: (id, data) => request.put(`/knowledge/bases/${id}`, data),

  // 获取知识条目列表
  getItems: (baseId, params) =>
    request.get(`/knowledge/bases/${baseId}/items`, { params }),

  // 新建知识条目
  createItem: (baseId, data) =>
    request.post(`/knowledge/bases/${baseId}/items`, data),

  // Excel 批量导入
  importItems: (baseId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/knowledge/bases/${baseId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 检索测试
  search: (baseId, data) =>
    request.post(`/knowledge/bases/${baseId}/search`, data),

  // 更新知识条目
  updateItem: (itemId, data) => request.put(`/knowledge/items/${itemId}`, data),

  // 删除知识条目
  deleteItem: (itemId) => request.delete(`/knowledge/items/${itemId}`),

  // 批量删除知识条目
  batchDeleteItems: (itemIds) => request.post(`/knowledge/items/batch-delete`, itemIds),

  // 获取导入任务进度
  getImportTask: (taskId) => request.get(`/knowledge/import/progress/${taskId}`),

  // 获取导入错误详情
  getImportErrors: (taskId) => request.get(`/knowledge/import/errors/${taskId}`),

  // 下载导入结果Excel
  downloadImportResult: (taskId) =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/knowledge/import/download-result/${taskId}`,
}

// ==================== Bot 管理 ====================
export const botApi = {
  // 获取 Bot 列表
  getBots: (params) => request.get('/bots', { params }),

  // 创建 Bot
  createBot: (data) => request.post('/bots', data),

  // 更新 Bot
  updateBot: (id, data) => request.put(`/bots/${id}`, data),

  // 删除 Bot
  deleteBot: (botId) => request.delete(`/bots/${botId}`),

  // 获取关键词列表
  getKeywords: (botId, params) =>
    request.get(`/bots/${botId}/keywords`, { params }),

  // 创建关键词
  createKeyword: (botId, data) =>
    request.post(`/bots/${botId}/keywords`, data),

  // 更新关键词
  updateKeyword: (botId, keywordId, data) =>
    request.put(`/bots/${botId}/keywords/${keywordId}`, data),

  // 删除关键词
  deleteKeyword: (botId, keywordId) =>
    request.delete(`/bots/${botId}/keywords/${keywordId}`),
}

// ==================== Agent 管理 ====================
export const agentApi = {
  // 获取 Agent 列表
  getAgents: (params) => request.get('/agents', { params }),

  // 创建 Agent
  createAgent: (data) => request.post('/agents', data),

  // 获取版本列表
  getVersions: (agentId) => request.get(`/agents/${agentId}/versions`),

  // 创建版本（草稿）
  createVersion: (agentId, data) =>
    request.post(`/agents/${agentId}/versions`, data),

  // 发布版本
  publishVersion: (agentId, data) =>
    request.post(`/agents/${agentId}/publish`, data),

  // 更新配置（更新草稿版本配置）
  updateConfig: (agentId, data) =>
    request.put(`/agents/${agentId}/config`, data),

  // 获取配置（草稿版本配置）
  getConfig: (agentId) =>
    request.get(`/agents/${agentId}/config`),

  // 回滚版本
  rollbackVersion: (agentId, data) =>
    request.post(`/agents/${agentId}/rollback`, data),

  // 删除 Agent
  deleteAgent: (agentId) =>
    request.delete(`/agents/${agentId}`),

  // 获取工作流可视化图
  getWorkflowGraph: (agentId, format = 'mermaid') =>
    request.get(`/agents/${agentId}/workflow-graph`, {
      params: { format }
    }),
}

// ==================== 渠道管理 ====================
export const channelApi = {
  // 获取渠道列表
  getChannels: (params) => request.get('/channels', { params }),

  // 创建渠道
  createChannel: (data) => request.post('/channels', data),

  // 更新渠道
  updateChannel: (id, data) => request.put(`/channels/${id}`, data),

  // 获取渠道内容配置
  getConfig: (channelId) => request.get(`/channels/${channelId}/config`),

  // 保存渠道内容配置
  saveConfig: (channelId, data) => request.put(`/channels/${channelId}/config`, data),

  // 删除渠道
  deleteChannel: (channelId) => request.delete(`/channels/${channelId}`),
}

// ==================== 订单管理（管理员视角）====================
export const adminOrderApi = {
  // 获取订单列表
  getOrders: (params) => request.get('/orders/admin/list', { params }),

  // 获取订单详情
  getOrderDetail: (orderNo) => request.get(`/orders/admin/${orderNo}`),

  // 更新订单状态
  updateStatus: (orderNo, data) =>
    request.patch(`/orders/admin/${orderNo}/status`, data),
}

// ==================== 数据报表 ====================
export const reportsApi = {
  // 核心指标概览
  getDashboard: (params) => request.get('/reports/dashboard', { params }),

  // 会话量趋势
  getSessions: (params) => request.get('/reports/sessions', { params }),

  // 解决率趋势
  getResolveRate: (params) =>
    request.get('/reports/resolve-rate', { params }),

  // Top 未解决问题
  getTopUnanswered: (params) =>
    request.get('/reports/top-unanswered', { params }),

  // 意图分布
  getIntentDistribution: (params) =>
    request.get('/reports/intent-distribution', { params }),

  // 满意度统计
  getSatisfaction: (params) =>
    request.get('/reports/satisfaction', { params }),
}

// ==================== 会话记录 ====================
export const conversationApi = {
  // 获取会话列表
  getConversations: (params) =>
    request.get('/chat/conversations', { params }),

  // 获取消息记录
  getMessages: (conversationId) =>
    request.get(`/chat/conversations/${conversationId}/messages`),
}

// ==================== 数据标注 ====================
export const annotationApi = {
  // 创建标注
  create: (data) =>
    request.post('/annotations', data),

  // 查询列表
  getList: (params) =>
    request.get('/annotations', { params }),

  // 查询消息标注状态
  getByMessage: (messageId) =>
    request.get(`/annotations/message/${messageId}`),

  // 更新标注
  update: (id, data) =>
    request.put(`/annotations/${id}`, data),

  // 删除标注
  remove: (id) =>
    request.delete(`/annotations/${id}`),

  // 统计数据
  getStats: (params) =>
    request.get('/annotations/stats', { params }),
}