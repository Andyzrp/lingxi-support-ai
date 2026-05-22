<template>
  <div class="bot-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">Bot 管理</h2>
        <span class="page-sub">共 {{ botList.length }} 个 Bot</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新建 Bot
      </el-button>
    </div>

    <!-- Bot 卡片列表 -->
    <div v-loading="loading" class="bot-grid">
      <div
        v-for="bot in botList"
        :key="bot.id"
        class="bot-card"
      >
        <!-- 卡片头部 -->
        <div class="bot-card-header">
          <div class="bot-icon">
            <el-icon :size="28"><Service /></el-icon>
          </div>
          <div class="bot-header-right">
            <el-tag
              :type="bot.status === 1 ? 'success' : 'info'"
              size="small"
              round
            >
              {{ bot.status === 1 ? '启用' : '停用' }}
            </el-tag>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, bot)">
              <el-button text :icon="MoreFilled" size="small" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit" :icon="Edit">
                    编辑 Bot
                  </el-dropdown-item>
                  <el-dropdown-item command="keywords" :icon="Key">
                    关键词管理
                  </el-dropdown-item>
                  <el-dropdown-item
                    :command="bot.status === 1 ? 'disable' : 'enable'"
                    :icon="bot.status === 1 ? CircleClose : CircleCheck"
                  >
                    {{ bot.status === 1 ? '停用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item
                    command="delete"
                    :icon="Delete"
                    style="color: #f56c6c"
                  >
                    删除 Bot
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- Bot 名称 -->
        <div class="bot-name">{{ bot.name }}</div>
        <div class="bot-desc">{{ bot.no_answer_reply || '暂无兜底回复配置' }}</div>

        <!-- 配置信息 -->
        <div class="bot-config">
          <!-- 相似度阈值 -->
          <div class="config-item">
            <div class="config-label">
              <el-icon><Aim /></el-icon>
              相似度阈值
            </div>
            <div class="config-value-wrap">
              <el-progress
                :percentage="Math.round(bot.similarity_threshold * 100)"
                :color="getThresholdColor(bot.similarity_threshold)"
                :stroke-width="6"
                :show-text="false"
                style="flex: 1"
              />
              <span
                class="config-value"
                :style="{ color: getThresholdColor(bot.similarity_threshold) }"
              >
                {{ bot.similarity_threshold }}
              </span>
            </div>
          </div>

          <!-- 关联知识库 -->
          <div class="config-item">
            <div class="config-label">
              <el-icon><Collection /></el-icon>
              关联知识库
            </div>
            <el-tag
              :type="bot.knowledge_base_status === 1 ? 'success' : 'danger'"
              size="small"
              effect="plain"
            >
              {{ bot.knowledge_base_status === 1 ? '●' : '○' }}
              {{ bot.knowledge_base_name || getKbName(bot.knowledge_base_id) }}
            </el-tag>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="bot-stats">
          <div class="bot-stat-item">
            <span class="stat-value">{{ bot.keyword_count || 0 }}</span>
            <span class="stat-label">关键词</span>
          </div>
          <div class="bot-stat-divider"></div>
          <div class="bot-stat-item">
            <span class="stat-value">
              {{ bot.today_sessions || 0 }}
            </span>
            <span class="stat-label">今日会话</span>
          </div>
          <div class="bot-stat-divider"></div>
          <div class="bot-stat-item">
            <span class="stat-value">
              {{ bot.resolve_rate != null
                  ? `${(bot.resolve_rate * 100).toFixed(0)}%`
                  : '--' }}
            </span>
            <span class="stat-label">解决率</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="bot-card-footer">
          <el-button
            type="primary"
            plain
            size="small"
            :icon="Key"
            @click="goKeywords(bot)"
          >
            关键词管理
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Edit"
            @click="openEditDialog(bot)"
          >
            编辑配置
          </el-button>
        </div>
      </div>

      <!-- 新建卡片入口 -->
      <div class="bot-card bot-card--add" @click="openCreateDialog">
        <el-icon :size="36" class="add-icon"><Plus /></el-icon>
        <span class="add-text">新建 Bot</span>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && botList.length === 0"
        description="暂无 Bot，点击右上角新建"
        :image-size="100"
        class="bot-empty"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑 Bot 配置' : '新建 Bot'"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
        class="bot-form"
      >
        <!-- Bot 名称 -->
        <el-form-item label="Bot 名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入 Bot 名称"
            maxlength="50"
            show-word-limit
            clearable
          />
        </el-form-item>

        <!-- 关联知识库 -->
        <el-form-item label="关联知识库" prop="knowledge_base_id">
          <el-select
            v-model="form.knowledge_base_id"
            placeholder="请选择关联的知识库"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="kb in kbList"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            >
              <div class="kb-option">
                <span>{{ kb.name }}</span>
                <span class="kb-option-count">{{ kb.item_count || 0 }} 条</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 相似度阈值 -->
        <el-form-item label="相似度阈值" prop="similarity_threshold">
          <div class="threshold-wrap">
            <el-slider
              v-model="form.similarity_threshold"
              :min="0.5"
              :max="1.0"
              :step="0.01"
              :show-tooltip="true"
              style="flex: 1"
            />
            <el-input-number
              v-model="form.similarity_threshold"
              :min="0.5"
              :max="1.0"
              :step="0.01"
              :precision="2"
              size="small"
              style="width: 90px; margin-left: 12px"
            />
          </div>
          <div class="threshold-hint">
            <el-icon :color="getThresholdColor(form.similarity_threshold)">
              <InfoFilled />
            </el-icon>
            <span :style="{ color: getThresholdColor(form.similarity_threshold) }">
              {{ getThresholdHint(form.similarity_threshold) }}
            </span>
          </div>
        </el-form-item>

        <!-- 兜底回复 -->
        <el-form-item label="兜底回复" prop="no_answer_reply">
          <el-input
            v-model="form.no_answer_reply"
            type="textarea"
            placeholder="当 Bot 无法匹配知识库时的默认回复"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Service,
  MoreFilled,
  Edit,
  Delete,
  Key,
  CircleClose,
  CircleCheck,
  Collection,
  Aim,
  InfoFilled,
} from '@element-plus/icons-vue'
import { botApi, knowledgeApi } from '@/api/admin'

const router = useRouter()

// ==================== 列表数据 ====================
const loading = ref(false)
const botList = ref([])
const kbList  = ref([])

async function fetchBotList() {
  loading.value = true
  try {
    const res = await botApi.getBots()
    botList.value = res.data || []
  } catch {
    ElMessage.error('获取 Bot 列表失败')
  } finally {
    loading.value = false
  }
}

// 获取知识库列表（用于下拉选择 + 名称展示）
async function fetchKbList() {
  try {
    const res = await knowledgeApi.getBases()
    kbList.value = (res.data || []).filter(kb => kb.status === 1)
  } catch {
    // 不影响主功能
  }
}

// 根据 ID 获取知识库名称
function getKbName(kbId) {
  if (!kbId) return '未关联'
  const kb = kbList.value.find(k => k.id === kbId)
  return kb?.name || `知识库 #${kbId}`
}

// ==================== 阈值样式 ====================
function getThresholdColor(val) {
  if (val >= 0.90) return '#f56c6c'
  if (val >= 0.80) return '#67c23a'
  return '#e6a23c'
}

function getThresholdHint(val) {
  if (val >= 0.90) return '严格模式：精确匹配，召回率低，建议补充更多相似问法'
  if (val >= 0.80) return '推荐模式：平衡精确与召回，适合大多数场景'
  return '宽松模式：召回率高，可能匹配不相关内容，谨慎使用'
}

// ==================== 跳转 ====================
function goKeywords(bot) {
  router.push(`/admin/bots/${bot.id}/keywords`)
}

// ==================== 新建 / 编辑弹窗 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const isEdit        = ref(false)
const editId        = ref(null)
const formRef       = ref(null)

const form = ref({
  name:                 '',
  knowledge_base_id:    null,
  similarity_threshold: 0.85,
  no_answer_reply:      '抱歉，我暂时无法回答这个问题，为您转接人工客服。',
  status:               1,
})

const rules = {
  name: [
    { required: true, message: '请输入 Bot 名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度 2-50 个字符', trigger: 'blur' },
  ],
  knowledge_base_id: [
    { required: true, message: '请选择关联的知识库', trigger: 'change' },
  ],
  similarity_threshold: [
    { required: true, message: '请设置相似度阈值', trigger: 'change' },
  ],
  no_answer_reply: [
    { required: true, message: '请输入兜底回复内容', trigger: 'blur' },
  ],
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  dialogVisible.value = true
}

function openEditDialog(bot) {
  isEdit.value                       = true
  editId.value                       = bot.id
  form.value.name                    = bot.name
  form.value.knowledge_base_id       = bot.knowledge_base_id
  form.value.similarity_threshold    = bot.similarity_threshold
  form.value.no_answer_reply         = bot.no_answer_reply
  form.value.status                  = bot.status
  dialogVisible.value                = true
}

function resetForm() {
  form.value = {
    name:                 '',
    knowledge_base_id:    null,
    similarity_threshold: 0.85,
    no_answer_reply:      '抱歉，我暂时无法回答这个问题，为您转接人工客服。',
    status:               1,
  }
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await botApi.updateBot(editId.value, form.value)
        ElMessage.success('修改成功')
      } else {
        await botApi.createBot(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchBotList()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// ==================== 更多操作 ====================
async function handleCommand(command, bot) {
  if (command === 'edit') {
    openEditDialog(bot)
    return
  }

  if (command === 'keywords') {
    goKeywords(bot)
    return
  }

  if (command === 'enable' || command === 'disable') {
    const newStatus = command === 'enable' ? 1 : 0
    const label     = command === 'enable' ? '启用' : '停用'
    try {
      await ElMessageBox.confirm(
        `确认要${label} Bot「${bot.name}」吗？`,
        '提示',
        {
          type:              'warning',
          confirmButtonText: '确认',
          cancelButtonText:  '取消',
        }
      )
      await botApi.updateBot(bot.id, { status: newStatus })
      ElMessage.success(`已${label}`)
      fetchBotList()
    } catch {
      // 用户取消不处理
    }
  }

  if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除 Bot「${bot.name}」吗？该操作不可恢复。`,
        '删除确认',
        { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
      )
      await botApi.deleteBot(bot.id)
      ElMessage.success('删除成功')
      fetchBotList()
    } catch (e) {
      if (e !== 'cancel') {
        const msg = e?.response?.data?.message || e?.response?.data?.detail || '删除失败'
        ElMessage.error(msg)
      }
    }
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchKbList()
  fetchBotList()
})
</script>
<style scoped lang="scss">
.bot-list {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
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

// Bot 卡片网格
.bot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.bot-empty {
  grid-column: 1 / -1;
}

// Bot 卡片
.bot-card {
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

  // 新建按钮卡片
  &--add {
    border: 2px dashed #dcdfe6;
    box-shadow: none;
    align-items: center;
    justify-content: center;
    gap: 12px;
    cursor: pointer;
    min-height: 240px;
    color: #c0c4cc;
    transition: all 0.2s;

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

  .bot-card--add:hover & {
    transform: rotate(90deg);
  }
}

.add-text {
  font-size: 14px;
  font-weight: 500;
}

// 卡片头部
.bot-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.bot-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: rgba(91, 138, 245, 0.1);
  color: #5b8af5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bot-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

// Bot 名称
.bot-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bot-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

// 配置信息
.bot-config {
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
}

.config-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  width: 76px;

  .el-icon {
    font-size: 13px;
  }
}

.config-value-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.config-value {
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

// 统计数据
.bot-stats {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 0;
  margin-bottom: 14px;
}

.bot-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.bot-stat-divider {
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
.bot-card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px solid #f5f7fa;
}

// 表单
.bot-form {
  padding: 8px 0;
}

// 阈值滑块
.threshold-wrap {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 0;
}

.threshold-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;
}

// 知识库下拉选项
.kb-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.kb-option-count {
  font-size: 12px;
  color: #c0c4cc;
}
</style>