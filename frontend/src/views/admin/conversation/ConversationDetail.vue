<template>
  <div class="conversation-detail">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">会话详情</h2>
          <span class="page-sub">会话 #{{ convId }}</span>
        </div>
      </div>
      <div class="page-header-right">
        <el-tag
          v-if="conversation"
          :type="getStatusType(conversation.status)"
          size="large"
          round
        >
          {{ getStatusLabel(conversation.status) }}
        </el-tag>
      </div>
    </div>

    <div v-loading="loading" class="detail-layout">
      <el-row :gutter="16">

        <!-- 左侧：消息记录 -->
        <el-col :span="16">
          <div class="messages-card">
            <div class="messages-card-header">
              <span class="card-title">消息记录</span>
              <span class="msg-total">共 {{ messages.length }} 条</span>
            </div>

            <!-- 消息列表 -->
            <div class="messages-body" ref="messagesBodyRef">
              <template v-if="messages.length">
                <div
                  v-for="msg in messages"
                  :key="msg.id"
                  class="msg-item"
                  :class="`msg-item--${msg.role}`"
                >
                  <!-- 用户消息 -->
                  <template v-if="msg.role === 0">
                    <div class="msg-row msg-row--right">
                      <div class="msg-main">
                        <div class="msg-meta msg-meta--right">
                          <span class="msg-sender">用户</span>
                          <span class="msg-time">{{ formatDateFull(msg.created_at) }}</span>
                        </div>
                        <div class="msg-bubble msg-bubble--user">
                          {{ msg.content }}
                        </div>
                      </div>
                      <el-avatar :size="36" class="msg-avatar avatar--user">
                        U
                      </el-avatar>
                    </div>
                  </template>

                  <!-- Bot / Agent 消息 (role 1=bot, 2=agent) -->
                  <template v-else-if="msg.role === 1 || msg.role === 2">
                    <div class="msg-row msg-row--left">
                      <el-avatar
                        :size="36"
                        :class="['msg-avatar', msg.role === 1 ? 'avatar--bot' : 'avatar--agent']"
                      >
                        {{ msg.role === 1 ? 'B' : 'A' }}
                      </el-avatar>
                      <div class="msg-main">
                        <div class="msg-meta msg-meta--left">
                          <span class="msg-sender">
                            {{ msg.role === 1 ? 'Bot' : '人工客服' }}
                          </span>
                          <span class="msg-time">{{ formatDateFull(msg.created_at) }}</span>

                          <!-- 意图标签 -->
                          <el-tag
                            v-if="msg.extra?.intent"
                            size="small"
                            :type="getIntentType(msg.extra.intent)"
                            effect="plain"
                          >
                            {{ getIntentLabel(msg.extra.intent) }}
                          </el-tag>

                          <!-- 情绪标签 -->
                          <span
                            v-if="msg.extra?.emotion"
                            class="emotion-tag"
                            :class="`emotion--${msg.extra.emotion}`"
                          >
                            {{ getEmotionLabel(msg.extra.emotion) }}
                          </span>

                          <!-- 来源标签 -->
                          <el-tag
                            v-if="msg.extra?.answer_source"
                            size="small"
                            :type="getSourceType(msg.extra.answer_source)"
                          >
                            {{ getSourceLabel(msg.extra.answer_source) }}
                          </el-tag>
                        </div>

                        <div class="msg-bubble msg-bubble--bot">
                          {{ msg.content }}
                        </div>

                        <!-- 标注按钮（仅 bot/agent 消息显示）-->
                        <div class="msg-actions" style="margin-top:6px; display:flex !important; opacity:1 !important; visibility:visible !important">
                          <el-button
                            text
                            size="small"
                            style="color:#5b8af5;font-size:12px; display:inline-flex !important"
                            @click.stop="openAnnotationDialog(msg)"
                          >
                            {{ annotationMap[msg.id] ? '✅ 已标注' : '📌 标注此回复' }}
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </template>

                  <!-- 系统消息 -->
                  <template v-else-if="msg.role === 2">
                    <div class="msg-system">
                      <div class="system-line"></div>
                      <div class="system-content">
                        <el-icon><InfoFilled /></el-icon>
                        {{ msg.content }}
                        <span class="system-time">
                          {{ formatDateFull(msg.created_at) }}
                        </span>
                      </div>
                      <div class="system-line"></div>
                    </div>
                  </template>
                </div>
              </template>

              <!-- 空状态 -->
              <el-empty
                v-else-if="!loading"
                description="暂无消息记录"
                :image-size="80"
              />
            </div>
          </div>
        </el-col>

        <!-- 右侧：会话信息 + 分析 -->
        <el-col :span="8">

          <!-- 会话基础信息 -->
          <div class="info-card" v-if="conversation">
            <div class="info-card-title">会话信息</div>
            <div class="info-grid">
              <div class="info-row">
                <span class="info-label">会话 ID</span>
                <span class="info-value">#{{ conversation.id }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">用户</span>
                <div class="info-value user-info">
                  <el-avatar :size="22" class="mini-avatar">
                    {{ (conversation.username || conversation.user_id)
                        ?.toString().charAt(0).toUpperCase() }}
                  </el-avatar>
                  <span>
                    {{ conversation.username || `用户${conversation.user_id}` }}
                  </span>
                </div>
              </div>
              <div class="info-row">
                <span class="info-label">渠道</span>
                <el-tag size="small" effect="plain">
                  {{ conversation.channel_name || `渠道${conversation.channel_id}` }}
                </el-tag>
              </div>
              <div class="info-row">
                <span class="info-label">状态</span>
                <el-tag
                  :type="getStatusType(conversation.status)"
                  size="small"
                  round
                >
                  {{ getStatusLabel(conversation.status) }}
                </el-tag>
              </div>
              <div class="info-row">
                <span class="info-label">消息数</span>
                <span class="info-value">{{ messages.length }} 条</span>
              </div>
              <div class="info-row">
                <span class="info-label">开始时间</span>
                <span class="info-value time-value">
                  {{ formatDateFull(conversation.created_at) }}
                </span>
              </div>
              <div class="info-row" v-if="conversation.closed_at">
                <span class="info-label">结束时间</span>
                <span class="info-value time-value">
                  {{ formatDateFull(conversation.closed_at) }}
                </span>
              </div>
              <div class="info-row" v-if="conversation.closed_at">
                <span class="info-label">持续时长</span>
                <span class="info-value">
                  {{ calcDuration(conversation.created_at, conversation.closed_at) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 意图分布 -->
          <div class="info-card" v-if="intentStats.length">
            <div class="info-card-title">意图分布</div>
            <div class="intent-list">
              <div
                v-for="item in intentStats"
                :key="item.intent"
                class="intent-item"
              >
                <div class="intent-item-header">
                  <el-tag
                    :type="getIntentType(item.intent)"
                    size="small"
                    effect="plain"
                  >
                    {{ getIntentLabel(item.intent) }}
                  </el-tag>
                  <span class="intent-count">{{ item.count }} 次</span>
                </div>
                <el-progress
                  :percentage="Math.round((item.count / messages.length) * 100)"
                  :color="getIntentColor(item.intent)"
                  :stroke-width="5"
                  :show-text="false"
                />
              </div>
            </div>
          </div>

          <!-- 情绪走势 -->
          <div class="info-card" v-if="emotionStats">
            <div class="info-card-title">情绪分析</div>
            <div class="emotion-stats">
              <div
                v-for="(count, emotion) in emotionStats"
                :key="emotion"
                class="emotion-stat-item"
              >
                <span class="emotion-tag" :class="`emotion--${emotion}`">
                  {{ getEmotionLabel(emotion) }}
                </span>
                <span class="emotion-count">{{ count }} 次</span>
              </div>
            </div>
          </div>

          <!-- 回答来源分布 -->
          <div class="info-card" v-if="sourceStats.length">
            <div class="info-card-title">回答来源</div>
            <div class="source-list">
              <div
                v-for="item in sourceStats"
                :key="item.source"
                class="source-item"
              >
                <div class="source-item-header">
                  <el-tag
                    :type="getSourceType(item.source)"
                    size="small"
                  >
                    {{ getSourceLabel(item.source) }}
                  </el-tag>
                  <span class="source-count">{{ item.count }} 次</span>
                </div>
                <el-progress
                  :percentage="item.rate"
                  :color="getSourceColor(item.source)"
                  :stroke-width="5"
                  :show-text="false"
                />
              </div>
            </div>
          </div>

          <!-- 用户评价 -->
          <div class="info-card" v-if="conversation?.rating">
            <div class="info-card-title">用户评价</div>
            <div class="rating-section">
              <el-rate
                v-model="conversation.rating"
                disabled
                :max="5"
                style="margin-bottom: 10px"
              />
              <div class="rating-tags" v-if="conversation.rating_tags?.length">
                <el-tag
                  v-for="tag in conversation.rating_tags"
                  :key="tag"
                  size="small"
                  type="success"
                  effect="plain"
                  style="margin-right: 6px; margin-bottom: 6px"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <div class="rating-remark" v-if="conversation.rating_remark">
                {{ conversation.rating_remark }}
              </div>
            </div>
          </div>

        </el-col>
      </el-row>
    </div>

    <!-- 新增标注弹窗 -->
    <el-dialog
      v-model="annotationDialogVisible"
      title="新增标注"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetAnnotationForm"
    >
      <!-- 原始消息预览 -->
      <div class="annotation-preview" v-if="annotatingMsg">
        <div class="preview-header">
          <el-icon><ChatDotRound /></el-icon>
          <span>被标注的消息</span>
        </div>
        <div class="preview-body">
          {{ annotatingMsg.content }}
        </div>
        <!-- 已有标注提示 -->
        <div class="existing-annotation" v-if="annotationMap[annotatingMsg.id]">
          <el-icon><InfoFilled /></el-icon>
          <span>该消息已有标注，提交后将覆盖</span>
          <el-tag
            :type="getLabelType(annotationMap[annotatingMsg.id].label)"
            size="small"
            round
          >
            {{ getLabelText(annotationMap[annotatingMsg.id].label) }}
          </el-tag>
        </div>
      </div>

      <!-- 标注表单 -->
      <el-form
        ref="annotationFormRef"
        :model="annotationForm"
        :rules="annotationRules"
        label-width="90px"
        style="margin-top: 16px"
      >
        <!-- 标注结果 -->
        <el-form-item label="标注结果" prop="label">
          <el-radio-group v-model="annotationForm.label" size="large">
            <el-radio-button label="good">
              <div class="label-option">
                <span class="label-emoji">👍</span>
                <span>好的回答</span>
              </div>
            </el-radio-button>
            <el-radio-button label="neutral">
              <div class="label-option">
                <span class="label-emoji">😐</span>
                <span>中性</span>
              </div>
            </el-radio-button>
            <el-radio-button label="bad">
              <div class="label-option">
                <span class="label-emoji">👎</span>
                <span>差的回答</span>
              </div>
            </el-radio-button>
          </el-radio-group>

          <!-- 标注说明 -->
          <div class="label-hint">
            <span v-if="annotationForm.label === 'good'" class="hint-good">
              ✅ 回答准确、完整，用户问题得到有效解决
            </span>
            <span v-else-if="annotationForm.label === 'neutral'" class="hint-neutral">
              😐 回答基本正确但不够完善，或与问题关联度一般
            </span>
            <span v-else-if="annotationForm.label === 'bad'" class="hint-bad">
              ❌ 回答错误、不相关或无法解决用户问题，请填写修正答案
            </span>
          </div>
        </el-form-item>

        <!-- 修正答案（差评时必填）-->
        <el-form-item
          label="修正答案"
          prop="correct_answer"
          v-if="annotationForm.label === 'bad'"
        >
          <el-input
            v-model="annotationForm.correct_answer"
            type="textarea"
            placeholder="请输入正确的回答内容，将用于后续模型微调训练"
            :rows="4"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <!-- 备注 -->
        <el-form-item label="标注备注">
          <el-input
            v-model="annotationForm.remark"
            placeholder="可选，描述标注原因或补充说明"
            maxlength="200"
            show-word-limit
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="annotationDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submittingAnnotation"
          @click="handleAnnotationSubmit"
        >
          {{ annotationMap[annotatingMsg?.id] ? '更新标注' : '提交标注' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  InfoFilled,
  CreditCard,
  ChatDotRound,
  Collection,
  EditPen,
} from '@element-plus/icons-vue'
import { conversationApi } from '@/api/admin'
import { annotationApi } from '@/api/admin'
import dayjs from 'dayjs'

const route  = useRoute()
const router = useRouter()

const convId = computed(() => Number(route.params.id))

// ==================== 数据加载 ====================
const loading      = ref(false)
const conversation = ref(null)
const messages     = ref([])
const messagesBodyRef = ref(null)

async function fetchDetail() {
  loading.value = true
  try {
    // 同时拉取会话信息和消息记录
    const [convRes, msgRes] = await Promise.all([
      conversationApi.getConversations({ id: convId.value }),
      conversationApi.getMessages(convId.value),
    ])

    // 从列表中找到当前会话
    const list = convRes.data || []
    conversation.value = list.find(c => c.id === convId.value) || null

    messages.value = msgRes.data || []

    await loadAnnotations(messages.value)

    await nextTick()
    scrollToBottom()
  } catch {
    ElMessage.error('获取会话详情失败')
  } finally {
    loading.value = false
  }
}

function scrollToBottom() {
  if (messagesBodyRef.value) {
    messagesBodyRef.value.scrollTop = messagesBodyRef.value.scrollHeight
  }
}

// ==================== 统计分析 ====================

// 意图分布（从 bot 消息的 extra 中统计）
const intentStats = computed(() => {
  const map = {}
  messages.value.forEach(msg => {
    if (msg.extra?.intent) {
      map[msg.extra.intent] = (map[msg.extra.intent] || 0) + 1
    }
  })
  return Object.entries(map)
    .map(([intent, count]) => ({ intent, count }))
    .sort((a, b) => b.count - a.count)
})

// 情绪分布
const emotionStats = computed(() => {
  const map = {}
  messages.value.forEach(msg => {
    if (msg.extra?.emotion) {
      map[msg.extra.emotion] = (map[msg.extra.emotion] || 0) + 1
    }
  })
  return Object.keys(map).length ? map : null
})

// 回答来源分布
const sourceStats = computed(() => {
  const map = {}
  const botMsgs = messages.value.filter(m => m.role === 1)
  botMsgs.forEach(msg => {
    if (msg.extra?.answer_source) {
      map[msg.extra.answer_source] = (map[msg.extra.answer_source] || 0) + 1
    }
  })
  const total = botMsgs.length || 1
  return Object.entries(map)
    .map(([source, count]) => ({
      source,
      count,
      rate: Math.round((count / total) * 100),
    }))
    .sort((a, b) => b.count - a.count)
})

// ==================== 状态标签 ====================
function getStatusLabel(status) {
  const map = {
    active:      '进行中',
    closed:      '已结束',
    transferred: '已转人工',
  }
  return map[status] || status || '未知'
}

function getStatusType(status) {
  const map = {
    active:      'success',
    closed:      'info',
    transferred: 'warning',
  }
  return map[status] || 'info'
}

// ==================== 意图标签 ====================
const INTENT_MAP = {
  order_query:     '订单查询',
  logistics_query: '物流查询',
  refund_request:  '退款申请',
  product_query:   '商品咨询',
  complaint:       '投诉',
  greeting:        '打招呼',
  other:           '其他',
}

function getIntentLabel(intent) {
  return INTENT_MAP[intent] || intent
}

function getIntentType(intent) {
  const map = {
    order_query:     'primary',
    logistics_query: 'success',
    refund_request:  'danger',
    product_query:   'warning',
    complaint:       'danger',
    greeting:        'info',
    other:           'info',
  }
  return map[intent] || 'info'
}

function getIntentColor(intent) {
  const map = {
    order_query:     '#5b8af5',
    logistics_query: '#67c23a',
    refund_request:  '#f56c6c',
    product_query:   '#e6a23c',
    complaint:       '#f56c6c',
    greeting:        '#909399',
    other:           '#909399',
  }
  return map[intent] || '#909399'
}

// ==================== 情绪标签 ====================
function getEmotionLabel(emotion) {
  const map = {
    neutral:  '😊 平静',
    negative: '😞 消极',
    angry:    '😡 激动',
  }
  return map[emotion] || emotion
}

// ==================== 来源标签 ====================
function getSourceLabel(source) {
  const map = {
    rag:     'RAG 检索',
    tool:    '工具调用',
    llm:     'LLM 生成',
    keyword: '关键词',
    default: '兜底回复',
  }
  return map[source] || source
}

function getSourceType(source) {
  const map = {
    rag:     'primary',
    tool:    'success',
    llm:     'warning',
    keyword: 'danger',
    default: 'info',
  }
  return map[source] || 'info'
}

function getSourceColor(source) {
  const map = {
    rag:     '#5b8af5',
    tool:    '#67c23a',
    llm:     '#e6a23c',
    keyword: '#f56c6c',
    default: '#909399',
  }
  return map[source] || '#909399'
}

// ==================== 卡片类型标签 ====================
function getCardTypeLabel(cardType) {
  const map = {
    order:      '订单卡片',
    order_list: '订单列表卡片',
    logistics:  '物流卡片',
    product:    '商品卡片',
  }
  return map[cardType] || cardType
}

// ==================== 工具函数 ====================
function formatDateFull(dateStr) {
  if (!dateStr) return '--'
  const isoStr = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z'
  return dayjs(isoStr).format('YYYY-MM-DD HH:mm:ss')
}

// 计算持续时长
function calcDuration(start, end) {
  if (!start || !end) return '--'
  const diff = dayjs(end).diff(dayjs(start), 'second')
  if (diff < 60)   return `${diff} 秒`
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟`
  return `${Math.floor(diff / 3600)} 小时 ${Math.floor((diff % 3600) / 60)} 分钟`
}

// ==================== 标注相关 ====================
const annotationMap           = ref({})
const annotationDialogVisible = ref(false)
const submittingAnnotation    = ref(false)
const annotatingMsg           = ref(null)
const annotationFormRef       = ref(null)

const annotationForm = ref({
  label:          'good',
  correct_answer: '',
  remark:         '',
})

const annotationRules = {
  label: [
    { required: true, message: '请选择标注结果', trigger: 'change' },
  ],
  correct_answer: [
    {
      validator: (rule, value, callback) => {
        if (annotationForm.value.label === 'bad' && !value?.trim()) {
          callback(new Error('差评标注必须填写修正答案'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function loadAnnotations(msgList) {
  if (!msgList?.length) return
  const botMsgIds = msgList
    .filter(m => m.role === 'bot' || m.role === 'agent')
    .map(m => m.id)
  if (!botMsgIds.length) return
  const results = await Promise.allSettled(
    botMsgIds.map(id => annotationApi.getByMessage(id))
  )
  const map = {}
  results.forEach((result, index) => {
    if (result.status === 'fulfilled' && result.value?.data) {
      map[botMsgIds[index]] = result.value.data
    }
  })
  annotationMap.value = map
}

function openAnnotationDialog(msg) {
  annotatingMsg.value = msg
  const existing = annotationMap.value[msg.id]
  if (existing) {
    annotationForm.value.label          = existing.label          || 'good'
    annotationForm.value.correct_answer = existing.correct_answer || ''
    annotationForm.value.remark         = existing.remark         || ''
  } else {
    annotationForm.value.label          = 'good'
    annotationForm.value.correct_answer = ''
    annotationForm.value.remark         = ''
  }
  annotationDialogVisible.value = true
}

function resetAnnotationForm() {
  annotationForm.value = { label: 'good', correct_answer: '', remark: '' }
  annotationFormRef.value?.clearValidate()
  annotatingMsg.value = null
}

async function handleAnnotationSubmit() {
  await annotationFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submittingAnnotation.value = true
    try {
      await annotationApi.create({
        conversation_id: convId.value,
        message_id:      annotatingMsg.value.id,
        label:           annotationForm.value.label,
        correct_answer:  annotationForm.value.label === 'bad'
                           ? annotationForm.value.correct_answer
                           : null,
        remark:          annotationForm.value.remark || null,
      })
      ElMessage.success('标注已保存')
      annotationDialogVisible.value = false
      await loadAnnotations(messages.value)
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '标注提交失败')
    } finally {
      submittingAnnotation.value = false
    }
  })
}

function getAnnotationBtnType(msgId) {
  const record = annotationMap.value[msgId]
  if (!record) return 'default'
  const typeMap = { good: 'success', bad: 'danger', neutral: 'warning' }
  return typeMap[record.label] || 'default'
}

function getLabelType(label) {
  const map = { good: 'success', bad: 'danger', neutral: 'warning' }
  return map[label] || 'info'
}

function getLabelText(label) {
  const map = { good: '👍 好的回答', bad: '👎 差的回答', neutral: '😐 中性' }
  return map[label] || label
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchDetail()
})
</script>
<style scoped lang="scss">
.conversation-detail {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 2px;
}

.page-sub {
  font-size: 12px;
  color: #909399;
}

.page-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

// 整体布局
.detail-layout {
  min-height: 600px;
}

// 消息卡片
.messages-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 500px;
  overflow: hidden;
}

.messages-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f5f7fa;
  flex-shrink: 0;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.msg-total {
  font-size: 12px;
  color: #909399;
}

// 消息列表体
.messages-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

// 消息行
.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;

  &--right {
    flex-direction: row-reverse;
  }

  &--left {
    flex-direction: row;
  }
}

.msg-avatar {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 700;

  &.avatar--user {
    background: linear-gradient(135deg, #5b8af5, #3d6fd4);
    color: #ffffff;
  }

  &.avatar--bot {
    background: linear-gradient(135deg, #67c23a, #4fa021);
    color: #ffffff;
  }

  &.avatar--agent {
    background: linear-gradient(135deg, #e6a23c, #c88a1e);
    color: #ffffff;
  }
}

.msg-main {
  flex: 1;
  min-width: 0;
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

// 消息元信息
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;

  &--right {
    flex-direction: row-reverse;
  }

  &--left {
    flex-direction: row;
  }
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

// 情绪标签
.emotion-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;

  &.emotion--neutral {
    background: rgba(144, 147, 153, 0.1);
    color: #909399;
  }

  &.emotion--negative {
    background: rgba(230, 162, 60, 0.1);
    color: #e6a23c;
  }

  &.emotion--angry {
    background: rgba(245, 108, 108, 0.1);
    color: #f56c6c;
  }
}

// 消息气泡
.msg-bubble {
  font-size: 13px;
  line-height: 1.65;
  padding: 10px 14px;
  border-radius: 4px;
  word-break: break-word;
  white-space: pre-wrap;

  &--user {
    background: #5b8af5;
    color: #ffffff;
    border-radius: 12px 12px 2px 12px;
    align-self: flex-end;
  }

  &--bot {
    background: #f5f7fa;
    color: #303133;
    border-radius: 12px 12px 12px 2px;
    border: 1px solid #e4e7ed;
    align-self: flex-start;
  }
}

// 卡片消息提示
.msg-card-preview {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(91, 138, 245, 0.06);
  border: 1px dashed #b3d8ff;
  border-radius: 6px;
  font-size: 12px;
  color: #5b8af5;
  margin-top: 4px;

  .el-icon {
    font-size: 14px;
  }
}

// 系统消息
.msg-system {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.system-line {
  flex: 1;
  height: 1px;
  background: #f0f0f0;
}

.system-content {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  flex-shrink: 0;

  .el-icon {
    color: #c0c4cc;
  }
}

.system-time {
  color: #c0c4cc;
  margin-left: 4px;
}

// 右侧信息卡片
.info-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 16px 18px;
  margin-bottom: 14px;
}

.info-card-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f5f7fa;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 24px;
}

.info-label {
  font-size: 12px;
  color: #909399;
  width: 64px;
  flex-shrink: 0;
}

.info-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.time-value {
  font-size: 11px;
  color: #606266;
  font-weight: 400;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mini-avatar {
  background: linear-gradient(135deg, #5b8af5, #3d6fd4);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
}

// 意图分布
.intent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.intent-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.intent-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.intent-count {
  font-size: 12px;
  color: #909399;
}

// 情绪统计
.emotion-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.emotion-stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.emotion-count {
  font-size: 12px;
  color: #909399;
}

// 来源统计
.source-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.source-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.source-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.source-count {
  font-size: 12px;
  color: #909399;
}

// 用户评价
.rating-section {
  display: flex;
  flex-direction: column;
}

.rating-tags {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.rating-remark {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  padding: 8px 10px;
  background: #f5f7fa;
  border-radius: 6px;
  font-style: italic;
}

// ==================== 标注相关样式 ====================

// 消息操作按钮区
.msg-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 5px;
}

.annotate-btn {
  font-size: 12px;
  padding: 2px 8px;
  height: 24px;
  border-radius: 12px;
}

// 标注弹窗预览
.annotation-preview {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 14px;
  border-left: 3px solid #5b8af5;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  .el-icon {
    color: #5b8af5;
  }
}

.preview-body {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 80px;
  overflow-y: auto;
  margin-bottom: 8px;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.existing-annotation {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #e6a23c;

  .el-icon {
    flex-shrink: 0;
  }
}

.label-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
}

.label-emoji {
  font-size: 20px;
  line-height: 1;
}

.label-hint {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;

  .hint-good    { color: #67c23a; }
  .hint-neutral { color: #909399; }
  .hint-bad     { color: #f56c6c; }
}
</style>