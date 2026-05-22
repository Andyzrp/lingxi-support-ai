<template>
  <div class="annotation-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">数据标注</h2>
        <span class="page-sub">共 {{ total }} 条标注记录</span>
      </div>
      <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stat-row">
      <el-col :span="6">
        <div class="stat-card stat-card--blue">
          <div class="stat-icon">
            <el-icon :size="22"><Collection /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总标注数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--green">
          <div class="stat-icon">
            <el-icon :size="22"><CircleCheck /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.good || 0 }}</div>
            <div class="stat-label">
              好评标注
              <span class="stat-rate" v-if="stats.good_rate">
                {{ (stats.good_rate * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--red">
          <div class="stat-icon">
            <el-icon :size="22"><CircleClose /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.bad || 0 }}</div>
            <div class="stat-label">
              差评标注
              <span class="stat-rate" v-if="stats.bad_rate">
                {{ (stats.bad_rate * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--orange">
          <div class="stat-icon">
            <el-icon :size="22"><Remove /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.neutral || 0 }}</div>
            <div class="stat-label">中性标注</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-select
        v-model="filterLabel"
        placeholder="全部标签"
        clearable
        style="width: 140px"
        @change="handleSearch"
      >
        <el-option label="👍 好的回答" value="good" />
        <el-option label="👎 差的回答" value="bad" />
        <el-option label="😐 中性"     value="neutral" />
      </el-select>

      <el-input
        v-model="filterConvId"
        placeholder="按会话 ID 筛选"
        clearable
        style="width: 180px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />

      <el-button type="primary" :icon="Search" @click="handleSearch">
        搜索
      </el-button>
      <el-button :icon="Refresh" @click="handleReset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="table-wrap" v-loading="loading">
      <el-table
        :data="annotationList"
        border
        stripe
        style="width: 100%"
      >
        <!-- 标注 ID -->
        <el-table-column label="ID" width="70" align="center">
          <template #default="{ row }">
            <span class="id-text">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <!-- 会话 ID -->
        <el-table-column label="会话" width="80" align="center">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              size="small"
              @click="goConversation(row.conversation_id)"
            >
              #{{ row.conversation_id }}
            </el-button>
          </template>
        </el-table-column>

        <!-- 原始消息内容 -->
        <el-table-column label="原始回答" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="original-content">
              {{ row.original_content || '—' }}
            </span>
          </template>
        </el-table-column>

        <!-- 标注标签 -->
        <el-table-column label="标注结果" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getLabelType(row.label)"
              size="small"
              round
            >
              {{ getLabelText(row.label) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 修正答案 -->
        <el-table-column label="修正答案" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.correct_answer" class="correct-answer">
              {{ row.correct_answer }}
            </span>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <!-- 标注人 -->
        <el-table-column label="标注人" width="110" align="center">
          <template #default="{ row }">
            <span class="annotator">
              {{ row.annotator_name || `管理员${row.annotator_id}` }}
            </span>
          </template>
        </el-table-column>

        <!-- 备注 -->
        <el-table-column label="备注" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="remark-text">{{ row.remark || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 标注时间 -->
        <el-table-column label="标注时间" width="160" align="center">
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

    <!-- 编辑标注弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑标注"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <!-- 原始消息预览 -->
      <div class="original-preview" v-if="currentRow">
        <div class="preview-label">原始回答内容</div>
        <div class="preview-content">
          {{ currentRow.original_content || '暂无内容' }}
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        style="margin-top: 16px"
      >
        <!-- 标注标签 -->
        <el-form-item label="标注结果" prop="label">
          <el-radio-group v-model="form.label">
            <el-radio-button label="good">
              <el-icon><CircleCheck /></el-icon>
              好的回答
            </el-radio-button>
            <el-radio-button label="neutral">
              <el-icon><Remove /></el-icon>
              中性
            </el-radio-button>
            <el-radio-button label="bad">
              <el-icon><CircleClose /></el-icon>
              差的回答
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 修正答案（差评时必填）-->
        <el-form-item
          label="修正答案"
          prop="correct_answer"
          v-if="form.label === 'bad'"
        >
          <el-input
            v-model="form.correct_answer"
            type="textarea"
            placeholder="请输入正确的回答内容，用于模型微调"
            :rows="4"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <!-- 备注 -->
        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            placeholder="可选，描述标注原因"
            maxlength="500"
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存修改
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
  Refresh,
  Search,
  Edit,
  Delete,
  Collection,
  CircleCheck,
  CircleClose,
  Remove,
} from '@element-plus/icons-vue'
import { annotationApi } from '@/api/admin'
import dayjs from 'dayjs'

const router = useRouter()

// ==================== 统计数据 ====================
const stats = ref({
  total:     0,
  good:      0,
  bad:       0,
  neutral:   0,
  good_rate: 0,
  bad_rate:  0,
})

async function fetchStats() {
  try {
    const res   = await annotationApi.getStats()
    stats.value = res.data || {}
  } catch {
    // 不影响主功能
  }
}

// ==================== 列表数据 ====================
const loading        = ref(false)
const annotationList = ref([])
const total          = ref(0)
const page           = ref(1)
const pageSize       = ref(20)
const filterLabel    = ref('')
const filterConvId   = ref('')

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page:            page.value,
      page_size:       pageSize.value,
      label:           filterLabel.value  || undefined,
      conversation_id: filterConvId.value
                         ? Number(filterConvId.value)
                         : undefined,
    }
    const res        = await annotationApi.getList(params)
    annotationList.value = res.data || []
    total.value          = res.page_info?.total || 0
  } catch {
    ElMessage.error('获取标注列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handleReset() {
  filterLabel.value  = ''
  filterConvId.value = ''
  page.value         = 1
  fetchList()
}

// ==================== 标签样式 ====================
function getLabelType(label) {
  const map = { good: 'success', bad: 'danger', neutral: 'warning' }
  return map[label] || 'info'
}

function getLabelText(label) {
  const map = { good: '👍 好的回答', bad: '👎 差的回答', neutral: '😐 中性' }
  return map[label] || label
}

// ==================== 跳转会话详情 ====================
function goConversation(convId) {
  router.push(`/admin/conversations/${convId}`)
}

// ==================== 编辑弹窗 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const currentRow    = ref(null)
const formRef       = ref(null)

const form = ref({
  label:          'good',
  correct_answer: '',
  remark:         '',
})

const rules = {
  label: [
    { required: true, message: '请选择标注结果', trigger: 'change' },
  ],
  correct_answer: [
    {
      validator: (rule, value, callback) => {
        if (form.value.label === 'bad' && !value?.trim()) {
          callback(new Error('差评标注必须填写修正答案'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function openEditDialog(row) {
  currentRow.value        = row
  form.value.label          = row.label          || 'good'
  form.value.correct_answer = row.correct_answer || ''
  form.value.remark         = row.remark         || ''
  dialogVisible.value     = true
}

function resetForm() {
  form.value = { label: 'good', correct_answer: '', remark: '' }
  formRef.value?.clearValidate()
  currentRow.value = null
}

async function handleSubmit() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await annotationApi.update(currentRow.value.id, {
        label:          form.value.label,
        correct_answer: form.value.label === 'bad'
                          ? form.value.correct_answer
                          : null,
        remark:         form.value.remark || null,
      })
      ElMessage.success('标注已更新')
      dialogVisible.value = false
      fetchList()
      fetchStats()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '更新失败')
    } finally {
      submitting.value = false
    }
  })
}

// ==================== 删除 ====================
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除该标注记录？删除后不可恢复！`,
      '删除确认',
      {
        type:               'warning',
        confirmButtonText:  '确认删除',
        cancelButtonText:   '取消',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await annotationApi.remove(row.id)
    ElMessage.success('删除成功')
    if (annotationList.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
    fetchStats()
  } catch {
    // 用户取消不处理
  }
}

// ==================== 工具函数 ====================
function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('MM-DD HH:mm')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchStats()
  fetchList()
})
</script>

<style scoped lang="scss">
.annotation-list {
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

  &--blue {
    border-left-color: #5b8af5;
    .stat-icon { background: rgba(91,138,245,0.1); color: #5b8af5; }
  }
  &--green {
    border-left-color: #67c23a;
    .stat-icon { background: rgba(103,194,58,0.1); color: #67c23a; }
  }
  &--red {
    border-left-color: #f56c6c;
    .stat-icon { background: rgba(245,108,108,0.1); color: #f56c6c; }
  }
  &--orange {
    border-left-color: #e6a23c;
    .stat-icon { background: rgba(230,162,60,0.1); color: #e6a23c; }
  }
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
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-rate {
  font-size: 11px;
  color: #5b8af5;
  background: rgba(91, 138, 245, 0.1);
  padding: 1px 5px;
  border-radius: 8px;
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

// 表格
.table-wrap {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  padding-bottom: 16px;
}

.id-text {
  font-size: 13px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.original-content {
  font-size: 13px;
  color: #606266;
}

.correct-answer {
  font-size: 13px;
  color: #67c23a;
  font-style: italic;
}

.text-placeholder {
  color: #c0c4cc;
  font-size: 12px;
}

.annotator {
  font-size: 13px;
  color: #606266;
}

.remark-text {
  font-size: 12px;
  color: #909399;
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

// 编辑弹窗
.original-preview {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 14px;
  border-left: 3px solid #5b8af5;
}

.preview-label {
  font-size: 11px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.preview-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 100px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}
</style>
