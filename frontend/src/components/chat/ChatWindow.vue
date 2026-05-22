<template>
  <div class="chat-window">

    <!-- 顶部状态栏 -->
    <div class="chat-header">
      <div class="agent-info">
        <!-- 头像 -->
        <div class="agent-avatar" :class="avatarClass">
          {{ agentAvatar }}
        </div>
        <!-- 名称和标签 -->
        <div class="agent-detail">
          <div class="agent-name-row">
            <span class="agent-name">{{ agentName }}</span>
            <span class="agent-tag" :class="agentTagClass">
              {{ agentLabel }}
            </span>
          </div>
          <!-- 在线状态 -->
          <div class="agent-status">
            <span class="status-dot" :class="{ thinking: chatStore.isThinking }" />
            <span class="status-text">
              {{ chatStore.isThinking ? '正在输入...' : '在线' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 右侧操作 -->
      <div class="header-actions">
        <!-- 转人工按钮（非人工模式才显示） -->
        <el-button
          v-if="!chatStore.isHuman"
          text
          size="small"
          class="transfer-btn"
          @click="handleTransfer"
        >
          转人工
        </el-button>
        <!-- 关闭按钮 -->
        <el-button text size="small" @click="chatStore.closeChat()">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <MessageList @apply-refund="handleApplyRefund" />

    <!-- 输入框 -->
    <InputBox
      @send="handleSend"
      @transfer="handleTransfer"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'
import { Close } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { ChatWebSocket } from '@/utils/websocket'
import appConfig from '@/config/app.js'
import MessageList from './MessageList.vue'
import InputBox from './InputBox.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const chatStore = useChatStore()
const userStore = useUserStore()

const isTransferred = ref(false)
const staffName = ref('')

function senderTypeToRole(senderType) {
  const map = { 0: 'user', 1: 'bot', 2: 'agent', 3: 'human', 4: 'system' }
  return map[senderType] || 'bot'
}

const agentMap = computed(() => ({
  bot: {
    name: '灵犀客服',
    label: '智能客服',
    avatar: '🤖',
    tagClass: 'tag-bot',
    avatarClass: 'avatar-bot',
  },
  agent: {
    name: '灵犀 AI',
    label: 'AI 助手',
    avatar: '🤖',
    tagClass: 'tag-agent',
    avatarClass: 'avatar-agent',
  },
  human: {
    name: isTransferred.value ? staffName.value : '人工客服',
    label: '人工客服',
    avatar: '👤',
    tagClass: 'tag-human',
    avatarClass: 'avatar-human',
  },
}))

const agentName = computed(() => {
  if (isTransferred.value) return staffName.value || '人工客服'
  return agentMap.value[chatStore.agentMode]?.name || '灵犀客服'
})
const agentLabel = computed(() => agentMap.value[chatStore.agentMode]?.label || '智能客服')
const agentAvatar = computed(() => agentMap.value[chatStore.agentMode]?.avatar || '🤖')
const agentTagClass = computed(() => agentMap.value[chatStore.agentMode]?.tagClass || 'tag-bot')
const avatarClass = computed(() => agentMap.value[chatStore.agentMode]?.avatarClass || 'avatar-bot')

let wsClient = null

function initWebSocket() {
  if (wsClient) {
    wsClient.disconnect()
  }
  wsClient = new ChatWebSocket(userStore.userId)

  wsClient
    .on('open', () => {
      chatStore.isConnected = true
    })
    .on('message', handleWsMessage)
    .on('thinking', () => {
      chatStore.isThinking = true
    })
    .on('transfer', (data) => {
      isTransferred.value = true
      staffName.value = data.agent_name || '人工客服'
      chatStore.switchToHuman(data.agent_name)
      chatStore.addMessage({
        role: 'system',
        content: data.content,
      })
    })
    .on('error', () => {
      chatStore.isThinking = false
      ElMessage.error('连接异常，请刷新重试')
    })
    .on('close', () => {
      chatStore.isConnected = false
    })
    .on('reconnect_failed', () => {
      ElMessage.warning('网络连接失败，请刷新页面重试')
    })

  wsClient.connect()
}

function disconnect() {
  if (wsClient) {
    wsClient.disconnect()
    wsClient = null
  }
}

function handleWsMessage(data) {
  if (!chatStore.isOpen) return  // 防止组件卸载后仍处理消息
  if (data.type === 'thinking') return
  if (data.type === 'pong') return
  if (data.type === 'transfer') return

  chatStore.isThinking = false

  if (data.type === 'message') {
    if (data.conversation_id && !chatStore.conversationId) {
      chatStore.conversationId = data.conversation_id
    }
    try {
      chatStore.addMessage(data)
    } catch (e) {
      console.warn('添加消息失败:', e)
    }
    if (data.need_transfer && data.agent_name) {
      isTransferred.value = true
      staffName.value = data.agent_name
      chatStore.switchToHuman(data.agent_name)
    }
  }

  if (data.type === 'error') {
    try {
      chatStore.addMessage({
        role: 'system',
        content: data.content || '处理消息失败，请稍后重试',
      })
    } catch (e) {
      console.warn('添加消息失败:', e)
    }
  }
}

async function loadHistory() {
  if (!chatStore.conversationId) return
  try {
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await axios.get(
      `${baseURL}/api/v1/chat/conversations/${chatStore.conversationId}/messages`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    )
    const historyMsgs = ((res.data?.data) || []).map((m) => ({
      id: m.id,
      role: senderTypeToRole(m.role),
      content: m.content,
      timestamp: m.created_at,
      extra: m.extra || null,
    }))
    chatStore.messages = historyMsgs
  } catch (e) {
    console.warn('[loadHistory] 加载历史消息失败:', e?.response?.status, e?.message)
  }
}

async function initChat() {
  isTransferred.value = false
  staffName.value = ''
  chatStore.agentMode = 'bot'
  chatStore.agentName = '灵犀客服'
  chatStore.messages = []
  chatStore.conversationId = null
  chatStore.isThinking = false
  chatStore.showEvaluate = false

  initWebSocket()
}

onMounted(async () => {
  if (props.visible) {
    await initChat()
  }
})

watch(
  () => props.visible,
  async (newVal, oldVal) => {
    if (newVal === oldVal) return
    if (newVal) {
      await initChat()
    } else {
      disconnect()
    }
  }
)

onUnmounted(() => {
  disconnect()
})

function handleSend(text) {
  if (!text.trim() || !chatStore.isConnected) return

  chatStore.addMessage({
    role: 'user',
    content: text,
  })

  chatStore.isThinking = true

  wsClient.sendChat(text)
}

function handleApplyRefund({ orderNo, reason }) {
  if (!wsClient) {
    ElMessage.error('连接未建立，请刷新页面')
    return
  }
  if (wsClient.readyState === WebSocket.CONNECTING || wsClient.readyState === WebSocket.CLOSED || wsClient.readyState === WebSocket.CLOSING) {
    ElMessage.error('连接尚未就绪，请稍候再试')
    return
  }
  wsClient.sendRefund(orderNo, reason)
}

async function handleTransfer() {
  try {
    await ElMessageBox.confirm(
      '转接后将由人工客服继续为您服务，您无需重复描述问题。',
      '确定要转接人工客服吗？',
      {
        confirmButtonText: '确认转接',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    wsClient.sendTransfer()
  } catch {
    // cancel
  }
}
</script>

<style scoped>
.chat-window {
  position: absolute;
  bottom: 76px;
  right: 0;
  width: 380px;
  height: 600px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.16);
  border: 1px solid var(--lx-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  flex-shrink: 0;
}
.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 头像 */
.agent-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.avatar-bot   { background: rgba(255,255,255,0.2); }
.avatar-agent { background: rgba(124, 58, 237, 0.3); }
.avatar-human { background: rgba(34, 197, 94, 0.3); }

.agent-detail {}
.agent-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
}
.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

/* 身份标签 */
.agent-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 7px;
  border-radius: 999px;
}
.tag-bot   { background: rgba(255,255,255,0.2); color: #fff; }
.tag-agent { background: rgba(167,139,250,0.3); color: #e9d5ff; }
.tag-human { background: rgba(34,197,94,0.25);  color: #bbf7d0; }

/* 在线状态 */
.agent-status {
  display: flex;
  align-items: center;
  gap: 5px;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  transition: background 0.3s ease;
}
.status-dot.thinking {
  background: #facc15;
  animation: pulse 1s infinite;
}
.status-text {
  font-size: 12px;
  color: rgba(255,255,255,0.75);
}

/* 操作按钮 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.transfer-btn {
  color: rgba(255,255,255,0.85) !important;
  font-size: 12px;
}
.transfer-btn:hover {
  color: #fff !important;
  background: rgba(255,255,255,0.15) !important;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

/* 响应式 */
@media (max-width: 480px) {
  .chat-window {
    width: 100vw;
    height: 100vh;
    bottom: 0;
    right: 0;
    border-radius: 0;
  }
}
</style>