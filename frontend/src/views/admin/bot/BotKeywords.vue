<template>
  <div class="bot-keywords">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">关键词管理</h2>
          <span class="page-sub">{{ botName || 'Bot' }} · 共 {{ total }} 个关键词</span>
        </div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新建关键词
      </el-button>
    </div>

    <!-- 说明横幅 -->
    <div class="tips-banner">
      <el-icon><InfoFilled /></el-icon>
      <span>
        关键词干预优先级 <strong>高于</strong> FAQ 知识库检索，触发关键词后直接执行配置的动作。
        优先级数值越大越先匹配。
      </span>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索关键词"
        :prefix-icon="Search"
        clearable
        style="width: 280px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-select
        v-model="filterMatchType"
        placeholder="全部匹配类型"
        clearable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option label="精确匹配" value="exact" />
        <el-option label="包含匹配" value="contains" />
        <el-option label="正则匹配" value="regex" />
      </el-select>
      <el-select
        v-model="filterStatus"
        placeholder="全部状态"
        clearable
        style="width: 120px"
        @change="handleSearch"
      >
        <el-option label="启用" :value="1" />
        <el-option label="停用" :value="0" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
      <el-button :icon="Refresh" @click="handleReset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="table-wrap" v-loading="loading">
      <el-table
        :data="keywordList"
        border
        stripe
        row-key="id"
        style="width: 100%"
      >
        <!-- 优先级 -->
        <el-table-column label="优先级" prop="priority" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small" round>{{ row.priority }}</el-tag>
          </template>
        </el-table-column>

        <!-- 关键词 -->
        <el-table-column label="关键词" min-width="140">
          <template #default="{ row }">
            <div class="keyword-cell">
              <el-tag type="primary" effect="dark" size="small">
                {{ row.keyword }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <!-- 匹配类型 -->
        <el-table-column label="匹配类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getMatchTypeTag(row.match_type)" size="small">
              {{ getMatchTypeLabel(row.match_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 触发动作 -->
        <el-table-column label="触发动作" min-width="280">
          <template #default="{ row }">
            <div class="actions-cell">
              <div
                v-for="(action, index) in row.actions"
                :key="index"
                class="action-tag"
              >
                <el-icon :size="13">
                  <component :is="getActionIcon(action.type)" />
                </el-icon>
                <span>{{ getActionLabel(action) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>

        <!-- 创建时间 -->
        <el-table-column label="创建时间" width="120" align="center">
          <template #default="{ row }">
            <span class="text-time">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="130" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :icon="Edit"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑关键词' : '新建关键词'"
      width="640px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="keyword-form"
      >
        <!-- 关键词 -->
        <el-form-item label="关键词" prop="keyword">
          <el-input
            v-model="form.keyword"
            placeholder="请输入触发关键词，如：退款、投诉"
            maxlength="100"
            show-word-limit
            clearable
          />
        </el-form-item>

        <!-- 匹配类型 -->
        <el-form-item label="匹配类型" prop="match_type">
          <el-radio-group v-model="form.match_type">
            <el-radio-button value="contains">包含匹配</el-radio-button>
            <el-radio-button value="exact">精确匹配</el-radio-button>
            <el-radio-button value="regex">正则匹配</el-radio-button>
          </el-radio-group>
          <div class="match-type-hint">
            <span v-if="form.match_type === 'contains'" class="hint-text">
              用户消息中 <strong>包含</strong> 该词即触发，如「退款」可匹配「我要退款」
            </span>
            <span v-else-if="form.match_type === 'exact'" class="hint-text">
              用户消息与该词 <strong>完全相同</strong> 才触发，适合精确指令
            </span>
            <span v-else class="hint-text">
              使用 <strong>正则表达式</strong> 匹配，适合复杂规则，如 <code>^投诉.*</code>
            </span>
          </div>
        </el-form-item>

        <!-- 优先级 -->
        <el-form-item label="优先级" prop="priority">
          <el-input-number
            v-model="form.priority"
            :min="1"
            :max="100"
            :step="1"
            style="width: 140px"
          />
          <span class="priority-hint">数值越大，优先级越高（1-100）</span>
        </el-form-item>

        <!-- 触发动作 -->
        <el-form-item label="触发动作" prop="actions">
          <div class="actions-editor">
            <div class="actions-list">
              <div
                v-for="(action, index) in form.actions"
                :key="index"
                class="action-item"
              >
                <!-- 动作类型选择 -->
                <el-select
                  v-model="action.type"
                  style="width: 130px"
                  size="small"
                  @change="onActionTypeChange(action)"
                >
                  <el-option label="💬 回复消息" value="reply" />
                  <el-option label="👤 转人工" value="transfer" />
                  <el-option label="📋 推荐FAQ" value="recommend_faq" />
                </el-select>

                <!-- 回复消息：输入内容 -->
                <el-input
                  v-if="action.type === 'reply'"
                  v-model="action.content"
                  placeholder="请输入回复内容"
                  size="small"
                  style="flex: 1"
                  maxlength="500"
                />

                <!-- 转人工：无需额外配置 -->
                <div
                  v-else-if="action.type === 'transfer'"
                  class="action-no-config"
                >
                  <el-icon><User /></el-icon>
                  <span>触发后立即转接人工客服</span>
                </div>

                <!-- 推荐FAQ：选择知识条目 -->
                <el-select
                  v-else-if="action.type === 'recommend_faq'"
                  v-model="action.faq_ids"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  placeholder="选择推荐的知识条目（最多5条）"
                  size="small"
                  style="flex: 1"
                  :max-collapse-tags="2"
                >
                  <el-option
                    v-for="item in faqOptions"
                    :key="item.id"
                    :label="item.title"
                    :value="item.id"
                  />
                </el-select>

                <!-- 删除动作 -->
                <el-button
                  type="danger"
                  link
                  :icon="Delete"
                  size="small"
                  :disabled="form.actions.length <= 1"
                  @click="removeAction(index)"
                />
              </div>
            </div>

            <!-- 添加动作 -->
            <el-button
              text
              type="primary"
              :icon="Plus"
              size="small"
              :disabled="form.actions.length >= 3"
              @click="addAction"
            >
              添加动作（最多 3 个）
            </el-button>
          </div>
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
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Search,
  Refresh,
  Edit,
  Delete,
  InfoFilled,
  User,
  ChatDotRound,
  List,
} from '@element-plus/icons-vue'
import { botApi, knowledgeApi } from '@/api/admin'
import dayjs from 'dayjs'

const route  = useRoute()
const router = useRouter()

const botId   = computed(() => Number(route.params.id))
const botName = ref('')

// ==================== 列表数据 ====================
const loading         = ref(false)
const keywordList     = ref([])
const total           = ref(0)
const page            = ref(1)
const pageSize        = ref(20)
const searchKeyword   = ref('')
const filterMatchType = ref('')
const filterStatus    = ref('')

async function fetchList() {
  loading.value = true
  try {
    const res = await botApi.getKeywords(botId.value, {
      page:       page.value,
      page_size:  pageSize.value,
      keyword:    searchKeyword.value   || undefined,
      match_type: filterMatchType.value || undefined,
      status:     filterStatus.value !== '' ? filterStatus.value : undefined,
    })
    keywordList.value = res.data || []
    total.value       = res.page_info?.total || 0
  } catch {
    ElMessage.error('获取关键词列表失败')
  } finally {
    loading.value = false
  }
}

// 获取 Bot 信息（用于展示名称）
async function fetchBotInfo() {
  try {
    const res = await botApi.getBots()
    const bot = (res.data || []).find(b => b.id === botId.value)
    botName.value = bot?.name || ''
  } catch {
    // 不影响主功能
  }
}

// 获取 FAQ 选项（用于推荐FAQ动作）
const faqOptions = ref([])
async function fetchFaqOptions() {
  try {
    // 先获取 Bot 信息，再根据知识库 ID 拉取条目
    const botRes = await botApi.getBots()
    const bot    = (botRes.data || []).find(b => b.id === botId.value)
    if (!bot?.knowledge_base_id) return

    const res = await knowledgeApi.getItems(bot.knowledge_base_id, {
      page:      1,
      page_size: 100,
    })
    faqOptions.value = res.data || []
  } catch {
    // 不影响主功能
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handleReset() {
  searchKeyword.value   = ''
  filterMatchType.value = ''
  filterStatus.value    = ''
  page.value            = 1
  fetchList()
}

// ==================== 状态快速切换 ====================
async function handleStatusChange(row) {
  try {
    await botApi.updateKeyword(botId.value, row.id, { status: row.status })
    ElMessage.success(row.status === 1 ? '已启用' : '已停用')
  } catch {
    // 回滚状态
    row.status = row.status === 1 ? 0 : 1
    ElMessage.error('状态更新失败')
  }
}

// ==================== 新建 / 编辑弹窗 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const isEdit        = ref(false)
const editId        = ref(null)
const formRef       = ref(null)

const defaultAction = () => ({ type: 'reply', content: '' })

const form = ref({
  keyword:    '',
  match_type: 'contains',
  priority:   1,
  actions:    [defaultAction()],
  status:     1,
})

const rules = {
  keyword: [
    { required: true, message: '请输入关键词', trigger: 'blur' },
    { min: 1, max: 100, message: '关键词长度 1-100 个字符', trigger: 'blur' },
  ],
  match_type: [
    { required: true, message: '请选择匹配类型', trigger: 'change' },
  ],
  priority: [
    { required: true, message: '请设置优先级', trigger: 'change' },
  ],
  actions: [
    {
      validator: (rule, value, callback) => {
        if (!value || value.length === 0) {
          callback(new Error('至少配置一个触发动作'))
          return
        }
        // 校验 reply 动作必须有内容
        for (const action of value) {
          if (action.type === 'reply' && !action.content?.trim()) {
            callback(new Error('回复消息动作的内容不能为空'))
            return
          }
          if (action.type === 'recommend_faq' && (!action.faq_ids || !action.faq_ids.length)) {
            callback(new Error('推荐FAQ动作至少选择一个知识条目'))
            return
          }
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

function openCreateDialog() {
  isEdit.value        = false
  editId.value        = null
  dialogVisible.value = true
}

function openEditDialog(row) {
  isEdit.value        = true
  editId.value        = row.id

  // 深拷贝 actions，避免直接修改列表数据
  form.value.keyword    = row.keyword
  form.value.match_type = row.match_type
  form.value.priority   = row.priority
  form.value.status     = row.status
  form.value.actions    = JSON.parse(JSON.stringify(row.actions || [defaultAction()]))

  dialogVisible.value   = true
}

function resetForm() {
  form.value = {
    keyword:    '',
    match_type: 'contains',
    priority:   1,
    actions:    [defaultAction()],
    status:     1,
  }
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true

    // 清理 actions 中无效字段
    const cleanActions = form.value.actions.map(action => {
      if (action.type === 'reply') {
        return { type: 'reply', content: action.content }
      }
      if (action.type === 'transfer') {
        return { type: 'transfer' }
      }
      if (action.type === 'recommend_faq') {
        return { type: 'recommend_faq', faq_ids: action.faq_ids }
      }
      return action
    })

    const payload = {
      ...form.value,
      actions: cleanActions,
    }

    try {
      if (isEdit.value) {
        await botApi.updateKeyword(botId.value, editId.value, payload)
        ElMessage.success('修改成功')
      } else {
        await botApi.createKeyword(botId.value, payload)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// ==================== 删除 ====================
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除关键词「${row.keyword}」？删除后不可恢复！`,
      '删除确认',
      {
        type:               'warning',
        confirmButtonText:  '确认删除',
        cancelButtonText:   '取消',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await botApi.deleteKeyword(botId.value, row.id)
    ElMessage.success('删除成功')
    if (keywordList.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch {
    // 用户取消不处理
  }
}

// ==================== 动作编辑 ====================
function addAction() {
  if (form.value.actions.length >= 3) return
  form.value.actions.push(defaultAction())
}

function removeAction(index) {
  if (form.value.actions.length <= 1) return
  form.value.actions.splice(index, 1)
}

function onActionTypeChange(action) {
  // 切换类型时清空旧字段
  delete action.content
  delete action.faq_ids
  if (action.type === 'reply') action.content = ''
  if (action.type === 'recommend_faq') action.faq_ids = []
}

// ==================== 工具函数 ====================

// 匹配类型
function getMatchTypeLabel(type) {
  const map = { exact: '精确匹配', contains: '包含匹配', regex: '正则匹配' }
  return map[type] || type
}

function getMatchTypeTag(type) {
  const map = { exact: 'danger', contains: 'primary', regex: 'warning' }
  return map[type] || 'info'
}

// 动作图标
function getActionIcon(type) {
  const map = {
    reply:         'ChatDotRound',
    transfer:      'User',
    recommend_faq: 'List',
  }
  return map[type] || 'ChatDotRound'
}

// 动作说明文字
function getActionLabel(action) {
  if (action.type === 'reply') {
    const content = action.content || ''
    return `回复：${content.length > 20 ? content.slice(0, 20) + '...' : content}`
  }
  if (action.type === 'transfer') {
    return '转接人工客服'
  }
  if (action.type === 'recommend_faq') {
    const count = action.faq_ids?.length || 0
    return `推荐 ${count} 条知识`
  }
  return action.type
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('MM-DD HH:mm')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchBotInfo()
  fetchFaqOptions()
  fetchList()
})
</script>
<style scoped lang="scss">
.bot-keywords {
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
  margin-bottom: 16px;

  .el-icon {
    color: #409eff;
    flex-shrink: 0;
    font-size: 16px;
  }

  strong {
    color: #303133;
  }
}

// 搜索栏
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

// 表格
.table-wrap {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  padding-bottom: 16px;
}

// 关键词单元格
.keyword-cell {
  display: flex;
  align-items: center;
}

// 动作单元格
.actions-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  padding: 3px 8px;
  border-radius: 4px;
  width: fit-content;

  .el-icon {
    color: #5b8af5;
  }
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

// 表单
.keyword-form {
  padding: 8px 0;
}

// 匹配类型提示
.match-type-hint {
  margin-top: 8px;

  .hint-text {
    font-size: 12px;
    color: #909399;
    line-height: 1.6;

    strong { color: #5b8af5; }
    code {
      background: #f5f7fa;
      padding: 1px 4px;
      border-radius: 3px;
      font-family: monospace;
      color: #e6a23c;
    }
  }
}

// 优先级提示
.priority-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

// 动作编辑器
.actions-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: border-color 0.2s;

  &:hover {
    border-color: #c6e2ff;
  }
}

.action-no-config {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  padding: 0 8px;

  .el-icon {
    color: #5b8af5;
  }
}
</style>