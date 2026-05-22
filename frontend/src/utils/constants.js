// WebSocket 固定 channel_token [1]
export const CHANNEL_TOKEN = 'LrDSr5ZRFjCu0mBunFxOTiMTTVeZ8m7xCJhqygIfHmw'

// 订单状态映射（与后端 Order.status 一致）
export const ORDER_STATUS = {
  0: { text: '待付款',  color: '#E6A23C', tag: 'warning' },
  1: { text: '已付款',  color: '#409EFF', tag: 'primary' },
  2: { text: '已发货',  color: '#67C23A', tag: 'success' },
  3: { text: '已收货',  color: '#909399', tag: 'info'    },
  4: { text: '退款中',  color: '#F56C6C', tag: 'danger'  },
  5: { text: '已退款',  color: '#909399', tag: 'info'    },
  6: { text: '已取消',  color: '#909399', tag: 'info'    },
}

// 消息来源标签
export const ANSWER_SOURCE = {
  rag:     { text: '知识库',   color: '#409EFF' },
  tool:    { text: '工具调用', color: '#67C23A' },
  llm:     { text: 'AI生成',  color: '#9B59B6' },
  keyword: { text: '关键词',  color: '#E6A23C' },
  default: { text: '兜底回复', color: '#909399' },
}

// 客服身份配置
export const AGENT_MODE = {
  bot: {
    name: '灵犀客服',
    label: '智能客服',
    tagClass: 'lx-tag-bot',
    avatar: '🤖',
  },
  agent: {
    name: '灵犀 AI 助手',
    label: 'AI 助手',
    tagClass: 'lx-tag-agent',
    avatar: '✨',
  },
  human: {
    name: '人工客服',
    label: '人工客服',
    tagClass: 'lx-tag-human',
    avatar: '👤',
  },
}

// 占位图
export const PLACEHOLDER_IMG = (id = 1) =>
  `https://picsum.photos/400/400?random=${id}`