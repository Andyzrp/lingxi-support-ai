<template>
  <div class="agent-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">Agent 管理</h2>
        <span class="page-sub">共 {{ agentList.length }} 个 Agent</span>
      </div>
      <div class="page-header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">
          新建 Agent
        </el-button>
      </div>
    </div>

    <!-- 说明横幅 -->
    <div class="tips-banner">
      <el-icon><InfoFilled /></el-icon>
      <span>
        Agent 是第二层智能拦截，负责意图识别、RAG 检索、工具调用等复杂推理。
        修改配置后需 <strong>发布新版本</strong> 才会生效。
      </span>
    </div>

    <!-- Agent 卡片列表 -->
    <div v-loading="loading" class="agent-grid">
      <div
        v-for="agent in agentList"
        :key="agent.id"
        class="agent-card"
      >
        <!-- 卡片头部 -->
        <div class="agent-card-header">
          <div class="agent-icon">
            <el-icon :size="28"><Cpu /></el-icon>
          </div>
          <div class="agent-header-right">
            <el-tag
              :type="agent.status === 1 ? 'success' : 'info'"
              size="small"
              round
            >
              {{ agent.status === 1 ? '运行中' : '停用' }}
            </el-tag>
          </div>
        </div>

        <!-- Agent 名称 -->
        <div class="agent-name">{{ agent.name }}</div>

        <!-- 当前版本 -->
        <div class="agent-version-row">
          <el-icon class="version-icon"><Flag /></el-icon>
          <span class="version-label">当前版本：</span>
          <el-tag type="primary" size="small" effect="dark">
            {{ agent.current_version || '未发布' }}
          </el-tag>
        </div>

        <!-- 模型信息 -->
        <div class="agent-config">
          <!-- 使用模型 -->
          <div class="config-item">
            <div class="config-label">
              <el-icon><MagicStick /></el-icon>
              使用模型
            </div>
            <div class="config-value model-value">
              {{ formatModelName(agent.model) }}
            </div>
          </div>

          <!-- 工具列表 -->
          <div class="config-item config-item--tools">
            <div class="config-label">
              <el-icon><Tools /></el-icon>
              启用工具
            </div>
            <div class="tools-wrap">
              <el-tag
                v-for="tool in (agent.tools_enabled || [])"
                :key="tool"
                size="small"
                type="success"
                effect="plain"
              >
                {{ getToolLabel(tool) }}
              </el-tag>
              <span v-if="!agent.tools_enabled?.length" class="text-placeholder">
                未配置
              </span>
            </div>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="agent-stats">
          <div class="agent-stat-item">
            <span class="stat-value">{{ agent.version_count || 0 }}</span>
            <span class="stat-label">历史版本</span>
          </div>
          <div class="agent-stat-divider"></div>
          <div class="agent-stat-item">
            <span class="stat-value">
              {{ agent.today_sessions || 0 }}
            </span>
            <span class="stat-label">今日会话</span>
          </div>
          <div class="agent-stat-divider"></div>
          <div class="agent-stat-item">
            <span class="stat-value">
              {{ agent.resolve_rate != null
                  ? `${(agent.resolve_rate * 100).toFixed(0)}%`
                  : '--' }}
            </span>
            <span class="stat-label">解决率</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="agent-card-footer">
          <el-button
            type="primary"
            plain
            size="small"
            :icon="Document"
            @click="goVersions(agent)"
          >
            版本管理
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Share"
            @click="openWorkflowGraph(agent.id)"
          >
            查看工作流
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Edit"
            @click="openConfigDialog(agent)"
          >
            快速配置
          </el-button>
          <el-dropdown trigger="click" @command="(cmd) => handleAgentCommand(cmd, agent)">
            <el-button text :icon="MoreFilled" size="small" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="delete" :icon="Delete">
                  删除 Agent
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && agentList.length === 0"
        description="暂无 Agent 数据"
        :image-size="100"
        class="agent-empty"
      />
    </div>

    <!-- 快速配置弹窗（新建版本草稿） -->
    <el-dialog
      v-model="configDialogVisible"
      title="快速配置 Agent"
      width="720px"
      :close-on-click-modal="false"
      @closed="resetConfigForm"
    >
      <!-- 版本提示 -->
      <el-alert
        title="修改后将创建新的草稿版本，需前往「版本管理」发布后才会生效"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      />

      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        label-width="110px"
      >
        <!-- 使用模型 -->
        <el-form-item label="使用模型" prop="model">
          <el-select
            v-model="configForm.model"
            placeholder="请选择大模型"
            style="width: 100%"
          >
            <el-option-group label="DeepSeek">
              <el-option
                label="DeepSeek V3.2（推荐）"
                value="deepseek-v3.2-chat-private"
              />
              <el-option
                label="DeepSeek V3.2 复杂推理"
                value="deepseek-v3.2-private"
              />
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
            v-model="configForm.system_prompt"
            type="textarea"
            placeholder="请输入系统提示词..."
            :rows="8"
            maxlength="4000"
            show-word-limit
          />
        </el-form-item>

        <!-- 温度 + 最大 Token -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="温度（temperature）" prop="temperature">
              <div class="slider-wrap">
                <el-slider
                  v-model="configForm.temperature"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  style="flex: 1"
                />
                <span class="slider-value">{{ configForm.temperature }}</span>
              </div>
              <div class="param-hint">
                {{ configForm.temperature <= 0.3
                    ? '低：回复更确定、保守'
                    : configForm.temperature >= 0.8
                      ? '高：回复更多样、创意'
                      : '中：平衡稳定与灵活（推荐）' }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大 Token" prop="max_tokens">
              <el-input-number
                v-model="configForm.max_tokens"
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
          <el-checkbox-group v-model="configForm.tools_enabled">
            <el-checkbox
              v-for="tool in availableTools"
              :key="tool.value"
              :label="tool.value"
              border
              style="margin-right: 8px; margin-bottom: 8px"
            >
              <div class="tool-option">
                <el-icon><component :is="tool.icon" /></el-icon>
                <span>{{ tool.label }}</span>
              </div>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 答不上阈值 -->
        <el-form-item label="转人工阈值" prop="no_answer_threshold">
          <el-input-number
            v-model="configForm.no_answer_threshold"
            :min="1"
            :max="10"
            :step="1"
            style="width: 140px"
          />
          <span class="param-hint" style="margin-left: 10px">
            连续答不上 {{ configForm.no_answer_threshold }} 次后自动转人工
          </span>
        </el-form-item>

        <!-- 转人工关键词 -->
        <el-form-item label="转人工关键词">
          <div class="tags-editor">
            <el-tag
              v-for="kw in configForm.transfer_keywords"
              :key="kw"
              closable
              size="small"
              type="danger"
              style="margin-right: 6px; margin-bottom: 6px"
              @close="removeTransferKeyword(kw)"
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
          <div class="param-hint">触发这些词时立即转人工，如：投诉、举报、曝光</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          plain
          :loading="submitting"
          @click="handleSaveDraft"
        >
          保存为草稿
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSaveAndPublish"
        >
          保存并发布
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建 Agent 弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建 Agent"
      width="500px"
      :close-on-click-modal="false"
      @closed="createForm.name = ''"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入描述（选填）"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 工作流可视化弹窗 -->
    <el-dialog
      v-model="graphVisible"
      title="Agent 工作流图"
      width="800px"
      top="5vh"
    >
      <div class="graph-wrap">
        <pre v-if="graphFormat === 'ascii'" class="graph-ascii">{{ graphContent }}</pre>
        <div v-else ref="mermaidRef" class="graph-mermaid" />
      </div>

      <template #footer>
        <el-radio-group
          v-model="graphFormat"
          size="small"
          @change="renderGraph"
          style="margin-right: auto"
        >
          <el-radio-button value="mermaid">流程图</el-radio-button>
          <el-radio-button value="ascii">ASCII</el-radio-button>
        </el-radio-group>
        <el-button @click="graphVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  InfoFilled,
  Cpu,
  Flag,
  MagicStick,
  Tools,
  Document,
  Share,
  Edit,
  Plus,
  Delete,
  MoreFilled,
  List,
  ShoppingCart,
  Van,
  RefreshRight,
} from '@element-plus/icons-vue'
import { agentApi } from '@/api/admin'

const router = useRouter()

// ==================== 列表数据 ====================
const loading   = ref(false)
const agentList = ref([])

async function fetchAgentList() {
  loading.value = true
  try {
    const res = await agentApi.getAgents()
    agentList.value = res.data || []
  } catch {
    ElMessage.error('获取 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

// ==================== 新建 Agent ====================
const createDialogVisible = ref(false)
const creating             = ref(false)
const createFormRef        = ref(null)
const createForm           = ref({ name: '', description: '' })

const createRules = {
  name: [
    { required: true, message: '请输入 Agent 名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度 2-50 字符', trigger: 'blur' },
  ],
}

function openCreateDialog() {
  createDialogVisible.value = true
}

async function handleCreate() {
  await createFormRef.value?.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      await agentApi.createAgent({
        name: createForm.value.name,
        description: createForm.value.description,
      })
      ElMessage.success('Agent 创建成功')
      createDialogVisible.value = false
      fetchAgentList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '创建失败')
    } finally {
      creating.value = false
    }
  })
}

async function handleAgentCommand(cmd, agent) {
  if (cmd === 'delete') {
    await handleDelete(agent)
  }
}

async function handleDelete(agent) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 Agent「${agent.name}」吗？该操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await agentApi.deleteAgent(agent.id)
    ElMessage.success('删除成功')
    fetchAgentList()
  } catch (e) {
    if (e !== 'cancel') {
      const msg = e?.response?.data?.message || e?.response?.data?.detail || '删除失败'
      ElMessage.error(msg)
    }
  }
}

// ==================== 可用工具定义 ====================
const availableTools = [
  { value: 'query_order',     label: '订单查询', icon: 'List'         },
  { value: 'query_logistics', label: '物流查询', icon: 'Van'          },
  { value: 'refund',          label: '退款申请', icon: 'RefreshRight' },
  { value: 'query_product',   label: '商品查询', icon: 'ShoppingCart' },
]

function getToolLabel(tool) {
  const found = availableTools.find(t => t.value === tool)
  return found?.label || tool
}

// ==================== 模型名称格式化 ====================
function formatModelName(model) {
  const map = {
    'deepseek-v3.2-chat-private': 'DeepSeek V3.2',
    'deepseek-v3.2-private':      'DeepSeek V3.2 Pro',
    'glm-4.7-private':            'GLM 4.7',
    'glm-5-private':              'GLM 5',
    'minimax-m2.1-private':       'Minimax M2.1',
    'minimax-m2.5-private':       'Minimax M2.5',
    'kimi-k2.5-private':          'Kimi K2.5',
    'kimi-k2.6-private':          'Kimi K2.6',
  }
  return map[model] || model || '未配置'
}

// ==================== 跳转版本管理 ====================
function goVersions(agent) {
  router.push(`/admin/agents/${agent.id}/versions`)
}

// ==================== 快速配置弹窗 ====================
const configDialogVisible = ref(false)
const submitting          = ref(false)
const currentAgentId      = ref(null)
const configFormRef       = ref(null)

const DEFAULT_PROMPT = `你是灵犀智能客服，专业处理电商售后问题。

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

const configForm = ref({
  model:                'deepseek-v3.2-chat-private',
  system_prompt:        DEFAULT_PROMPT,
  temperature:          0.7,
  max_tokens:           1024,
  tools_enabled:        ['query_order', 'query_logistics', 'refund', 'query_product'],
  no_answer_threshold:  3,
  transfer_keywords:    ['投诉', '举报', '曝光'],
})

const configRules = {
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
        if (!value || value.length === 0) {
          callback(new Error('至少启用一个工具'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 打开快速配置弹窗，并加载当前版本配置
async function openConfigDialog(agent) {
  currentAgentId.value  = agent.id
  configDialogVisible.value = true

  try {
    const res = await agentApi.getConfig(agent.id)
    const cfg = res.data || {}
    configForm.value.model               = cfg.model               || configForm.value.model
    configForm.value.system_prompt       = cfg.system_prompt       || DEFAULT_PROMPT
    configForm.value.temperature         = cfg.temperature         ?? 0.7
    configForm.value.max_tokens          = cfg.max_tokens          ?? 1024
    configForm.value.tools_enabled       = cfg.tools_enabled       || ['query_order', 'query_logistics', 'refund', 'query_product']
    configForm.value.no_answer_threshold = cfg.no_answer_threshold ?? 3
    configForm.value.transfer_keywords   = [...(cfg.transfer_keywords || ['投诉', '举报', '曝光'])]
  } catch {
    // 加载失败不影响弹窗打开，使用默认值
  }
}

function resetConfigForm() {
  configForm.value = {
    model:                'deepseek-v3.2-chat-private',
    system_prompt:        DEFAULT_PROMPT,
    temperature:          0.7,
    max_tokens:           1024,
    tools_enabled:        ['query_order', 'query_logistics', 'refund', 'query_product'],
    no_answer_threshold:  3,
    transfer_keywords:    ['投诉', '举报', '曝光'],
  }
  configFormRef.value?.clearValidate()
  kwInputVisible.value = false
  kwInputValue.value   = ''
}

// 保存草稿（更新现有草稿版本配置）
async function handleSaveDraft() {
  await configFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await agentApi.updateConfig(currentAgentId.value, {
        ...configForm.value,
      })
      ElMessage.success('草稿已保存')
      configDialogVisible.value = false
      fetchAgentList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '保存失败')
    } finally {
      submitting.value = false
    }
  })
}

// 保存并立即发布
async function handleSaveAndPublish() {
  await configFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await agentApi.updateConfig(currentAgentId.value, {
        ...configForm.value,
      })
      await agentApi.publishVersion(currentAgentId.value)

      ElMessage.success('已保存并发布，新配置立即生效！')
      configDialogVisible.value = false
      fetchAgentList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '发布失败')
    } finally {
      submitting.value = false
    }
  })
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
  if (val && !configForm.value.transfer_keywords.includes(val)) {
    configForm.value.transfer_keywords.push(val)
  }
  kwInputVisible.value = false
  kwInputValue.value   = ''
}

function removeTransferKeyword(kw) {
  configForm.value.transfer_keywords =
    configForm.value.transfer_keywords.filter(k => k !== kw)
}

// ==================== 工作流可视化 ====================
const graphVisible    = ref(false)
const graphContent    = ref('')
const graphFormat     = ref('mermaid')
const mermaidRef      = ref(null)
const currentAgentIdForGraph = ref(null)

async function openWorkflowGraph(agentId) {
  currentAgentIdForGraph.value = agentId
  graphVisible.value = true
  graphFormat.value  = 'mermaid'
  await renderGraph()
}

async function renderGraph() {
  try {
    const res = await agentApi.getWorkflowGraph(
      currentAgentIdForGraph.value,
      graphFormat.value
    )
    graphContent.value = res.data?.graph || ''

    if (graphFormat.value === 'mermaid') {
      await nextTick()
      await renderMermaid(graphContent.value)
    }
  } catch {
    ElMessage.error('获取工作流图失败')
  }
}

async function renderMermaid(code) {
  if (!mermaidRef.value) return
  try {
    const mermaid = (await import('mermaid')).default
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      flowchart: { curve: 'linear' },
    })
    const { svg } = await mermaid.render('agent-graph', code)
    mermaidRef.value.innerHTML = svg
  } catch {
    graphFormat.value = 'ascii'
    ElMessage.warning('Mermaid 渲染失败，已切换为 ASCII 模式')
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchAgentList()
})
</script>
<style scoped lang="scss">
.agent-list {
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
  background: #f0f9eb;
  border: 1px solid #b3e19d;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 20px;

  .el-icon {
    color: #67c23a;
    flex-shrink: 0;
    font-size: 16px;
  }

  strong {
    color: #303133;
  }
}

// Agent 卡片网格
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.agent-empty {
  grid-column: 1 / -1;
}

// Agent 卡片
.agent-card {
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
}

// 卡片头部
.agent-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.agent-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(91,138,245,0.15), rgba(91,138,245,0.05));
  color: #5b8af5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

// Agent 名称
.agent-name {
  font-size: 17px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 版本行
.agent-version-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
}

.version-icon {
  color: #909399;
  font-size: 14px;
}

.version-label {
  font-size: 13px;
  color: #909399;
}

// 配置信息
.agent-config {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 14px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 10px;

  &--tools {
    align-items: flex-start;
  }
}

.config-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  width: 68px;

  .el-icon {
    font-size: 13px;
  }
}

.config-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.model-value {
  color: #5b8af5;
  background: rgba(91, 138, 245, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.tools-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.text-placeholder {
  color: #c0c4cc;
  font-size: 12px;
}

// 统计数据
.agent-stats {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 0;
  margin-bottom: 14px;
}

.agent-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.agent-stat-divider {
  width: 1px;
  height: 28px;
  background: #e4e7ed;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

// 卡片底部操作
.agent-card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px solid #f5f7fa;
}

// 弹窗内表单
.slider-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.slider-value {
  font-size: 14px;
  font-weight: 700;
  color: #5b8af5;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.5;
}

// 工具选项
.tool-option {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;

  .el-icon {
    color: #67c23a;
  }
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

// 工作流图
.graph-wrap {
  min-height: 300px;
  overflow: auto;
}

.graph-ascii {
  background: #1a1a2e;
  color: #67c23a;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre;
  overflow-x: auto;
}

.graph-mermaid {
  display: flex;
  justify-content: center;
  padding: 16px;

  :deep(svg) {
    max-width: 100%;
    height: auto;
  }
}
</style>