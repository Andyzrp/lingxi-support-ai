<template>
  <div class="chat-page">
    <!-- 顶部品牌栏 -->
    <div class="chat-header">
      <div class="chat-header-left">
        <div class="chat-logo-wrap">
          <img src="/brand/lingxi-chat-button.svg" class="chat-logo" alt="灵犀客服" />
        </div>
        <div class="chat-brand">
          <div class="chat-brand-name">灵犀智能客服</div>
          <div class="chat-brand-sub">{{ channelName || '在线客服' }}</div>
        </div>
      </div>
      <div class="chat-header-right">
        <div class="chat-status">
          <span class="status-dot" :class="wsStatus === 'connected' ? 'status-dot--online' : 'status-dot--offline'"></span>
          <span class="status-text">{{ wsStatus === 'connected' ? '在线' : '连接中' }}</span>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesRef">
      <!-- 欢迎语（固定，始终显示）-->
      <div class="welcome-msg">
        <div class="welcome-avatar-wrap">
          <img src="/brand/lingxi-chat-button.svg" class="welcome-avatar" alt="客服" />
        </div>
        <div class="welcome-bubble">
          您好！我是灵犀智能客服，很高兴为您服务 😊<br />
          请问有什么可以帮助您？
        </div>
      </div>

      <!-- 热点问题卡片（固定，始终显示）-->
      <div class="hot-questions-card" v-if="displayedQuestions.length">
        <div class="hot-questions-header">
          <span class="hot-questions-title">猜您想问</span>
          <span
            class="hot-questions-refresh"
            :class="{ 'is-spinning': isRefreshing }"
            @click="refreshHotQuestions"
          >
            <el-icon><RefreshRight /></el-icon>
            换一批
          </span>
        </div>
        <div class="hot-questions-list">
          <div
            v-for="(q, index) in displayedQuestions"
            :key="index"
            class="hot-question-item"
            @click="sendMessage(typeof q === 'string' ? q : q.text)"
          >
            <span class="hot-question-text">
              {{ typeof q === 'string' ? q : q.text }}
            </span>
            <el-icon class="hot-question-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- Banner 横向卡片 -->
      <div class="banner-section" v-if="banners.length">
        <div
          v-for="(b, index) in banners"
          :key="index"
          class="banner-card"
          :class="{ 'banner-card--clickable': b.link_url }"
          @click="b.link_url && openLink(b.link_url)"
        >
          <div class="banner-card-img">
            <img
              v-if="b.image_url"
              :src="b.image_url"
              class="banner-img"
              @error="(e) => e.target.style.display = 'none'"
            />
            <div v-if="!b.image_url" class="banner-card-img-placeholder">
              <el-icon :size="28"><Picture /></el-icon>
            </div>
          </div>
          <div class="banner-card-content">
            <div class="banner-card-title">{{ b.title }}</div>
            <div class="banner-card-subtitle" v-if="b.subtitle">{{ b.subtitle }}</div>
          </div>
        </div>
      </div>

      <!-- 正常消息列表 -->
      <div
        v-for="msg in messages"
        :key="msg.id || msg.timestamp"
        class="msg-item"
        :class="msg.role === 'user' ? 'msg-item--user' : 'msg-item--bot'"
      >
        <template v-if="msg.role === 'user'">
          <div class="msg-row msg-row--right">
            <div class="msg-main msg-main--right">
              <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
              <div class="msg-bubble msg-bubble--user">{{ msg.content }}</div>
            </div>
            <img :src="USER_AVATAR_IMG" class="msg-avatar" alt="我" />
          </div>
        </template>

        <template v-else-if="msg.role === 'bot' || msg.role === 'agent'">
          <div class="msg-row msg-row--left">
            <img :src="msg.role === 'agent' ? AGENT_AVATAR_IMG : BOT_AVATAR_IMG" class="msg-avatar" alt="客服" />
            <div class="msg-main">
              <div class="msg-meta-row">
                <span class="msg-sender">{{ msg.role === 'agent' ? '人工客服' : '智能客服' }}</span>
                <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="msg-bubble msg-bubble--bot" v-if="msg.type === 'thinking'">
                <div class="thinking-dots"><span></span><span></span><span></span></div>
              </div>
              <div class="msg-bubble msg-bubble--bot" v-else v-html="msg.content"></div>
              <OrderCard
                v-if="msg.extra?.card_type === 'order'"
                :data="msg.extra.card_data"
                class="msg-card"
                @refund="handleRefund"
              />
              <OrderListCard v-else-if="msg.extra?.card_type === 'order_list'" :data="msg.extra.card_data" class="msg-card" @refund="handleRefund" />
              <LogisticsCard v-else-if="msg.extra?.card_type === 'logistics'" :card-data="msg.extra.card_data" class="msg-card" />
              <ProductCard v-else-if="msg.extra?.card_type === 'product'" :card-data="msg.extra.card_data" class="msg-card" />
              <ProductListCard v-else-if="msg.extra?.card_type === 'product_list'" :products="msg.extra.card_data" class="msg-card" />
              <OrdersCard v-else-if="msg.extra?.card_type === 'orders_list'" :orders="msg.extra.card_data" class="msg-card" />
            </div>
          </div>
        </template>

        <template v-else-if="msg.role === 'system'">
          <div class="msg-system">
            <span class="system-text">{{ msg.content }}</span>
          </div>
        </template>
      </div>

      <div ref="bottomRef"></div>
    </div>

    <!-- 评价卡片 -->
    <div class="evaluate-wrap" v-if="showEvaluate">
      <EvaluateCard :conversation-id="conversationId" @submitted="handleEvaluateSubmit" />
    </div>

    <!-- 输入区 -->
    <div class="chat-input-wrap">
      <div class="input-row">
        <div class="transferred-tip" v-if="isTransferred">
          <el-icon><Headset /></el-icon>
          <span>已连接人工客服，请继续描述您的问题</span>
        </div>
        <el-input
          v-model="inputText"
          :placeholder="isTransferred ? '请继续描述您的问题...' : '请输入您的问题...'"
          :disabled="wsStatus !== 'connected'"
          @keyup.enter="sendMessage()"
        />
        <el-button type="primary" :disabled="wsStatus !== 'connected' || !inputText.trim()" @click="sendMessage()">发送</el-button>
      </div>
      <div class="input-actions" v-if="!isTransferred">
        <el-button text size="small" type="warning" @click="handleTransfer">
          <el-icon><Headset /></el-icon>
          转人工客服
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Headset, ArrowRight, Picture, RefreshRight } from '@element-plus/icons-vue'
import axios from 'axios'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import OrderCard     from '@/components/chat/OrderCard.vue'
import OrderListCard from '@/components/chat/OrderListCard.vue'
import LogisticsCard from '@/components/chat/LogisticsCard.vue'
import ProductCard   from '@/components/chat/ProductCard.vue'
import ProductListCard from '@/components/chat/ProductListCard.vue'
import OrdersCard from '@/components/chat/OrdersCard.vue'
import EvaluateCard  from '@/components/chat/EvaluateCard.vue'

const route       = useRoute()
const userStore   = useUserStore()
const channelToken = route.query.channel || ''

function getUserId() {
  const urlUserId = route.query.user_id
  if (urlUserId && !isNaN(Number(urlUserId))) {
    console.log('[ChatPage] URL user_id:', urlUserId)
    return String(urlUserId)
  }
  if (userStore.userInfo?.id) {
    console.log('[ChatPage] 已登录用户 id:', userStore.userInfo.id)
    return String(userStore.userInfo.id)
  }
  let guestId = localStorage.getItem('lingxi_guest_id')
  if (!guestId) {
    guestId = `guest_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    localStorage.setItem('lingxi_guest_id', guestId)
  }
  console.log('[ChatPage] 匿名访客 id:', guestId)
  return guestId
}

const userId = getUserId()

const USER_AVATAR_IMG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="%235b8af5"/>
  <circle cx="20" cy="15" r="7" fill="white" opacity="0.95"/>
  <ellipse cx="20" cy="35" rx="12" ry="9" fill="white" opacity="0.95"/>
</svg>`

const BOT_AVATAR_IMG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="%2367c23a"/>
  <rect x="11" y="14" width="18" height="14" rx="4" fill="white" opacity="0.95"/>
  <circle cx="16" cy="20" r="2.5" fill="%2367c23a"/>
  <circle cx="24" cy="20" r="2.5" fill="%2367c23a"/>
  <rect x="15" y="25" width="10" height="2" rx="1" fill="%2367c23a"/>
  <rect x="19" y="9" width="2" height="5" rx="1" fill="white" opacity="0.95"/>
  <circle cx="20" cy="8" r="2" fill="white" opacity="0.95"/>
  <rect x="9" y="18" width="3" height="6" rx="1.5" fill="white" opacity="0.8"/>
  <rect x="28" y="18" width="3" height="6" rx="1.5" fill="white" opacity="0.8"/>
</svg>`

const AGENT_AVATAR_IMG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="%23e6a23c"/>
  <circle cx="20" cy="14" r="6" fill="white" opacity="0.95"/>
  <path d="M10 27 Q10 20 20 20 Q30 20 30 27" fill="white" opacity="0.95"/>
  <rect x="9" y="24" width="4" height="6" rx="2" fill="white" opacity="0.9"/>
  <rect x="27" y="24" width="4" height="6" rx="2" fill="white" opacity="0.9"/>
  <path d="M13 30 Q13 33 20 33 Q27 33 27 30" fill="none" stroke="white" stroke-width="2" opacity="0.9"/>
</svg>`

// 热点问题：全部存储，每次显示4条，换一批滚动
const allHotQuestions = ref(['我的订单在哪里？', '如何申请退款？', '物流到哪了？', '商品质量有问题怎么办？', '取消订单怎么操作？', '从哪里进入登录？', '有优惠活动吗？', '怎么联系人工客服？'])
const banners = ref([])
const PAGE_SIZE = 4
const hotPage = ref(0)
const isRefreshing = ref(false)
const displayedQuestions = ref([])

// 初始化显示的问题
function initDisplayedQuestions() {
  if (allHotQuestions.value.length) {
    hotPage.value = 0
    displayedQuestions.value = allHotQuestions.value.slice(0, PAGE_SIZE)
  }
}

function refreshHotQuestions() {
  if (isRefreshing.value || !allHotQuestions.value.length) return
  isRefreshing.value = true

  const total    = allHotQuestions.value.length
  const nextPage = (hotPage.value + 1) % Math.ceil(total / PAGE_SIZE)
  const start    = nextPage * PAGE_SIZE
  const end      = start + PAGE_SIZE

  if (end <= total) {
    displayedQuestions.value = allHotQuestions.value.slice(start, end)
  } else {
    displayedQuestions.value = [
      ...allHotQuestions.value.slice(start, total),
      ...allHotQuestions.value.slice(0, end - total),
    ]
  }

  hotPage.value = nextPage

  setTimeout(() => {
    isRefreshing.value = false
  }, 600)
}

// 监听 allHotQuestions 变化时重新初始化
watch(allHotQuestions, () => {
  initDisplayedQuestions()
}, { immediate: true })

function openLink(url) {
  window.open(url, '_blank')
}

const messages       = ref([])
const bottomRef      = ref(null)
const inputText      = ref('')
const conversationId = ref(null)
const isTransferred  = ref(false)
const showEvaluate   = ref(false)
const wsStatus       = ref('disconnected')
const channelName    = ref('')

let ws             = null
let heartbeatTimer = null
let reconnectTimer = null
let reconnectCount = 0
const MAX_RECONNECT = 5

function scrollToBottom() {
  bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
}

function addMessage(msg) {
  messages.value.push(msg)
  setTimeout(scrollToBottom, 30)
}

function removeThinking() {
  const idx = messages.value.findIndex(m => m.type === 'thinking')
  if (idx !== -1) messages.value.splice(idx, 1)
}

function connect() {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host  = window.location.hostname
  const port  = window.location.port === '3000' ? '8000' : window.location.port
  const url   = `${proto}://${host}:${port}/api/v1/chat/ws/${channelToken}?user_id=${encodeURIComponent(userId)}`
  wsStatus.value = 'connecting'
  ws = new WebSocket(url)

  ws.onopen = () => {
    wsStatus.value  = 'connected'
    reconnectCount  = 0
    startHeartbeat()
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleServerMsg(data)
    } catch { /* ignore */ }
  }

  ws.onerror = () => { wsStatus.value = 'disconnected' }
  ws.onclose = () => {
    wsStatus.value = 'disconnected'
    stopHeartbeat()
    scheduleReconnect()
  }
}

function handleServerMsg(data) {
  if (data.type === 'pong') return
  if (data.conversation_id) conversationId.value = data.conversation_id
  if (data.channel_name) channelName.value = data.channel_name

  if (data.type === 'thinking') {
    addMessage({ id: Date.now(), role: isTransferred.value ? 'agent' : 'bot', type: 'thinking', content: '', timestamp: data.timestamp })
    return
  }

  removeThinking()

  if (data.type === 'message') {
    // 跳过服务器欢迎消息（静态欢迎语已单独显示）
    if (!messages.value.length && data.content?.includes('请问有什么可以帮助您')) {
      return
    }
    addMessage({
      id: data.message_id || Date.now(),
      role: data.role,
      content: data.content,
      timestamp: data.timestamp,
      extra: data.extra || null,
    })
    return
  }

  if (data.type === 'transfer') {
    isTransferred.value = true
    addMessage({ id: Date.now(), role: 'system', content: data.content, timestamp: data.timestamp })
    return
  }

  if (data.type === 'error') {
    ElMessage.error(data.content || '消息发送失败')
  }
}

function startHeartbeat() {
  heartbeatTimer = setInterval(() => {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
  }, 30000)
}

function stopHeartbeat() {
  clearInterval(heartbeatTimer)
}

function scheduleReconnect() {
  if (reconnectCount >= MAX_RECONNECT) return
  const delays = [2000, 4000, 8000, 16000, 30000]
  reconnectCount++
  reconnectTimer = setTimeout(connect, delays[reconnectCount - 1] || 30000)
}

function sendMessage(text) {
  const content = (text || inputText.value).trim()
  if (!content) return
  if (ws?.readyState !== WebSocket.OPEN) {
    ElMessage.warning('连接已断开，请稍候重试')
    return
  }
  addMessage({ id: Date.now(), role: 'user', content, timestamp: dayjs().format('YYYY-MM-DD HH:mm:ss') })
  ws.send(JSON.stringify({ type: 'chat', content }))
  inputText.value = ''
}

function handleTransfer() {
  if (ws?.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ type: 'transfer' }))
}

function handleApplyRefund({ orderNo, reason }) {
  if (!ws || ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
    ElMessage.error('连接尚未就绪，请稍候再试')
    return
  }
  ws.send(JSON.stringify({ type: 'refund', order_no: orderNo, reason }))
}

async function handleRefund(orderNo) {
  try {
    await ElMessageBox.confirm(
      `确定要为订单 ${orderNo} 申请退款？`,
      '申请退款',
      { confirmButtonText: '确认申请', cancelButtonText: '取消', type: 'warning' }
    )
    const { value: reason } = await ElMessageBox.prompt(
      '请填写退款原因（必填）',
      '退款申请',
      {
        confirmButtonText: '提交申请',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：商品质量问题、不想要了...',
        inputValidator: (val) => (val && val.trim() ? true : '请填写退款原因'),
      }
    )
    handleApplyRefund({ orderNo, reason: reason.trim() })
  } catch {
    // 用户取消不处理
  }
}

function handleEvaluateSubmit() {
  showEvaluate.value = false
  addMessage({ id: Date.now(), role: 'system', content: '感谢您的评价，再见！', timestamp: dayjs().format('YYYY-MM-DD HH:mm:ss') })
}

function formatTime(ts) {
  return ts ? dayjs(ts).format('HH:mm') : ''
}

async function loadChannelConfig() {
  if (!channelToken) return
  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await axios.get(`${baseURL}/api/v1/channels/config/public?token=${encodeURIComponent(channelToken)}`)
    const cfg = res.data?.data
    if (!cfg) return
    if (cfg.hot_questions?.length) {
      allHotQuestions.value = cfg.hot_questions
    }
    if (cfg.banners?.length) {
      banners.value = cfg.banners
    }
    if (cfg.channel_name) {
      channelName.value = cfg.channel_name
    }
  } catch (e) {
    // 加载失败使用默认值，不影响主流程
    console.warn('[ChatPage] 加载渠道配置失败:', e?.message)
  }
}

onMounted(() => {
  connect()
  loadChannelConfig()
})
onUnmounted(() => {
  ws?.close()
  stopHeartbeat()
  clearTimeout(reconnectTimer)
})
</script>

<style scoped lang="scss">
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 480px;
  margin: 0 auto;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #ffffff;
  flex-shrink: 0;
  border-bottom: 1px solid #ebedf0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-logo-wrap {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.chat-logo {
  width: 24px;
  height: 24px;
}

.chat-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-brand-name {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
  letter-spacing: 0.2px;
}

.chat-brand-sub {
  font-size: 11px;
  color: #909399;
  font-weight: 400;
  line-height: 1.2;
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 5px;
  background: #f5f7fa;
  border-radius: 20px;
  padding: 4px 10px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &--online {
    background: #52c41a;
    box-shadow: 0 0 6px rgba(82, 196, 26, 0.6);
    animation: pulse-green 2s infinite;
  }

  &--offline {
    background: #909399;
  }
}

.status-text {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 4px rgba(82, 196, 26, 0.4); }
  50% { box-shadow: 0 0 8px rgba(82, 196, 26, 0.8); }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;

  &::-webkit-scrollbar       { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #e4e7ed; border-radius: 2px; }
}

.welcome-msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.welcome-avatar-wrap {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.welcome-avatar {
  width: 24px;
  height: 24px;
}

.welcome-bubble {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 2px 12px 12px 12px;
  padding: 10px 14px;
  font-size: 14px;
  color: #303133;
  line-height: 1.65;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;

  &--left  { flex-direction: row; }
  &--right { flex-direction: row-reverse; }
}

.msg-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: calc(100% - 96px);

  &--right {
    align-items: flex-end;
  }
}

.msg-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

:deep(.msg-row--right) {
  flex-direction: row-reverse;
}

:deep(.msg-main--right) {
  align-items: flex-end;
}

.msg-meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.msg-sender {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.msg-time {
  font-size: 11px;
  color: #c0c4cc;
}

.msg-bubble {
  font-size: 14px;
  line-height: 1.65;
  padding: 10px 14px;
  width: fit-content;
  word-break: break-word;
  white-space: pre-wrap;

  &--user {
    background: #5b8af5;
    color: #fff;
    border-radius: 12px 2px 12px 12px;
    align-self: flex-end;
  }

  &--bot {
    background: #fff;
    color: #303133;
    border: 1px solid #e4e7ed;
    border-radius: 2px 12px 12px 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    align-self: flex-start;
  }
}

.thinking-dots {
  display: flex;
  gap: 4px;
  padding: 2px 4px;

  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #c0c4cc;
    animation: bounce 1.2s infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

.msg-card {
  margin-top: 6px;
}

.msg-system {
  display: flex;
  justify-content: center;
  padding: 4px 0;
}

.system-text {
  font-size: 12px;
  color: #909399;
  background: rgba(144,147,153,0.1);
  border-radius: 10px;
  padding: 3px 12px;
}

.evaluate-wrap {
  padding: 0 12px 8px;
  flex-shrink: 0;
}

.chat-input-wrap {
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 10px 12px 12px;
  flex-shrink: 0;
  box-shadow: 0 -1px 4px rgba(0,0,0,0.04);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.quick-item {
  font-size: 12px;
  color: #5b8af5;
  background: rgba(91,138,245,0.08);
  border: 1px solid rgba(91,138,245,0.2);
  border-radius: 12px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover { background: rgba(91,138,245,0.15); }
}

.input-row {
  display: flex;
  gap: 8px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}

.transferred-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #e6a23c;
  padding: 6px 4px;
  margin-bottom: 6px;
}

// ==================== 猜您想问 ====================
.hot-questions-card {
  margin-left: 48px;
  margin-bottom: 12px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #ebedf0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  width: 320px;
  flex-shrink: 0;
}

.hot-questions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px 8px;
}

.hot-questions-title {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a2e;
}

.hot-questions-refresh {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 8px;
  transition: all 0.2s;
  user-select: none;

  .el-icon {
    font-size: 13px;
    transition: transform 0.6s ease;
  }

  &:hover {
    color: #5b8af5;
    background: rgba(91, 138, 245, 0.08);
  }

  &.is-spinning .el-icon {
    transform: rotate(360deg);
  }
}

.hot-questions-list {
  padding: 0 0 4px;
}

.hot-question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-top: 1px solid #f5f7fa;

  &:hover {
    background: #f5f8ff;

    .hot-question-text {
      color: #5b8af5;
    }

    .hot-question-arrow {
      color: #5b8af5;
      transform: translateX(3px);
    }
  }
}

.hot-question-text {
  font-size: 13px;
  color: #303133;
  transition: color 0.15s;
  line-height: 1.4;
}

.hot-question-arrow {
  color: #c0c4cc;
  font-size: 12px;
  flex-shrink: 0;
  transition: color 0.15s, transform 0.15s;
}

// ==================== Banner 横版卡片 ====================
.banner-section {
  margin-left: 48px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 160px;
  box-sizing: border-box;
}

.banner-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #ebedf0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s, transform 0.2s;
  width: 100%;
  box-sizing: border-box;

  &--clickable {
    cursor: pointer;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      transform: translateY(-1px);
    }
  }
}

.banner-card-img {
  width: 100%;
  height: 120px;
  overflow: hidden;
  display: block;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf0 100%);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }

  .banner-card--clickable:hover & img {
    transform: scale(1.03);
  }
}

.banner-card-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: linear-gradient(135deg, #f5f7fa, #e8ecf0);
}

.banner-card-content {
  padding: 8px 12px 10px;
  text-align: center;
}

.banner-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.4;
}

.banner-card-subtitle {
  font-size: 12px;
  color: #909399;
  margin-top: 3px;
  line-height: 1.4;
}
</style>
