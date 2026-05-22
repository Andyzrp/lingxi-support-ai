import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    isOpen: false,
    isConnected: false,
    isThinking: false,          // AI思考中（显示loading）

    messages: [],               // 消息列表
    conversationId: null,       // 当前会话ID [1]

    // 当前客服身份
    agentMode: 'bot',           // 'bot' | 'agent' | 'human'
    agentName: '灵犀客服',

    showEvaluate: false,        // 是否显示评价卡片
  }),

  getters: {
    isHuman: (state) => state.agentMode === 'human',
    lastMessage: (state) => state.messages[state.messages.length - 1] ?? null,
  },

  actions: {
    openChat()  { this.isOpen = true  },
    closeChat() { this.isOpen = false },

    // 添加一条消息
    addMessage(msg) {
      if (!this.isOpen) return  // 防止组件卸载后仍处理消息
      this.messages.push({
        id: msg.message_id || `local_${Date.now()}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString(),
        intent: msg.extra?.intent,
        emotion: msg.extra?.emotion,
        source: msg.extra?.answer_source,
        needTransfer: msg.need_transfer || false,
        cardType: msg.extra?.card_type || null,
        cardData: msg.extra?.card_data || null,
      })
      // 保存会话ID [1]
      if (msg.conversation_id) {
        this.conversationId = msg.conversation_id
      }
    },

    // 切换到人工客服
    switchToHuman(agentName) {
      this.agentMode = 'human'
      this.agentName = agentName || '人工客服'
    },

    // 切换到Agent模式
    switchToAgent() {
      this.agentMode = 'agent'
      this.agentName = '灵犀 AI 助手'
    },

    // 重置会话（关闭窗口时调用）
    reset() {
      this.messages = []
      this.conversationId = null
      this.isConnected = false
      this.isThinking = false
      this.agentMode = 'bot'
      this.agentName = '灵犀客服'
      this.showEvaluate = false
    },
  },
})