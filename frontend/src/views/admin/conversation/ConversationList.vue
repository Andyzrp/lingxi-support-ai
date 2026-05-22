<template>
  <div class="conversation-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">会话记录</h2>
        <span class="page-sub">共 {{ total }} 条会话记录</span>
      </div>
      <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="filterConvId"
        placeholder="会话 ID"
        clearable
        style="width: 120px"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      />

      <el-input
        v-model="filterUser"
        placeholder="用户搜索"
        clearable
        style="width: 140px"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      />

      <el-select
        v-model="filterChannel"
        placeholder="全部渠道"
        clearable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option
          v-for="ch in channelOptions"
          :key="ch.id"
          :label="ch.name"
          :value="ch.id"
        />
      </el-select>

      <el-select
        v-model="filterStatus"
        placeholder="全部状态"
        clearable
        style="width: 140px"
        @change="handleSearch"
      >
        <el-option label="进行中" value="active" />
        <el-option label="已结束" value="closed" />
        <el-option label="已转人工" value="transferred" />
      </el-select>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 260px"
        @change="handleSearch"
      />

      <el-button type="primary" :icon="Search" @click="handleSearch">
        搜索
      </el-button>
      <el-button :icon="Refresh" @click="handleReset">重置</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stat-row">
      <el-col :span="6">
        <div class="stat-card stat-card--blue">
          <div class="stat-icon"><el-icon :size="22"><ChatDotRound /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总会话数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--green">
          <div class="stat-icon"><el-icon :size="22"><CircleCheck /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.bot_resolved || 0 }}</div>
            <div class="stat-label">Bot 解决</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--orange">
          <div class="stat-icon"><el-icon :size="22"><Cpu /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.agent_resolved || 0 }}</div>
            <div class="stat-label">Agent 解决</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--red">
          <div class="stat-icon"><el-icon :size="22"><User /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.transferred || 0 }}</div>
            <div class="stat-label">转人工</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 表格 -->
    <div class="table-wrap" v-loading="loading">
      <el-table
        :data="convList"
        border
        stripe
        row-key="id"
        style="width: 100%"
        @row-click="openDetailDrawer"
      >
        <!-- 会话 ID -->
        <el-table-column label="会话 ID" width="90" align="center">
          <template #default="{ row }">
            <span class="conv-id">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <!-- 用户信息 -->
        <el-table-column label="用户" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="28" class="user-avatar">
                {{ (row.username || row.user_id)?.toString().charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ row.username || `用户${row.user_id}` }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 渠道 -->
        <el-table-column label="渠道" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.channel_type === 'production' ? 'danger' : 'warning'"
              size="small"
              effect="plain"
            >
              {{ row.channel_name || `渠道${row.channel_id}` }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 会话状态 -->
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
              round
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 最后意图 -->
        <el-table-column label="意图" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.last_intent"
              :type="getIntentType(row.last_intent)"
              size="small"
              effect="plain"
            >
              {{ getIntentLabel(row.last_intent) }}
            </el-tag>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <!-- 情绪 -->
        <el-table-column label="情绪" width="90" align="center">
          <template #default="{ row }">
            <span
              v-if="row.last_emotion"
              class="emotion-tag"
              :class="`emotion--${row.last_emotion}`"
            >
              {{ getEmotionLabel(row.last_emotion) }}
            </span>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <!-- 消息数 -->
        <el-table-column label="消息数" width="80" align="center">
          <template #default="{ row }">
            <el-badge
              :value="row.message_count"
              :type="row.message_count > 10 ? 'danger' : 'primary'"
            />
          </template>
        </el-table-column>

        <!-- 回答来源 -->
        <el-table-column label="回答来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.answer_source"
              :type="getSourceType(row.answer_source)"
              size="small"
            >
              {{ getSourceLabel(row.answer_source) }}
            </el-tag>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <!-- 评分 -->
        <el-table-column label="评分" width="100" align="center">
          <template #default="{ row }">
            <el-rate
              v-if="row.rating"
              v-model="row.rating"
              disabled
              :max="5"
              size="small"
            />
            <span v-else class="text-placeholder">未评价</span>
          </template>
        </el-table-column>

        <!-- 开始时间 -->
        <el-table-column label="开始时间" width="160" align="center">
          <template #default="{ row }">
            <span class="text-time">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :icon="View"
              @click.stop="openDetailDrawer(row)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @change="fetchList"
        />
      </div>
    </div>

    <!-- 会话详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="会话详情"
      size="560px"
      direction="rtl"
      :destroy-on-close="true"
    >
      <div v-if="currentConv" class="drawer-content">
        <!-- 基础信息 -->
        <div class="detail-section">
          <div class="detail-section-title">基础信息</div>
          <div class="detail-grid">
            <div class="detail-row">
              <span class="detail-label">会话 ID</span>
              <span class="detail-value">#{{ currentConv.id }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">用户</span>
              <span class="detail-value">
                {{ currentConv.username || `用户${currentConv.user_id}` }}
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">渠道</span>
              <el-tag size="small" effect="plain">
                {{ currentConv.channel_name || `渠道${currentConv.channel_id}` }}
              </el-tag>
            </div>
            <div class="detail-row" v-if="currentConv.bot_name">
              <span class="detail-label">Bot</span>
              <el-tag size="small" type="success" effect="plain">
                🤖 {{ currentConv.bot_name }}
              </el-tag>
            </div>
            <div class="detail-row" v-if="currentConv.agent_name">
              <span class="detail-label">Agent</span>
              <el-tag size="small" type="warning" effect="plain">
                🧠 {{ currentConv.agent_name }}
              </el-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态</span>
              <el-tag :type="getStatusType(currentConv.status)" size="small" round>
                {{ getStatusLabel(currentConv.status) }}
              </el-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">消息数</span>
              <span class="detail-value">{{ currentConv.message_count }} 条</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">开始时间</span>
              <span class="detail-value">{{ formatDateFull(currentConv.created_at) }}</span>
            </div>
            <div class="detail-row" v-if="currentConv.closed_at">
              <span class="detail-label">结束时间</span>
              <span class="detail-value">{{ formatDateFull(currentConv.closed_at) }}</span>
            </div>
            <div class="detail-row" v-if="currentConv.rating">
              <span class="detail-label">用户评分</span>
              <el-rate v-model="currentConv.rating" disabled size="small" />
            </div>
          </div>
        </div>

        <!-- 消息记录 -->
        <div class="detail-section" style="flex:1;display:flex;flex-direction:column;overflow:hidden">
          <div class="detail-section-title">
            消息记录
            <span class="msg-count">（{{ messages.length }} 条）</span>
          </div>

          <div v-loading="loadingMessages" class="messages-wrap">
            <template v-if="messages.length">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="msg-item"
                :class="msg.role === 0 ? 'msg-item--user' : 'msg-item--bot'"
              >
                <!-- 用户消息（左侧）-->
                <template v-if="msg.role === 0">
                  <div class="msg-row msg-row--left">
                    <img :src="USER_AVATAR_SVG" class="msg-avatar" alt="用户" />
                    <div class="msg-main">
                      <div class="msg-meta msg-meta--left">
                        <span class="msg-sender">用户</span>
                        <span class="msg-time">{{ formatDateFull(msg.created_at) }}</span>
                      </div>
                      <div class="msg-bubble msg-bubble--user" v-html="msg.content"></div>
                    </div>
                  </div>
                </template>

                <!-- Bot 消息（左侧气泡，右侧头像）-->
                <template v-else-if="msg.role === 1">
                  <div class="msg-row">
                    <div class="msg-main msg-main--bot">
                      <div class="msg-meta msg-meta--right">
                        <span class="msg-sender">智能客服</span>
                        <span class="msg-time">{{ formatDateFull(msg.created_at) }}</span>
                        <el-tag v-if="msg.extra?.intent" size="small" :type="getIntentType(msg.extra.intent)" effect="plain">
                          {{ getIntentLabel(msg.extra.intent) }}
                        </el-tag>
                        <span v-if="msg.extra?.emotion" class="emotion-tag" :class="`emotion--${msg.extra.emotion}`">
                          {{ getEmotionLabel(msg.extra.emotion) }}
                        </span>
                        <el-tag v-if="msg.extra?.answer_source" size="small" :type="getSourceType(msg.extra.answer_source)">
                          {{ getSourceLabel(msg.extra.answer_source) }}
                        </el-tag>
                      </div>
                      <div class="msg-bubble msg-bubble--bot" v-html="msg.content"></div>
                      <OrderCard
                        v-if="(msg.extra?.card_type || msg.card_type) === 'order'"
                        :data="msg.extra?.card_data || msg.card_data"
                        class="msg-card"
                      />
                      <OrderListCard v-else-if="(msg.extra?.card_type || msg.card_type) === 'order_list'" :data="msg.extra?.card_data || msg.card_data" class="msg-card" />
                      <LogisticsCard v-else-if="(msg.extra?.card_type || msg.card_type) === 'logistics'" :card-data="msg.extra?.card_data || msg.card_data" class="msg-card" />
                      <ProductCard v-else-if="(msg.extra?.card_type || msg.card_type) === 'product'" :card-data="msg.extra?.card_data || msg.card_data" class="msg-card" />
                      <ProductListCard v-else-if="(msg.extra?.card_type || msg.card_type) === 'product_list'" :products="msg.extra?.card_data || msg.card_data" class="msg-card" />
                      <OrdersCard v-else-if="(msg.extra?.card_type || msg.card_type) === 'orders_list'" :orders="msg.extra?.card_data || msg.card_data" class="msg-card" />
                      <div class="msg-actions">
                        <el-button text size="small" :type="getAnnotationBtnType(msg.id)" @click="openAnnotationDialog(msg)">
                          <el-icon><EditPen v-if="annotationMap[msg.id]" /><Collection v-else /></el-icon>
                          {{ annotationMap[msg.id] ? '已标注' : '标注' }}
                        </el-button>
                      </div>
                    </div>
                    <img :src="BOT_AVATAR_SVG" class="msg-avatar avatar--bot" alt="智能客服" />
                  </div>
                </template>

                <!-- 人工客服消息（左侧气泡，右侧头像）-->
                <template v-else-if="msg.role === 2">
                  <div class="msg-row">
                    <div class="msg-main msg-main--bot">
                      <div class="msg-meta msg-meta--right">
                        <span class="msg-sender">人工客服</span>
                        <span class="msg-time">{{ formatDateFull(msg.created_at) }}</span>
                      </div>
                      <div class="msg-bubble msg-bubble--agent" v-html="msg.content"></div>
                      <div class="msg-actions">
                        <el-button text size="small" :type="getAnnotationBtnType(msg.id)" @click="openAnnotationDialog(msg)">
                          <el-icon><EditPen v-if="annotationMap[msg.id]" /><Collection v-else /></el-icon>
                          {{ annotationMap[msg.id] ? '已标注' : '标注' }}
                        </el-button>
                      </div>
                    </div>
                    <img :src="AGENT_AVATAR_SVG" class="msg-avatar avatar--agent" alt="人工客服" />
                  </div>
                </template>

                <!-- 系统消息（居中）-->
                <template v-else-if="msg.role === 3">
                  <div class="msg-system">
                    <div class="system-line"></div>
                    <div class="system-content">
                      <el-icon><InfoFilled /></el-icon>
                      {{ msg.content }}
                      <span class="system-time">{{ formatDateFull(msg.created_at) }}</span>
                    </div>
                    <div class="system-line"></div>
                  </div>
                </template>
              </div>
            </template>

            <el-empty
              v-else-if="!loadingMessages"
              description="暂无消息记录"
              :image-size="60"
            />
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 标注弹窗 -->
    <el-dialog v-model="annotationDialogVisible" title="标注回复" width="520px" :close-on-click-modal="false" @closed="resetAnnotationForm">
      <div v-if="annotatingMsg" class="annotation-preview">
        <div class="preview-label">被标注的消息</div>
        <div class="preview-content">{{ annotatingMsg.content }}</div>
      </div>
      <el-form ref="annotationFormRef" :model="annotationForm" :rules="annotationRules" label-width="90px" style="margin-top:16px">
        <el-form-item label="标注结果" prop="label">
          <el-radio-group v-model="annotationForm.label" size="large">
            <el-radio-button label="good">👍 好的回答</el-radio-button>
            <el-radio-button label="neutral">😐 中性</el-radio-button>
            <el-radio-button label="bad">👎 差的回答</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="annotationForm.label === 'bad'" label="修正答案" prop="correct_answer">
          <el-input v-model="annotationForm.correct_answer" type="textarea" :rows="3" placeholder="请输入正确回答，用于模型微调" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="annotationForm.remark" placeholder="可选" maxlength="500" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="annotationDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingAnnotation" @click="handleAnnotationSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Search,
  View,
  ChatDotRound,
  CircleCheck,
  Cpu,
  User,
  EditPen,
  Collection,
  InfoFilled,
} from '@element-plus/icons-vue'
import { conversationApi, channelApi } from '@/api/admin'
import { annotationApi } from '@/api/admin'
import OrderCard     from '@/components/chat/OrderCard.vue'
import OrderListCard from '@/components/chat/OrderListCard.vue'
import LogisticsCard from '@/components/chat/LogisticsCard.vue'
import ProductCard   from '@/components/chat/ProductCard.vue'
import ProductListCard from '@/components/chat/ProductListCard.vue'
import OrdersCard from '@/components/chat/OrdersCard.vue'
import dayjs from 'dayjs'

const USER_AVATAR_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="%235b8af5"/>
  <circle cx="20" cy="15" r="7" fill="white" opacity="0.95"/>
  <ellipse cx="20" cy="35" rx="12" ry="9" fill="white" opacity="0.95"/>
</svg>`

const BOT_AVATAR_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
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

const AGENT_AVATAR_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="20" fill="%23e6a23c"/>
  <circle cx="20" cy="14" r="6" fill="white" opacity="0.95"/>
  <path d="M10 27 Q10 20 20 20 Q30 20 30 27" fill="white" opacity="0.95"/>
  <rect x="9" y="24" width="4" height="6" rx="2" fill="white" opacity="0.9"/>
  <rect x="27" y="24" width="4" height="6" rx="2" fill="white" opacity="0.9"/>
  <path d="M13 30 Q13 33 20 33 Q27 33 27 30" fill="none" stroke="white" stroke-width="2" opacity="0.9"/>
</svg>`

// ==================== 列表数据 ====================
const loading     = ref(false)
const convList    = ref([])
const total       = ref(0)
const page        = ref(1)
const pageSize    = ref(20)
const filterStatus = ref('')
const filterUser   = ref('')
const filterChannel = ref('')
const filterConvId = ref('')
const channelOptions = ref([])

// 标注相关
const annotationMap           = ref({})
const annotationDialogVisible = ref(false)
const submittingAnnotation    = ref(false)
const annotatingMsg           = ref(null)
const annotationFormRef       = ref(null)
const annotationForm          = ref({ label: 'good', correct_answer: '', remark: '' })
const annotationRules         = {
  label: [{ required: true, message: '请选择标注结果', trigger: 'change' }],
  correct_answer: [{
    validator: (rule, value, callback) => {
      if (annotationForm.value.label === 'bad' && !value?.trim()) {
        callback(new Error('差评必须填写修正答案'))
      } else { callback() }
    }, trigger: 'blur',
  }],
}

async function loadAnnotations(msgList) {
  if (!msgList?.length) return
  const botMsgIds = msgList.filter(m => m.role === 1).map(m => m.id)
  if (!botMsgIds.length) return
  const results = await Promise.allSettled(botMsgIds.map(id => annotationApi.getByMessage(id)))
  const map = {}
  results.forEach((result, i) => {
    if (result.status === 'fulfilled' && result.value?.data) map[botMsgIds[i]] = result.value.data
  })
  annotationMap.value = map
}

function openAnnotationDialog(msg) {
  annotatingMsg.value = msg
  const existing = annotationMap.value[msg.id]
  annotationForm.value = existing
    ? { label: existing.label || 'good', correct_answer: existing.correct_answer || '', remark: existing.remark || '' }
    : { label: 'good', correct_answer: '', remark: '' }
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
        conversation_id: currentConv.value?.id,
        message_id:      annotatingMsg.value.id,
        label:           annotationForm.value.label,
        correct_answer:  annotationForm.value.label === 'bad' ? annotationForm.value.correct_answer : null,
        remark:          annotationForm.value.remark || null,
      })
      ElMessage.success('标注已保存')
      annotationDialogVisible.value = false
      await loadAnnotations(messages.value)
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '标注失败')
    } finally {
      submittingAnnotation.value = false
    }
  })
}

function getAnnotationBtnType(msgId) {
  const record = annotationMap.value[msgId]
  if (!record) return 'default'
  const map = { good: 'success', bad: 'danger', neutral: 'warning' }
  return map[record.label] || 'default'
}

const dateRange    = ref([])

// 统计数据（本地从列表计算）
const stats = ref({
  total:          0,
  bot_resolved:   0,
  agent_resolved: 0,
  transferred:    0,
})

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page:           page.value,
      page_size:      pageSize.value,
      conversation_id: filterConvId.value  || undefined,
      status:         filterStatus.value  || undefined,
      start_date:     dateRange.value?.[0] || undefined,
      end_date:       dateRange.value?.[1] || undefined,
      username:       filterUser.value    || undefined,
      channel_id:     filterChannel.value || undefined,
    }
    const res = await conversationApi.getConversations(params)
    convList.value = res.data || []
    total.value    = res.page_info?.total || 0

    // 本地统计
    calcStats()
  } catch {
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

function calcStats() {
  const list = convList.value
  stats.value = {
    total:          total.value,
    bot_resolved:   list.filter(c => c.answer_source === 'rag' || c.answer_source === 'keyword').length,
    agent_resolved: list.filter(c => c.answer_source === 'tool' || c.answer_source === 'llm').length,
    transferred:    list.filter(c => c.status === 'transferred').length,
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handleReset() {
  filterStatus.value  = ''
  filterUser.value    = ''
  filterChannel.value = ''
  filterConvId.value  = ''
  dateRange.value     = []
  page.value          = 1
  fetchList()
}

// ==================== 会话详情抽屉 ====================
const drawerVisible   = ref(false)
const currentConv     = ref(null)
const messages        = ref([])
const loadingMessages = ref(false)

async function openDetailDrawer(row) {
  currentConv.value   = row
  messages.value      = []
  drawerVisible.value = true
  loadingMessages.value = true

  try {
    const res = await conversationApi.getMessages(row.id)
    messages.value = res.data || []
  } catch {
    ElMessage.error('获取消息记录失败')
  } finally {
    loadingMessages.value = false
  }
}

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

// ==================== 情绪标签 ====================
function getEmotionLabel(emotion) {
  const map = {
    neutral:  '😊 平静',
    negative: '😞 消极',
    angry:    '😡 激动',
  }
  return map[emotion] || emotion
}

// ==================== 回答来源标签 ====================
function getSourceLabel(source) {
  const map = {
    rag:     'RAG',
    tool:    '工具',
    llm:     'LLM',
    keyword: '关键词',
    default: '兜底',
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

// ==================== 消息角色标签 ====================
function getRoleLabel(role) {
  const map = {
    0: '用户',
    1: 'Bot',
    2: '人工',
    3: '系统',
  }
  return map[role] || role
}

function getRoleType(role) {
  const map = {
    0: 'primary',
    1: 'success',
    2: 'warning',
    3: 'info',
  }
  return map[role] || 'info'
}

// ==================== 工具函数 ====================
function formatDate(dateStr) {
  if (!dateStr) return '--'
  const isoStr = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z'
  return dayjs(isoStr).format('MM-DD HH:mm')
}

function formatDateFull(dateStr) {
  if (!dateStr) return '--'
  const isoStr = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z'
  return dayjs(isoStr).format('YYYY-MM-DD HH:mm:ss')
}

// ==================== 生命周期 ====================
async function loadChannelOptions() {
  try {
    const res = await channelApi.getChannels()
    channelOptions.value = res.data || []
  } catch {
    // ignore
  }
}

onMounted(() => {
  fetchList()
  loadChannelOptions()
})
</script>
<style scoped lang="scss">
.conversation-list {
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

// 搜索栏
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

// 统计卡片
.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border-left: 4px solid transparent;

  &--blue   { border-left-color: #5b8af5;
    .stat-icon { background: rgba(91,138,245,0.1); color: #5b8af5; } }
  &--green  { border-left-color: #67c23a;
    .stat-icon { background: rgba(103,194,58,0.1); color: #67c23a; } }
  &--orange { border-left-color: #e6a23c;
    .stat-icon { background: rgba(230,162,60,0.1); color: #e6a23c; } }
  &--red    { border-left-color: #f56c6c;
    .stat-icon { background: rgba(245,108,108,0.1); color: #f56c6c; } }
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 3px;
}

// 表格
.table-wrap {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  padding-bottom: 16px;
}

// 会话 ID
.conv-id {
  font-size: 13px;
  font-weight: 600;
  color: #5b8af5;
  font-family: 'Courier New', monospace;
}

// 用户单元格
.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background: linear-gradient(135deg, #5b8af5, #3d6fd4);
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 情绪标签
.emotion-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;

  &.emotion--neutral  {
    background: rgba(144,147,153,0.1);
    color: #909399;
  }
  &.emotion--negative {
    background: rgba(230,162,60,0.1);
    color: #e6a23c;
  }
  &.emotion--angry    {
    background: rgba(245,108,108,0.1);
    color: #f56c6c;
  }
}

.text-placeholder {
  color: #c0c4cc;
  font-size: 12px;
}

.text-time {
  font-size: 12px;
  color: #909399;
}

// 分页
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px 0;
}

// 抽屉内容
.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.detail-section {
  padding: 10px 0;
  border-bottom: 1px solid #f5f7fa;

  &:last-child {
    border-bottom: none;
  }
}

.detail-section-title {
  font-size: 10px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.msg-count {
  font-size: 11px;
  color: #c0c4cc;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-label {
  font-size: 12px;
  color: #909399;
  width: 60px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 12px;
  color: #303133;
  font-weight: 500;
}

// 消息记录
.messages-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  overflow-y: auto;
  padding: 4px 2px;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #e4e7ed; border-radius: 2px; }
}

.msg-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;

  &--left {
    flex-direction: row;
    padding-right: 48px;
  }

  &--right {
    flex-direction: row-reverse;
    padding-left: 48px;
  }
}

.msg-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
  max-width: 460px;

  &--bot {
    align-items: flex-end;
  }
}

.msg-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  flex-shrink: 0;
  flex-grow: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  border: 2px solid transparent;

  &.avatar--bot {
    border-color: #67c23a;
  }

  &.avatar--agent {
    border-color: #e6a23c;
  }
}

.msg-bubble {
  max-width: 100%;
  width: fit-content;
  box-sizing: border-box;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.65;
  padding: 10px 14px;

  &--user {
    background: #ecf5ff;
    color: #303133;
    border: 1px solid #d9ecff;
    border-radius: 2px 12px 12px 12px;
    align-self: flex-start;
  }

  &--bot {
    background: #ffffff;
    color: #303133;
    border: 1px solid #e4e7ed;
    border-radius: 12px 2px 12px 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    align-self: flex-end;
  }

  &--agent {
    background: #fdf6ec;
    color: #303133;
    border: 1px solid #fde8c0;
    border-radius: 12px 2px 12px 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    align-self: flex-end;
  }
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  width: 100%;

  &--left {
    flex-direction: row;
    justify-content: flex-start;
  }

  &--right {
    flex-direction: row-reverse;
    justify-content: flex-start;
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

.msg-actions {
  display: flex;
  align-items: center;
  width: fit-content;
  margin-top: 2px;
  opacity: 0;
  transition: opacity 0.2s;

  .msg-item:hover & {
    opacity: 1;
  }
}

.emotion-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;

  &.emotion--neutral  { background: rgba(144,147,153,0.1); color: #909399; }
  &.emotion--negative { background: rgba(230,162,60,0.1);  color: #e6a23c; }
  &.emotion--angry    { background: rgba(245,108,108,0.1); color: #f56c6c; }
}

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

  .el-icon { color: #c0c4cc; }
}

.system-time {
  color: #c0c4cc;
  margin-left: 4px;
}

.annotation-preview {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #5b8af5;
  margin-bottom: 12px;
}

.preview-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.preview-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
  white-space: pre-wrap;
  max-height: 80px;
  overflow-y: auto;
}
</style>