<template>
  <div class="channel-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">渠道管理</h2>
        <span class="page-sub">共 {{ channelList.length }} 个渠道</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新建渠道
      </el-button>
    </div>

    <!-- 说明横幅 -->
    <div class="tips-banner">
      <el-icon><InfoFilled /></el-icon>
      <span>
        渠道是对话入口的载体，每个渠道绑定一个 Bot 和一个 Agent。
        前端通过 <strong>channel_token</strong> 连接 WebSocket，
        当前测试渠道 Token 已固定为
        <el-tag size="small" type="primary" effect="plain">
          LrDSr5ZRFjCu0mBunFxOTiMTTVeZ8m7xCJhqygIfHmw
        </el-tag>
      </span>
    </div>

    <!-- 渠道卡片列表 -->
    <div v-loading="loading" class="channel-grid">
      <div
        v-for="channel in channelList"
        :key="channel.id"
        class="channel-card"
        :class="`channel-card--${channel.type}`"
      >
        <!-- 卡片头部 -->
        <div class="channel-card-header">
          <div class="channel-icon" :class="`icon--${channel.type}`">
            <el-icon :size="26">
              <Promotion v-if="channel.type === 'production'" />
              <Tools v-else />
            </el-icon>
          </div>
          <div class="channel-header-right">
            <el-tag
              :type="channel.type === 'production' ? 'danger' : 'warning'"
              size="small"
              round
            >
              {{ channel.type === 'production' ? '正式渠道' : '测试渠道' }}
            </el-tag>
            <el-tag
              :type="channel.status === 1 ? 'success' : 'info'"
              size="small"
              round
            >
              {{ channel.status === 1 ? '启用' : '停用' }}
            </el-tag>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, channel)">
              <el-button text :icon="MoreFilled" size="small" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit" :icon="Edit">
                    编辑渠道
                  </el-dropdown-item>
                  <el-dropdown-item command="copyToken" :icon="CopyDocument">
                    复制 Token
                  </el-dropdown-item>
                  <el-dropdown-item command="config" :icon="Tools">
                    内容配置
                  </el-dropdown-item>
                  <el-dropdown-item
                    :command="channel.status === 1 ? 'disable' : 'enable'"
                    :icon="channel.status === 1 ? CircleClose : CircleCheck"
                  >
                    {{ channel.status === 1 ? '停用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item
                    command="delete"
                    :icon="Delete"
                    style="color: #f56c6c"
                  >
                    删除渠道
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 渠道名称 -->
        <div class="channel-name">{{ channel.name }}</div>

        <!-- Channel Token -->
        <div class="channel-token-wrap">
          <div class="token-label">Channel Token</div>
          <div class="token-row">
            <code class="token-value">{{ maskToken(channel.channel_token) }}</code>
            <el-button
              text
              :icon="CopyDocument"
              size="small"
              @click="copyToken(channel.channel_token)"
            />
          </div>
        </div>

        <!-- 关联配置 -->
        <div class="channel-config">
          <!-- 关联 Bot -->
          <div class="config-item">
            <div class="config-label">
              <el-icon><Service /></el-icon>
              关联 Bot
            </div>
            <el-tag
              v-if="getBotName(channel.bot_id)"
              type="primary"
              size="small"
              effect="plain"
            >
              {{ getBotName(channel.bot_id) }}
            </el-tag>
            <el-tag v-else type="danger" size="small" effect="plain">
              未关联
            </el-tag>
          </div>

          <!-- 关联 Agent -->
          <div class="config-item">
            <div class="config-label">
              <el-icon><Cpu /></el-icon>
              关联 Agent
            </div>
            <el-tag
              v-if="getAgentName(channel.agent_id)"
              type="success"
              size="small"
              effect="plain"
            >
              {{ getAgentName(channel.agent_id) }}
            </el-tag>
            <el-tag v-else type="danger" size="small" effect="plain">
              未关联
            </el-tag>
          </div>
        </div>

        <!-- WS 连接地址 -->
        <div class="ws-url-wrap">
          <div class="ws-url-label">WebSocket 地址</div>
          <div class="ws-url-row">
            <code class="ws-url">
              ws://localhost:8000/api/v1/chat/ws/{{ channel.channel_token }}
            </code>
            <el-button
              text
              :icon="CopyDocument"
              size="small"
              @click="copyWsUrl(channel.channel_token)"
            />
          </div>
        </div>

        <!-- 对话链接 -->
        <div class="chat-link-wrap">
          <div class="chat-link-label">对话链接</div>
          <div class="test-user-row">
            <span class="test-user-label">测试用户ID</span>
            <el-input-number
              v-model="testUserIdMap[channel.channel_token]"
              :min="1"
              size="small"
              placeholder="输入用户ID"
              style="width: 130px"
            />
            <span class="test-user-hint">填写后可测试真实订单工具调用</span>
          </div>
          <div class="chat-link-row">
            <code class="chat-link-url">{{ getChatUrl(channel.channel_token) }}</code>
            <el-button text :icon="CopyDocument" size="small" @click="copyChatUrl(channel.channel_token)" />
            <el-button text :icon="ChromeFilled" size="small" @click="openChatUrl(channel.channel_token)" />
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="channel-stats">
          <div class="channel-stat-item">
            <span class="stat-value">{{ channel.today_sessions || 0 }}</span>
            <span class="stat-label">今日会话</span>
          </div>
          <div class="channel-stat-divider"></div>
          <div class="channel-stat-item">
            <span class="stat-value">{{ channel.total_sessions || 0 }}</span>
            <span class="stat-label">累计会话</span>
          </div>
          <div class="channel-stat-divider"></div>
          <div class="channel-stat-item">
            <span class="stat-value">
              {{ formatDate(channel.created_at) }}
            </span>
            <span class="stat-label">创建时间</span>
          </div>
        </div>

        <!-- 卡片底部操作 -->
        <div class="channel-card-footer">
          <el-button
            type="success"
            plain
            size="small"
            :icon="Position"
            @click="openPublish(channel)"
          >
            发布接入
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Edit"
            @click="openEditDialog(channel)"
          >
            编辑配置
          </el-button>
          <el-button
            plain
            size="small"
            :icon="CopyDocument"
            @click="copyToken(channel.channel_token)"
          >
            复制 Token
          </el-button>
          <el-button
            plain
            size="small"
            :icon="ChromeFilled"
            @click="openChatUrl(channel.channel_token)"
          >
            打开对话
          </el-button>
          <el-button
            v-if="channel.type === 'test'"
            type="primary"
            plain
            size="small"
            :icon="View"
            @click="openTestDialog(channel)"
          >
            连接测试
          </el-button>
        </div>
      </div>

      <!-- 新建卡片入口 -->
      <div class="channel-card channel-card--add" @click="openCreateDialog">
        <el-icon :size="36" class="add-icon"><Plus /></el-icon>
        <span class="add-text">新建渠道</span>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && channelList.length === 0"
        description="暂无渠道，点击右上角新建"
        :image-size="100"
        class="channel-empty"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑渠道' : '新建渠道'"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
        class="channel-form"
      >
        <!-- 渠道名称 -->
        <el-form-item label="渠道名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="如：商城正式渠道"
            maxlength="50"
            show-word-limit
            clearable
          />
        </el-form-item>

        <!-- 渠道类型 -->
        <el-form-item label="渠道类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button value="test">
              <el-icon><Tools /></el-icon>
              测试渠道
            </el-radio-button>
            <el-radio-button value="production">
              <el-icon><Promotion /></el-icon>
              正式渠道
            </el-radio-button>
          </el-radio-group>
          <div class="type-hint">
            <span v-if="form.type === 'test'" class="hint-text">
              测试渠道：用于开发调试，日志更详细，不计入正式统计
            </span>
            <span v-else class="hint-text">
              正式渠道：面向真实用户，建议充分测试后再切换
            </span>
          </div>
        </el-form-item>

        <!-- 关联 Bot -->
        <el-form-item label="关联 Bot" prop="bot_id">
          <el-select
            v-model="form.bot_id"
            placeholder="请选择关联的 Bot"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="bot in botList"
              :key="bot.id"
              :label="bot.name"
              :value="bot.id"
            >
              <div class="option-row">
                <span>{{ bot.name }}</span>
                <el-tag size="small" :type="bot.status === 1 ? 'success' : 'info'">
                  {{ bot.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 关联 Agent -->
        <el-form-item label="关联 Agent" prop="agent_id">
          <el-select
            v-model="form.agent_id"
            placeholder="请选择关联的 Agent"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="agent in agentList"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            >
              <div class="option-row">
                <span>{{ agent.name }}</span>
                <el-tag size="small" :type="agent.status === 1 ? 'success' : 'info'">
                  {{ agent.current_version || '未发布' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 状态 -->
        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="启用"
            inactive-text="停用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '立即创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 连接测试弹窗 -->
    <el-dialog
      v-model="testDialogVisible"
      title="WebSocket 连接测试"
      width="560px"
      :close-on-click-modal="false"
      @closed="handleTestClose"
    >
      <div class="test-dialog">
        <!-- 连接信息 -->
        <div class="test-info">
          <div class="test-info-item">
            <span class="test-info-label">渠道：</span>
            <span class="test-info-value">{{ testChannel?.name }}</span>
          </div>
          <div class="test-info-item">
            <span class="test-info-label">WS 地址：</span>
            <code class="test-ws-url">
              ws://localhost:8000/api/v1/chat/ws/{{ testChannel?.channel_token }}
            </code>
          </div>
          <div class="test-info-item">
            <span class="test-info-label">连接状态：</span>
            <el-tag :type="wsStatusType" size="small" round>
              {{ wsStatusText }}
            </el-tag>
          </div>
        </div>

        <!-- 消息记录 -->
        <div class="test-messages" ref="testMessagesRef">
          <div
            v-for="(msg, index) in testMessages"
            :key="index"
            class="test-message"
            :class="`test-message--${msg.role}`"
          >
            <div class="test-message-role">
              {{ msg.role === 'user' ? '我' : msg.role === 'bot' ? 'Bot' : '系统' }}
            </div>
            <div class="test-message-content">{{ msg.content }}</div>
            <div class="test-message-time">{{ msg.time }}</div>
          </div>
          <div v-if="!testMessages.length" class="test-empty">
            连接后发送消息开始测试...
          </div>
        </div>

        <!-- 输入区 -->
        <div class="test-input-wrap">
          <el-input
            v-model="testInput"
            placeholder="输入测试消息，按 Enter 发送"
            :disabled="wsStatus !== 'connected'"
            @keyup.enter="sendTestMessage"
          />
          <el-button
            type="primary"
            :disabled="wsStatus !== 'connected'"
            @click="sendTestMessage"
          >
            发送
          </el-button>
        </div>
      </div>

      <template #footer>
        <el-button
          v-if="wsStatus !== 'connected'"
          type="success"
          :loading="wsStatus === 'connecting'"
          @click="connectTestWs"
        >
          {{ wsStatus === 'connecting' ? '连接中...' : '连接 WebSocket' }}
        </el-button>
        <el-button
          v-else
          type="danger"
          plain
          @click="disconnectTestWs"
        >
          断开连接
        </el-button>
        <el-button @click="testDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 发布接入弹窗 -->
    <ChannelPublish
      v-model="publishVisible"
      :channel="publishChannel"
    />
  </div>
</template>
<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  InfoFilled,
  Promotion,
  Tools,
  MoreFilled,
  Edit,
  CopyDocument,
  CircleClose,
  CircleCheck,
  Delete,
  Service,
  Cpu,
  View,
  ChromeFilled,
  Position,
} from '@element-plus/icons-vue'
import { channelApi, botApi, agentApi } from '@/api/admin'
import ChannelPublish from './ChannelPublish.vue'
import dayjs from 'dayjs'

const router = useRouter()

// ==================== 发布弹窗 ====================
const publishVisible = ref(false)
const publishChannel = ref(null)

function openPublish(channel) {
  publishChannel.value = channel
  publishVisible.value = true
}

// ==================== 列表数据 ====================
const loading     = ref(false)
const channelList = ref([])
const botList     = ref([])
const agentList   = ref([])
const testUserIdMap = ref({})

async function fetchChannelList() {
  loading.value = true
  try {
    const res = await channelApi.getChannels()
    channelList.value = res.data || []
  } catch {
    ElMessage.error('获取渠道列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchBotList() {
  try {
    const res = await botApi.getBots()
    botList.value = res.data || []
  } catch {
    // 不影响主功能
  }
}

async function fetchAgentList() {
  try {
    const res = await agentApi.getAgents()
    agentList.value = res.data || []
  } catch {
    // 不影响主功能
  }
}

// 根据 ID 获取名称
function getBotName(botId) {
  if (!botId) return ''
  return botList.value.find(b => b.id === botId)?.name || `Bot #${botId}`
}

function getAgentName(agentId) {
  if (!agentId) return ''
  return agentList.value.find(a => a.id === agentId)?.name || `Agent #${agentId}`
}

// ==================== Token 处理 ====================
// 掩码显示 Token（保留前8位和后8位）
function maskToken(token) {
  if (!token) return '--'
  if (token.length <= 16) return token
  return `${token.slice(0, 8)}...${token.slice(-8)}`
}

// 复制 Token
async function copyToken(token) {
  try {
    await navigator.clipboard.writeText(token)
    ElMessage.success('Token 已复制到剪贴板')
  } catch {
    // 降级处理
    const input = document.createElement('input')
    input.value = token
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('Token 已复制到剪贴板')
  }
}

// 复制 WS 地址
async function copyWsUrl(token) {
  const url = `ws://localhost:8000/api/v1/chat/ws/${token}`
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('WebSocket 地址已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// ==================== 对话链接 ====================
function getChatUrl(token) {
  const base   = `${window.location.origin}/chat?channel=${token}`
  const testId = testUserIdMap.value[token]
  if (testId) {
    return `${base}&user_id=${testId}`
  }
  return base
}

async function copyChatUrl(token) {
  const url = getChatUrl(token)
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('对话链接已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

function openChatUrl(token) {
  const url = getChatUrl(token)
  window.open(url, '_blank')
}

// ==================== 新建 / 编辑弹窗 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const isEdit        = ref(false)
const editId        = ref(null)
const formRef       = ref(null)

const form = ref({
  name:     '',
  type:     'test',
  bot_id:   null,
  agent_id: null,
  status:   1,
})

const rules = {
  name: [
    { required: true, message: '请输入渠道名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度 2-50 个字符', trigger: 'blur' },
  ],
  type: [
    { required: true, message: '请选择渠道类型', trigger: 'change' },
  ],
  bot_id: [
    { required: true, message: '请选择关联的 Bot', trigger: 'change' },
  ],
  agent_id: [
    { required: true, message: '请选择关联的 Agent', trigger: 'change' },
  ],
}

function openCreateDialog() {
  isEdit.value        = false
  editId.value        = null
  dialogVisible.value = true
}

function openEditDialog(channel) {
  isEdit.value        = true
  editId.value        = channel.id
  form.value.name     = channel.name
  form.value.type     = channel.type
  form.value.bot_id   = channel.bot_id
  form.value.agent_id = channel.agent_id
  form.value.status   = channel.status
  dialogVisible.value = true
}

function resetForm() {
  form.value = {
    name:     '',
    type:     'test',
    bot_id:   null,
    agent_id: null,
    status:   1,
  }
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await channelApi.updateChannel(editId.value, form.value)
        ElMessage.success('修改成功')
      } else {
        await channelApi.createChannel(form.value)
        ElMessage.success('创建成功，系统已自动生成 channel_token')
      }
      dialogVisible.value = false
      fetchChannelList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// ==================== 更多操作 ====================
async function handleCommand(command, channel) {
  if (command === 'edit') {
    openEditDialog(channel)
    return
  }

  if (command === 'copyToken') {
    copyToken(channel.channel_token)
    return
  }

  if (command === 'config') {
    router.push(`/admin/channels/${channel.id}/config`)
    return
  }

  if (command === 'enable' || command === 'disable') {
    const newStatus = command === 'enable' ? 1 : 0
    const label     = command === 'enable' ? '启用' : '停用'
    try {
      await ElMessageBox.confirm(
        `确认要${label}渠道「${channel.name}」吗？`,
        '提示',
        {
          type:              'warning',
          confirmButtonText: '确认',
          cancelButtonText:  '取消',
        }
      )
      await channelApi.updateChannel(channel.id, { status: newStatus })
      ElMessage.success(`已${label}`)
      fetchChannelList()
    } catch {
      // 用户取消不处理
    }
  }

  if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除渠道「${channel.name}」吗？该操作不可恢复。`,
        '删除确认',
        { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
      )
      await channelApi.deleteChannel(channel.id)
      ElMessage.success('删除成功')
      fetchChannelList()
    } catch (e) {
      if (e !== 'cancel') {
        const msg = e?.response?.data?.message || e?.response?.data?.detail || '删除失败'
        ElMessage.error(msg)
      }
    }
  }
}

// ==================== WebSocket 连接测试 ====================
const testDialogVisible = ref(false)
const testChannel       = ref(null)
const testMessages      = ref([])
const testInput         = ref('')
const testMessagesRef   = ref(null)
const wsStatus          = ref('disconnected') // disconnected / connecting / connected
let   testWs            = null

const wsStatusText = computed(() => {
  const map = {
    disconnected: '未连接',
    connecting:   '连接中',
    connected:    '已连接',
  }
  return map[wsStatus.value] || '未知'
})

const wsStatusType = computed(() => {
  const map = {
    disconnected: 'info',
    connecting:   'warning',
    connected:    'success',
  }
  return map[wsStatus.value] || 'info'
})

function openTestDialog(channel) {
  testChannel.value       = channel
  testMessages.value      = []
  testInput.value         = ''
  wsStatus.value          = 'disconnected'
  testDialogVisible.value = true
}

function connectTestWs() {
  if (!testChannel.value) return
  wsStatus.value = 'connecting'

  const token = testChannel.value.channel_token
  // 使用管理员 ID=0 作为测试用户 [2]
  const url   = `ws://localhost:8000/api/v1/chat/ws/${token}?user_id=0`

  testWs = new WebSocket(url)

  testWs.onopen = () => {
    wsStatus.value = 'connected'
    pushSystemMessage('✅ WebSocket 连接成功！')
  }

  testWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'pong') return

      pushMessage({
        role:    'bot',
        content: data.content || JSON.stringify(data),
        time:    data.timestamp || dayjs().format('HH:mm:ss'),
      })
    } catch {
      pushMessage({ role: 'bot', content: event.data, time: dayjs().format('HH:mm:ss') })
    }
  }

  testWs.onerror = () => {
    wsStatus.value = 'disconnected'
    pushSystemMessage('❌ 连接失败，请确认后端服务已启动')
  }

  testWs.onclose = () => {
    wsStatus.value = 'disconnected'
    pushSystemMessage('🔌 连接已断开')
  }
}

function disconnectTestWs() {
  testWs?.close()
  testWs      = null
  wsStatus.value = 'disconnected'
}

function sendTestMessage() {
  const content = testInput.value.trim()
  if (!content || wsStatus.value !== 'connected') return

  // 发送消息 [2]
  testWs.send(JSON.stringify({ type: 'chat', content }))

  pushMessage({
    role:    'user',
    content,
    time:    dayjs().format('HH:mm:ss'),
  })

  testInput.value = ''
}

function pushMessage(msg) {
  testMessages.value.push(msg)
  scrollTestToBottom()
}

function pushSystemMessage(content) {
  testMessages.value.push({
    role:    'system',
    content,
    time:    dayjs().format('HH:mm:ss'),
  })
  scrollTestToBottom()
}

function scrollTestToBottom() {
  nextTick(() => {
    if (testMessagesRef.value) {
      testMessagesRef.value.scrollTop = testMessagesRef.value.scrollHeight
    }
  })
}

function handleTestClose() {
  disconnectTestWs()
  testMessages.value = []
  testChannel.value  = null
}

// ==================== 工具函数 ====================
function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('MM-DD')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchBotList()
  fetchAgentList()
  fetchChannelList()
})

onUnmounted(() => {
  disconnectTestWs()
})
</script>
<style scoped lang="scss">
.channel-list {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.page-sub {
  font-size: 13px;
  color: #909399;
}

// 说明横幅
.tips-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 20px;
  flex-wrap: wrap;

  .el-icon {
    color: #409eff;
    flex-shrink: 0;
    font-size: 16px;
  }

  strong {
    color: #303133;
  }
}

// 渠道卡片网格
.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.channel-empty {
  grid-column: 1 / -1;
}

// 渠道卡片
.channel-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  padding: 20px;
  transition: box-shadow 0.2s, transform 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  // 正式渠道：红色左边框
  &--production {
    border-left: 4px solid #f56c6c;
  }

  // 测试渠道：橙色左边框
  &--test {
    border-left: 4px solid #e6a23c;
  }

  // 新建按钮卡片
  &--add {
    border: 2px dashed #dcdfe6;
    box-shadow: none;
    align-items: center;
    justify-content: center;
    gap: 12px;
    cursor: pointer;
    min-height: 280px;
    color: #c0c4cc;
    transition: all 0.2s;
    border-left: 2px dashed #dcdfe6;

    &:hover {
      border-color: #5b8af5;
      color: #5b8af5;
      transform: translateY(-2px);
      box-shadow: none;
    }
  }
}

.add-icon {
  transition: transform 0.2s;

  .channel-card--add:hover & {
    transform: rotate(90deg);
  }
}

.add-text {
  font-size: 14px;
  font-weight: 500;
}

// 卡片头部
.channel-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.channel-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;

  &.icon--production {
    background: rgba(245, 108, 108, 0.1);
    color: #f56c6c;
  }

  &.icon--test {
    background: rgba(230, 162, 60, 0.1);
    color: #e6a23c;
  }
}

.channel-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

// 渠道名称
.channel-name {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Token 展示
.channel-token-wrap {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.token-label {
  font-size: 11px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.token-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.token-value {
  flex: 1;
  font-size: 12px;
  color: #5b8af5;
  font-family: 'Courier New', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(91, 138, 245, 0.06);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(91, 138, 245, 0.15);
}

// 关联配置
.channel-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 12px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  width: 72px;

  .el-icon {
    font-size: 13px;
  }
}

// WS 地址
.ws-url-wrap {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f0f9eb;
  border: 1px solid #d9f0c8;
  border-radius: 8px;
}

.ws-url-label {
  font-size: 11px;
  color: #67c23a;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.ws-url-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ws-url {
  flex: 1;
  font-size: 11px;
  color: #529b2e;
  font-family: 'Courier New', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-link-wrap {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f0f9eb;
  border: 1px solid #d9f0c8;
  border-radius: 8px;
}

.chat-link-label {
  font-size: 11px;
  color: #67c23a;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.chat-link-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-link-url {
  flex: 1;
  font-size: 11px;
  color: #529b2e;
  font-family: 'Courier New', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.test-user-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.test-user-label {
  font-size: 12px;
  color: #606266;
  flex-shrink: 0;
}

.test-user-hint {
  font-size: 11px;
  color: #c0c4cc;
}

// 统计数据
.channel-stats {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 0;
  margin-bottom: 14px;
}

.channel-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.channel-stat-divider {
  width: 1px;
  height: 28px;
  background: #e4e7ed;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

// 卡片底部操作
.channel-card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid #f5f7fa;
  flex-wrap: wrap;
}

// 表单
.channel-form {
  padding: 8px 0;
}

// 渠道类型提示
.type-hint {
  margin-top: 8px;

  .hint-text {
    font-size: 12px;
    color: #909399;
    line-height: 1.6;
  }
}

// 下拉选项行
.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

// 连接测试弹窗
.test-dialog {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.test-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
}

.test-info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}

.test-info-label {
  color: #909399;
  flex-shrink: 0;
}

.test-info-value {
  color: #303133;
  font-weight: 500;
}

.test-ws-url {
  font-size: 11px;
  color: #5b8af5;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

// 消息记录区
.test-messages {
  height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.test-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #c0c4cc;
}

.test-message {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 80%;

  &--user {
    align-self: flex-end;
    align-items: flex-end;

    .test-message-content {
      background: #5b8af5;
      color: #ffffff;
      border-radius: 12px 12px 2px 12px;
    }
  }

  &--bot {
    align-self: flex-start;
    align-items: flex-start;

    .test-message-content {
      background: #ffffff;
      color: #303133;
      border: 1px solid #e4e7ed;
      border-radius: 12px 12px 12px 2px;
    }
  }

  &--system {
    align-self: center;
    align-items: center;

    .test-message-content {
      background: rgba(230, 162, 60, 0.1);
      color: #e6a23c;
      border-radius: 8px;
      font-size: 12px;
    }
  }
}

.test-message-role {
  font-size: 11px;
  color: #c0c4cc;
  padding: 0 4px;
}

.test-message-content {
  font-size: 13px;
  padding: 8px 12px;
  line-height: 1.5;
  word-break: break-word;
}

.test-message-time {
  font-size: 10px;
  color: #c0c4cc;
  padding: 0 4px;
}

// 输入区
.test-input-wrap {
  display: flex;
  gap: 10px;
}
</style>