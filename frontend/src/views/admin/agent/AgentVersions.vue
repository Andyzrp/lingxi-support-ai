<template>
  <div class="agent-versions">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">版本管理</h2>
          <span class="page-sub">{{ agentName || 'Agent' }} · 共 {{ versionList.length }} 个版本</span>
        </div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新建版本
      </el-button>
    </div>

    <!-- 当前运行版本横幅 -->
    <div class="current-version-banner" v-if="publishedVersion">
      <div class="banner-left">
        <el-icon class="banner-icon"><CircleCheckFilled /></el-icon>
        <div>
          <div class="banner-title">
            当前运行版本：
            <el-tag type="success" effect="dark" size="small">
              {{ publishedVersion.version }}
            </el-tag>
          </div>
          <div class="banner-sub">
            发布于 {{ formatDateFull(publishedVersion.published_at) }} ·
            模型：{{ formatModelName(publishedVersion.model) }}
          </div>
        </div>
      </div>
      <el-button
        type="primary"
        plain
        size="small"
        :icon="Edit"
        @click="openCreateDialog"
      >
        基于此版本新建
      </el-button>
    </div>

    <!-- 版本时间线列表 -->
    <div v-loading="loading" class="versions-wrap">
      <el-timeline v-if="versionList.length">
        <el-timeline-item
          v-for="version in versionList"
          :key="version.id"
          :type="getTimelineType(version.status)"
          :hollow="version.status === 0"
          :timestamp="formatDateFull(version.created_at)"
          placement="top"
        >
          <div class="version-card" :class="`version-card--${version.status}`">
            <div class="status-bar"></div>
            <!-- 版本头部 -->
            <div class="version-card-header">
              <div class="version-title-row">
                <span class="version-tag">{{ version.version }}</span>
                <el-tag
                  :type="getStatusType(version.status)"
                  size="small"
                  round
                >
                  {{ getStatusLabel(version.status) }}
                </el-tag>
              </div>

              <!-- 操作按钮 -->
              <div class="version-actions">
                <el-button
                  v-if="version.status === 0"
                  type="success"
                  size="small"
                  :icon="Upload"
                  :loading="publishingId === version.id"
                  @click="handlePublish(version)"
                >
                  发布
                </el-button>
                <el-button
                  v-if="version.status === 2"
                  type="warning"
                  size="small"
                  plain
                  :icon="RefreshLeft"
                  :loading="rollbackingId === version.id"
                  @click="handleRollback(version)"
                >
                  回滚
                </el-button>
                <el-button
                  size="small"
                  :icon="View"
                  @click="openDetailDrawer(version)"
                >
                  查看配置
                </el-button>
                <el-button
                  v-if="version.status === 0"
                  type="primary"
                  size="small"
                  plain
                  :icon="Edit"
                  @click="openEditDialog(version)"
                >
                  编辑
                </el-button>
              </div>
            </div>

            <!-- 版本核心配置预览 -->
            <div class="version-config-preview">
              <!-- 模型 -->
              <div class="preview-item">
                <el-icon><MagicStick /></el-icon>
                <span class="preview-label">模型：</span>
                <el-tag size="small" type="primary" effect="plain">
                  {{ formatModelName(version.model) }}
                </el-tag>
              </div>

              <!-- 温度 -->
              <div class="preview-item">
                <el-icon><Odometer /></el-icon>
                <span class="preview-label">温度：</span>
                <span class="preview-value">{{ version.temperature }}</span>
              </div>

              <!-- 最大 Token -->
              <div class="preview-item">
                <el-icon><Document /></el-icon>
                <span class="preview-label">Max Token：</span>
                <span class="preview-value">{{ version.max_tokens }}</span>
              </div>

              <!-- 工具 -->
              <div class="preview-item">
                <el-icon><Tools /></el-icon>
                <span class="preview-label">工具：</span>
                <div class="preview-tools">
                  <el-tag
                    v-for="tool in (version.tools_enabled || [])"
                    :key="tool"
                    size="small"
                    type="success"
                    effect="plain"
                  >
                    {{ getToolLabel(tool) }}
                  </el-tag>
                  <span v-if="!version.tools_enabled?.length" class="text-placeholder">
                    未配置
                  </span>
                </div>
              </div>

              <!-- 转人工阈值 -->
              <div class="preview-item">
                <el-icon><SwitchButton /></el-icon>
                <span class="preview-label">转人工阈值：</span>
                <span class="preview-value">
                  {{ version.no_answer_threshold }} 次
                </span>
              </div>
            </div>

            <!-- Prompt 预览 -->
            <div class="prompt-preview" v-if="version.system_prompt">
              <div class="prompt-preview-label">System Prompt 预览：</div>
              <div class="prompt-preview-content">
                {{ truncatePrompt(version.system_prompt) }}
              </div>
            </div>

            <!-- 发布信息 -->
            <div class="version-publish-info" v-if="version.status === 1">
              <el-icon><Clock /></el-icon>
              <span>发布时间：{{ formatDateFull(version.published_at) }}</span>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && !versionList.length"
        description="暂无版本记录，点击右上角新建第一个版本"
        :image-size="100"
      />
    </div>

    <!-- 新建/编辑版本弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑草稿版本' : '新建 Agent 版本'"
      width="760px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <!-- 使用模型 -->
        <el-form-item label="使用模型" prop="model">
          <el-select v-model="form.model" style="width: 100%">
            <el-option-group label="DeepSeek">
              <el-option label="DeepSeek V3.2（推荐）" value="deepseek-v3.2-chat-private" />
              <el-option label="DeepSeek V3.2 Pro"     value="deepseek-v3.2-private" />
            </el-option-group>
            <el-option-group label="GLM">
              <el-option label="GLM 4.7" value="glm-4.7-private" />
              <el-option label="GLM 5"   value="glm-5-private" />
            </el-option-group>
            <el-option-group label="Minimax">
              <el-option label="Minimax M2.1" value="minimax-m2.1-private" />
              <el-option label="Minimax M2.5" value="minimax-m2.5-private" />
            </el-option-group>
            <el-option-group label="Kimi">
              <el-option label="Kimi K2.5" value="kimi-k2.5-private" />
              <el-option label="Kimi K2.6" value="kimi-k2.6-private" />
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- System Prompt -->
        <el-form-item label="System Prompt" prop="system_prompt">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            placeholder="请输入系统提示词..."
            :rows="10"
            maxlength="4000"
            show-word-limit
          />
        </el-form-item>

        <!-- 温度 + Max Token -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="温度（temperature）" prop="temperature">
              <div class="slider-wrap">
                <el-slider
                  v-model="form.temperature"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  style="flex: 1"
                />
                <span class="slider-val">{{ form.temperature }}</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大 Token" prop="max_tokens">
              <el-input-number
                v-model="form.max_tokens"
                :min="256"
                :max="4096"
                :step="128"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 启用工具 -->
        <el-form-item label="启用工具" prop="tools_enabled">
          <el-checkbox-group v-model="form.tools_enabled">
            <el-checkbox
              v-for="tool in availableTools"
              :key="tool.value"
              :label="tool.value"
              border
              style="margin-right: 8px; margin-bottom: 8px"
            >
              {{ tool.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 转人工阈值 -->
        <el-form-item label="转人工阈值" prop="no_answer_threshold">
          <el-input-number
            v-model="form.no_answer_threshold"
            :min="1"
            :max="10"
            :step="1"
            style="width: 140px"
          />
          <span class="form-hint">
            连续答不上 {{ form.no_answer_threshold }} 次后自动转人工
          </span>
        </el-form-item>

        <!-- 转人工关键词 -->
        <el-form-item label="转人工关键词">
          <div class="tags-editor">
            <el-tag
              v-for="kw in form.transfer_keywords"
              :key="kw"
              closable
              size="small"
              type="danger"
              style="margin-right: 6px; margin-bottom: 6px"
              @close="removeKeyword(kw)"
            >
              {{ kw }}
            </el-tag>
            <el-input
              v-if="kwInputVisible"
              ref="kwInputRef"
              v-model="kwInputValue"
              size="small"
              style="width: 100px"
              @keyup.enter="confirmKeyword"
              @blur="confirmKeyword"
            />
            <el-button
              v-else
              text
              type="primary"
              size="small"
              :icon="Plus"
              @click="showKwInput"
            >
              添加关键词
            </el-button>
          </div>
        </el-form-item>

        <!-- 版本备注 -->
        <el-form-item label="版本备注">
          <el-input
            v-model="form.remark"
            placeholder="描述本次修改内容，如：优化退款话术"
            maxlength="200"
            show-word-limit
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          plain
          type="primary"
          :loading="submitting"
          @click="handleSubmit(false)"
        >
          保存草稿
        </el-button>
        <el-button
          type="success"
          :loading="submitting"
          @click="handleSubmit(true)"
        >
          保存并发布
        </el-button>
      </template>
    </el-dialog>

    <!-- 配置详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="版本配置详情"
      size="520px"
      direction="rtl"
    >
      <div v-if="detailVersion" class="version-detail">
        <!-- 基础信息 -->
        <div class="detail-section">
          <div class="detail-section-title">基础信息</div>
          <div class="detail-grid">
            <div class="detail-row">
              <span class="detail-label">版本号</span>
              <el-tag type="primary" effect="dark" size="small">
                {{ detailVersion.version }}
              </el-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态</span>
              <el-tag
                :type="getStatusType(detailVersion.status)"
                size="small"
                round
              >
                {{ getStatusLabel(detailVersion.status) }}
              </el-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">使用模型</span>
              <el-tag type="primary" effect="plain" size="small">
                {{ formatModelName(detailVersion.model) }}
              </el-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">温度</span>
              <span class="detail-value">{{ detailVersion.temperature }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Max Token</span>
              <span class="detail-value">{{ detailVersion.max_tokens }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">转人工阈值</span>
              <span class="detail-value">
                {{ detailVersion.no_answer_threshold }} 次
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">创建时间</span>
              <span class="detail-value">
                {{ formatDateFull(detailVersion.created_at) }}
              </span>
            </div>
            <div class="detail-row" v-if="detailVersion.published_at">
              <span class="detail-label">发布时间</span>
              <span class="detail-value">
                {{ formatDateFull(detailVersion.published_at) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 启用工具 -->
        <div class="detail-section">
          <div class="detail-section-title">启用工具</div>
          <div class="detail-tools">
            <el-tag
              v-for="tool in (detailVersion.tools_enabled || [])"
              :key="tool"
              type="success"
              effect="plain"
              size="small"
            >
              {{ getToolLabel(tool) }}
            </el-tag>
            <span
              v-if="!detailVersion.tools_enabled?.length"
              class="text-placeholder"
            >
              未配置
            </span>
          </div>
        </div>

        <!-- 转人工关键词 -->
        <div class="detail-section">
          <div class="detail-section-title">转人工关键词</div>
          <div class="detail-tools">
            <el-tag
              v-for="kw in (detailVersion.transfer_keywords || [])"
              :key="kw"
              type="danger"
              effect="plain"
              size="small"
            >
              {{ kw }}
            </el-tag>
            <span
              v-if="!detailVersion.transfer_keywords?.length"
              class="text-placeholder"
            >
              未配置
            </span>
          </div>
        </div>

        <!-- System Prompt -->
        <div class="detail-section">
          <div class="detail-section-title">System Prompt</div>
          <div class="prompt-full">{{ detailVersion.system_prompt }}</div>
        </div>

        <!-- 版本备注 -->
        <div class="detail-section" v-if="detailVersion.remark">
          <div class="detail-section-title">版本备注</div>
          <div class="detail-remark">{{ detailVersion.remark }}</div>
        </div>

        <!-- 抽屉操作按钮 -->
        <div class="drawer-footer">
          <el-button
            v-if="detailVersion.status === 0"
            type="success"
            :icon="Upload"
            :loading="publishingId === detailVersion.id"
            @click="handlePublish(detailVersion)"
          >
            发布此版本
          </el-button>
          <el-button
            v-if="detailVersion.status === 2"
            type="warning"
            plain
            :icon="RefreshLeft"
            :loading="rollbackingId === detailVersion.id"
            @click="handleRollback(detailVersion)"
          >
            回滚到此版本
          </el-button>
          <el-button
            v-if="detailVersion.status === 0"
            type="primary"
            plain
            :icon="Edit"
            @click="openEditFromDrawer"
          >
            编辑此草稿
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Upload,
  RefreshLeft,
  View,
  Edit,
  CircleCheckFilled,
  MagicStick,
  Odometer,
  Document,
  Tools,
  SwitchButton,
  Clock,
} from '@element-plus/icons-vue'
import { agentApi } from '@/api/admin'
import dayjs from 'dayjs'

const route  = useRoute()
const router = useRouter()

const agentId   = computed(() => Number(route.params.id))
const agentName = ref('')

// ==================== 可用工具 ====================
const availableTools = [
  { value: 'query_order',     label: '订单查询' },
  { value: 'query_logistics', label: '物流查询' },
  { value: 'refund',          label: '退款申请' },
  { value: 'query_product',   label: '商品查询' },
]

function getToolLabel(tool) {
  return availableTools.find(t => t.value === tool)?.label || tool
}

// ==================== 模型名称格式化 ====================
const MODEL_MAP = {
  'deepseek-v3.2-chat-private': 'DeepSeek V3.2',
  'deepseek-v3.2-private':      'DeepSeek V3.2 Pro',
  'glm-4.7-private':            'GLM 4.7',
  'glm-5-private':              'GLM 5',
  'minimax-m2.1-private':       'Minimax M2.1',
  'minimax-m2.5-private':       'Minimax M2.5',
  'kimi-k2.5-private':          'Kimi K2.5',
  'kimi-k2.6-private':          'Kimi K2.6',
}

function formatModelName(model) {
  return MODEL_MAP[model] || model || '未配置'
}

// ==================== 版本状态 ====================
function getStatusLabel(status) {
  const map = {
    0: '草稿',
    1: '已发布',
    2: '已归档',
    draft:      '草稿',
    published:  '已发布',
    deprecated: '已归档',
  }
  return map[status] ?? String(status)
}

function getStatusType(status) {
  const map = {
    0: 'info',    // 草稿
    1: 'success', // 已发布
    2: 'warning', // 已归档
    draft:      'info',
    published:  'success',
    deprecated: 'warning',
  }
  return map[status] || 'info'
}

function getTimelineType(status) {
  const map = {
    0: 'info',    // 草稿
    1: 'success', // 已发布
    2: '',        // 已归档-默认灰色
    draft:      'info',
    published:  'success',
    deprecated: '',
  }
  return map[status] || 'primary'
}

// ==================== 版本列表 ====================
const loading     = ref(false)
const versionList = ref([])

// 当前已发布版本
const publishedVersion = computed(() =>
  versionList.value.find(v => v.status === 1)
)

async function fetchVersions() {
  loading.value = true
  try {
    const res = await agentApi.getVersions(agentId.value)
    // 按创建时间倒序排列
    versionList.value = (res.data || []).sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    )
  } catch {
    ElMessage.error('获取版本列表失败')
  } finally {
    loading.value = false
  }
}

// 获取 Agent 名称
async function fetchAgentName() {
  try {
    const res  = await agentApi.getAgents()
    const agent = (res.data || []).find(a => a.id === agentId.value)
    agentName.value = agent?.name || ''
  } catch {
    // 不影响主功能
  }
}

// ==================== 发布 ====================
const publishingId = ref(null)

async function handlePublish(version) {
  try {
    await ElMessageBox.confirm(
      `确认发布版本「${version.version}」？发布后将作为当前运行版本，原发布版本将变为已废弃。`,
      '发布确认',
      {
        type:              'warning',
        confirmButtonText: '确认发布',
        cancelButtonText:  '取消',
      }
    )
    publishingId.value = version.id
    await agentApi.publishVersion(agentId.value, {
      version_id: version.id,
      channel:    'production',
    })
    ElMessage.success(`版本「${version.version}」发布成功，已生效！`)
    detailDrawerVisible.value = false
    fetchVersions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.message || '发布失败')
    }
  } finally {
    publishingId.value = null
  }
}

// ==================== 回滚 ====================
const rollbackingId = ref(null)

async function handleRollback(version) {
  try {
    await ElMessageBox.confirm(
      `确认回滚到版本「${version.version}」？当前运行版本将被替换。`,
      '回滚确认',
      {
        type:              'warning',
        confirmButtonText: '确认回滚',
        cancelButtonText:  '取消',
        confirmButtonClass: 'el-button--warning',
      }
    )
    rollbackingId.value = version.id
    await agentApi.rollbackVersion(agentId.value, {
      version_id: version.id,
    })
    ElMessage.success(`已回滚到版本「${version.version}」！`)
    detailDrawerVisible.value = false
    fetchVersions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.message || '回滚失败')
    }
  } finally {
    rollbackingId.value = null
  }
}

// ==================== 新建/编辑版本 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const isEdit        = ref(false)
const editId        = ref(null)
const formRef       = ref(null)

const DEFAULT_PROMPT =
`你是灵犀智能客服，专业处理电商售后问题。

## 能力范围
- 订单查询、物流查询、退款申请、商品咨询

## 回复规范
1. 保持专业、友好的语气
2. 回复简洁，不超过200字
3. 涉及具体订单时，先调用工具查询再回答
4. 无法解决时，主动提出转接人工客服

## 注意事项
- 不讨论与客服无关的话题
- 遇到投诉、纠纷类问题，优先转人工处理`

const form = ref({
  model:                'deepseek-v3.2-chat-private',
  system_prompt:        DEFAULT_PROMPT,
  temperature:          0.7,
  max_tokens:           1024,
  tools_enabled:        ['query_order', 'query_logistics', 'refund', 'query_product'],
  no_answer_threshold:  3,
  transfer_keywords:    ['投诉', '举报', '曝光'],
  remark:               '',
})

const rules = {
  model: [
    { required: true, message: '请选择使用的大模型', trigger: 'change' },
  ],
  system_prompt: [
    { required: true, message: '请输入 System Prompt', trigger: 'blur' },
    { min: 10, message: 'Prompt 不少于 10 个字符', trigger: 'blur' },
  ],
  tools_enabled: [
    {
      validator: (rule, value, callback) => {
        if (!value?.length) {
          callback(new Error('至少启用一个工具'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 新建（可基于已发布版本预填）
function openCreateDialog() {
  isEdit.value = false
  editId.value = null

  // 若有已发布版本，基于其配置预填
  if (publishedVersion.value) {
    const pv = publishedVersion.value
    form.value.model               = pv.model               || 'deepseek-v3.2-chat-private'
    form.value.system_prompt       = pv.system_prompt       || DEFAULT_PROMPT
    form.value.temperature         = pv.temperature         ?? 0.7
    form.value.max_tokens          = pv.max_tokens          ?? 1024
    form.value.tools_enabled       = [...(pv.tools_enabled  || [])]
    form.value.no_answer_threshold = pv.no_answer_threshold ?? 3
    form.value.transfer_keywords   = [...(pv.transfer_keywords || [])]
    form.value.remark              = ''
  }

  dialogVisible.value = true
}

// 编辑草稿
function openEditDialog(version) {
  isEdit.value               = true
  editId.value               = version.id
  form.value.model               = version.model               || 'deepseek-v3.2-chat-private'
  form.value.system_prompt       = version.system_prompt       || DEFAULT_PROMPT
  form.value.temperature         = version.temperature         ?? 0.7
  form.value.max_tokens          = version.max_tokens          ?? 1024
  form.value.tools_enabled       = [...(version.tools_enabled  || [])]
  form.value.no_answer_threshold = version.no_answer_threshold ?? 3
  form.value.transfer_keywords   = [...(version.transfer_keywords || [])]
  form.value.remark              = version.remark              || ''
  dialogVisible.value            = true
}

function openEditFromDrawer() {
  detailDrawerVisible.value = false
  nextTick(() => openEditDialog(detailVersion.value))
}

function resetForm() {
  form.value = {
    model:                'deepseek-v3.2-chat-private',
    system_prompt:        DEFAULT_PROMPT,
    temperature:          0.7,
    max_tokens:           1024,
    tools_enabled:        ['query_order', 'query_logistics', 'refund', 'query_product'],
    no_answer_threshold:  3,
    transfer_keywords:    ['投诉', '举报', '曝光'],
    remark:               '',
  }
  formRef.value?.clearValidate()
  kwInputVisible.value = false
  kwInputValue.value   = ''
}

// 提交（saveAndPublish: 是否保存后立即发布）
async function handleSubmit(saveAndPublish = false) {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      let versionId = editId.value

      if (isEdit.value) {
        // 编辑草稿：暂无编辑接口，直接重新创建
        const res = await agentApi.createVersion(agentId.value, form.value)
        versionId = res.data?.id        
        ElMessage.info('草稿已更新，请前往版本列表发布')
      } else {
        await agentApi.createVersion(agentId.value, form.value)
        ElMessage.info('草稿已更新，请前往版本列表发布')
      }

      if (saveAndPublish && versionId) {
        await agentApi.publishVersion(agentId.value, {
          version_id: versionId,
          channel:    'production',
        })
        ElMessage.success('已保存并发布，新配置立即生效！')
      } else {
        ElMessage.success('草稿已保存，在版本列表中发布后生效')
      }

      dialogVisible.value = false
      fetchVersions()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// ==================== 配置详情抽屉 ====================
const detailDrawerVisible = ref(false)
const detailVersion       = ref(null)

function openDetailDrawer(version) {
  detailVersion.value       = version
  detailDrawerVisible.value = true
}

// ==================== 转人工关键词编辑 ====================
const kwInputVisible = ref(false)
const kwInputValue   = ref('')
const kwInputRef     = ref(null)

function showKwInput() {
  kwInputVisible.value = true
  nextTick(() => kwInputRef.value?.focus())
}

function confirmKeyword() {
  const val = kwInputValue.value.trim()
  if (val && !form.value.transfer_keywords.includes(val)) {
    form.value.transfer_keywords.push(val)
  }
  kwInputVisible.value = false
  kwInputValue.value   = ''
}

function removeKeyword(kw) {
  form.value.transfer_keywords =
    form.value.transfer_keywords.filter(k => k !== kw)
}

// ==================== 工具函数 ====================
function truncatePrompt(prompt) {
  if (!prompt) return ''
  return prompt.length > 120 ? prompt.slice(0, 120) + '...' : prompt
}

function formatDateFull(dateStr) {
  if (!dateStr) return '--'
  const isoStr = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z'
  return dayjs(isoStr).format('YYYY-MM-DD HH:mm:ss')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchAgentName()
  fetchVersions()
})
</script>
<style scoped lang="scss">
.agent-versions {
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

// 当前版本横幅
.current-version-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: linear-gradient(
    135deg,
    rgba(103, 194, 58, 0.08),
    rgba(103, 194, 58, 0.03)
  );
  border: 1px solid rgba(103, 194, 58, 0.3);
  border-radius: 10px;
  margin-bottom: 20px;
  gap: 12px;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.banner-icon {
  font-size: 24px;
  color: #67c23a;
  flex-shrink: 0;
}

.banner-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.banner-sub {
  font-size: 12px;
  color: #909399;
}

// 版本时间线
.versions-wrap {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 24px 28px;
  min-height: 300px;

  :deep(.el-timeline) {
    padding-left: 4px;
  }

  :deep(.el-timeline-item__tail) {
    border-left: 2px dashed #e4e7ed;
  }

  :deep(.el-timeline-item__node) {
    border-width: 2px;
  }

  :deep(.el-timeline-item__timestamp) {
    font-size: 12px;
    color: #c0c4cc;
    margin-bottom: 10px;
  }
}

// 版本卡片
.version-card {
  position: relative;
  padding-left: 24px;
  background: #f5f7fa;
  border-radius: 10px;
  border: 1px solid #e4e7ed;
  padding: 16px 20px 16px 28px;
  margin-bottom: 8px;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  // 已发布版本(1)：绿色边框
  &--1 {
    border-color: rgba(103, 194, 58, 0.4);
    background: rgba(103, 194, 58, 0.03);
  }

  // 草稿版本(0)：蓝色边框
  &--0 {
    border-color: rgba(91, 138, 245, 0.4);
    background: rgba(91, 138, 245, 0.03);
  }

  // 已归档版本(2)：灰色
  &--2 {
    border-color: #e4e7ed;
    background: #fafafa;
    opacity: 0.8;
  }
}

// 状态色条
.status-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 10px 0 0 10px;

  .version-card--1 & {
    background: #67c23a; // 已发布-绿
  }

  .version-card--0 & {
    background: #5b8af5; // 草稿-蓝
  }

  .version-card--2 & {
    background: #909399; // 已归档-灰
  }
}

// 版本卡片头部
.version-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;
}

.version-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.version-tag {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  font-family: 'Courier New', monospace;
}

.version-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

// 配置预览
.version-config-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  margin-bottom: 12px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;

  .el-icon {
    color: #909399;
    font-size: 14px;
    flex-shrink: 0;
  }
}

.preview-label {
  color: #909399;
  flex-shrink: 0;
}

.preview-value {
  color: #303133;
  font-weight: 500;
}

.preview-tools {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.text-placeholder {
  color: #c0c4cc;
  font-size: 12px;
}

// Prompt 预览
.prompt-preview {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  margin-bottom: 10px;
}

.prompt-preview-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prompt-preview-content {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
}

// 发布信息
.version-publish-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #67c23a;
  padding-top: 10px;
  border-top: 1px solid rgba(103, 194, 58, 0.2);

  .el-icon {
    font-size: 14px;
  }
}

// 弹窗表单
.slider-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.slider-val {
  font-size: 14px;
  font-weight: 700;
  color: #5b8af5;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

// 标签编辑器
.tags-editor {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
}

// 详情抽屉
.version-detail {
  padding: 0 4px;
  display: flex;
  flex-direction: column;
}

.detail-section {
  padding: 16px 0;
  border-bottom: 1px solid #f5f7fa;

  &:last-of-type {
    border-bottom: none;
  }
}

.detail-section-title {
  font-size: 11px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-label {
  font-size: 13px;
  color: #909399;
  width: 90px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.detail-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

// System Prompt 完整展示
.prompt-full {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 12px 14px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  max-height: 300px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.detail-remark {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  padding: 8px 12px;
  background: #fffbf0;
  border-left: 3px solid #e6a23c;
  border-radius: 0 6px 6px 0;
}

// 抽屉底部操作
.drawer-footer {
  padding-top: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>