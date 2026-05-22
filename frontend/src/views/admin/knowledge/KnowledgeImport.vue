<template>
  <div class="knowledge-import">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">Excel 批量导入</h2>
          <span class="page-sub">{{ kbName || '知识库' }}</span>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：上传区域 -->
      <el-col :span="14">

        <!-- Step 1：下载模板 -->
        <div class="step-card">
          <div class="step-header">
            <div class="step-badge">1</div>
            <div class="step-info">
              <div class="step-title">下载导入模板</div>
              <div class="step-desc">请先下载标准模板，按格式填写知识条目后再上传</div>
            </div>
            <el-button type="primary" plain :icon="Download" @click="downloadTemplate">
              下载模板
            </el-button>
          </div>

          <!-- 列格式说明 -->
          <div class="column-tips">
            <div class="column-tip-title">Excel 列格式说明：</div>
            <el-table :data="columnDefs" border size="small" style="margin-top: 8px">
              <el-table-column label="列" prop="col" width="50" align="center" />
              <el-table-column label="字段" prop="field" width="120" />
              <el-table-column label="说明" prop="desc" />
              <el-table-column label="必填" prop="required" width="60" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                    {{ row.required ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- Step 2：上传文件 -->
        <div class="step-card">
          <div class="step-header">
            <div class="step-badge">2</div>
            <div class="step-info">
              <div class="step-title">上传 Excel 文件</div>
              <div class="step-desc">支持 .xlsx 格式，文件大小不超过 20MB</div>
            </div>
          </div>

          <!-- 上传组件 -->
          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :on-remove="handleFileRemove"
            :file-list="fileList"
          >
            <div class="upload-inner">
              <el-icon :size="48" class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽文件到此处，或 <em>点击上传</em></div>
              <div class="upload-hint">仅支持 .xlsx 格式，最大 20MB</div>
            </div>
          </el-upload>

          <!-- 已选文件信息 -->
          <div v-if="selectedFile" class="file-info">
            <el-icon class="file-icon"><Document /></el-icon>
            <div class="file-meta">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
            </div>
            <el-tag type="success" size="small">已选择</el-tag>
          </div>

          <!-- 导入选项 -->
          <div class="import-options" v-if="selectedFile">
            <div class="option-title">导入选项：</div>
            <el-checkbox v-model="importOptions.skipDuplicate">
              跳过重复条目（根据知识标题判断）
            </el-checkbox>
            <el-checkbox v-model="importOptions.updateExisting">
              更新已存在条目（有 ID 则更新，无 ID 则新增）
            </el-checkbox>
            <el-checkbox v-model="importOptions.autoVectorize">
              导入后自动向量化（立即生效）
            </el-checkbox>
          </div>

          <!-- 导入按钮 -->
          <div class="upload-actions">
            <el-button
              type="primary"
              :icon="Upload"
              size="large"
              :loading="importing"
              :disabled="!selectedFile"
              @click="handleImport"
            >
              {{ importing ? '导入中...' : '开始导入' }}
            </el-button>
            <el-button
              v-if="selectedFile"
              size="large"
              @click="handleClear"
            >
              清除文件
            </el-button>
          </div>
        </div>

        <!-- Step 3：查看结果 -->
        <div class="step-card" v-if="importResult">
          <div class="step-header">
            <div class="step-badge" :class="importResult.success ? 'badge-success' : 'badge-error'">
              {{ importResult.success ? '✓' : '!' }}
            </div>
            <div class="step-info">
              <div class="step-title">导入结果</div>
              <div class="step-desc">{{ importResult.message }}</div>
            </div>
          </div>

          <!-- 结果统计 -->
          <div class="result-stats">
            <div class="result-stat-item result-stat--total">
              <div class="result-stat-value">{{ importResult.total }}</div>
              <div class="result-stat-label">总条数</div>
            </div>
            <div class="result-stat-item result-stat--success">
              <div class="result-stat-value">{{ importResult.created }}</div>
              <div class="result-stat-label">新增</div>
            </div>
            <div class="result-stat-item result-stat--update">
              <div class="result-stat-value">{{ importResult.updated }}</div>
              <div class="result-stat-label">更新</div>
            </div>
            <div class="result-stat-item result-stat--skip">
              <div class="result-stat-value">{{ importResult.skipped }}</div>
              <div class="result-stat-label">跳过</div>
            </div>
            <div class="result-stat-item result-stat--fail">
              <div class="result-stat-value">{{ importResult.failed }}</div>
              <div class="result-stat-label">失败</div>
            </div>
          </div>

          <!-- 错误详情 -->
          <div v-if="importResult.errors?.length" class="error-list">
            <div class="error-list-title">
              <el-icon><Warning /></el-icon>
              失败条目详情（{{ importResult.errors.length }} 条）
            </div>
            <el-table
              :data="importResult.errors"
              border
              size="small"
              max-height="200"
            >
              <el-table-column label="行号" prop="row" width="70" align="center" />
              <el-table-column label="标题" prop="title" min-width="160" show-overflow-tooltip />
              <el-table-column label="失败原因" prop="reason" min-width="200" />
            </el-table>
          </div>

          <!-- 有失败时显示下载结果按钮 -->
          <div v-if="importResult.failed > 0" class="result-download">
            <el-button type="warning" :icon="Download" @click="downloadResultFile">
              下载结果文件（含失败原因标注）
            </el-button>
          </div>

          <!-- 后续操作 -->
          <div class="result-actions">
            <el-button type="primary" :icon="List" @click="goItems">
              查看条目列表
            </el-button>
            <el-button :icon="Refresh" @click="resetImport">
              继续导入
            </el-button>
          </div>
        </div>
      </el-col>

      <!-- 右侧：导入历史 + 注意事项 -->
      <el-col :span="10">

        <!-- 注意事项 -->
        <div class="tips-card">
          <div class="tips-title">
            <el-icon><InfoFilled /></el-icon>
            导入注意事项
          </div>
          <ul class="tips-list">
            <li>请使用系统提供的标准模板，自定义格式可能导致导入失败</li>
            <li>知识标题（C列）为必填项，答案内容（F列）为必填项</li>
            <li>相似问法（D列）多个问法请换行分隔</li>
            <li>标签（G列）多个标签请用英文逗号分隔，如：退款,售后</li>
            <li>A列填写已有知识 ID 则执行更新操作，留空则新增</li>
            <li>单次导入建议不超过 5000 条，过多可能超时</li>
            <li>导入后系统将自动触发向量化，大批量导入需等待几分钟</li>
          </ul>
        </div>

        <!-- 导入历史 -->
        <div class="history-card">
          <div class="history-title">
            <el-icon><Clock /></el-icon>
            最近导入记录
          </div>
          <div v-if="importHistory.length" class="history-list">
            <div
              v-for="(record, index) in importHistory"
              :key="index"
              class="history-item"
            >
              <div class="history-item-header">
                <el-icon class="history-icon">
                  <SuccessFilled v-if="record.success" style="color: #67c23a" />
                  <CircleCloseFilled v-else style="color: #f56c6c" />
                </el-icon>
                <span class="history-filename">{{ record.filename }}</span>
                <span class="history-time">{{ record.time }}</span>
              </div>
              <div class="history-item-stats">
                <span class="history-stat">共 {{ record.total }} 条</span>
                <span class="history-stat success">新增 {{ record.created }}</span>
                <span class="history-stat update">更新 {{ record.updated }}</span>
                <span v-if="record.failed" class="history-stat fail">
                  失败 {{ record.failed }}
                </span>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            description="暂无导入记录"
            :image-size="60"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import {
  ArrowLeft,
  Download,
  Upload,
  UploadFilled,
  Document,
  Warning,
  InfoFilled,
  Clock,
  SuccessFilled,
  CircleCloseFilled,
  List,
  Refresh,
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/admin'
import dayjs from 'dayjs'

const route  = useRoute()
const router = useRouter()

const kbId   = computed(() => Number(route.params.id))
const kbName = ref('')

// ==================== 列格式定义 ====================
const columnDefs = [
  { col: 'A', field: '知识 ID',   desc: '有则更新，留空则新增',           required: false },
  { col: 'B', field: '分类',      desc: '知识条目分类，如：退款、物流',    required: false },
  { col: 'C', field: '知识标题',  desc: '标准问题，即知识的主问法',        required: true  },
  { col: 'D', field: '相似问法',  desc: '多个相似问法，每行一个',          required: false },
  { col: 'E', field: '答案类型',  desc: 'text 或 html，默认 text',        required: false },
  { col: 'F', field: '答案内容',  desc: '知识条目的答案正文',              required: true  },
  { col: 'G', field: '标签',      desc: '多个标签用英文逗号分隔',          required: false },
]

// ==================== 文件上传 ====================
const uploadRef    = ref(null)
const fileList     = ref([])
const selectedFile = ref(null)

const importOptions = ref({
  skipDuplicate:  true,
  updateExisting: true,
  autoVectorize:  true,
})

function handleFileChange(file) {
  // 校验文件类型
  const isXlsx = file.raw?.type ===
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  if (!isXlsx) {
    ElMessage.error('只支持上传 .xlsx 格式的 Excel 文件！')
    uploadRef.value?.clearFiles()
    return
  }

  // 校验文件大小（20MB）
  const isLt20M = file.raw.size / 1024 / 1024 < 20
  if (!isLt20M) {
    ElMessage.error('文件大小不能超过 20MB！')
    uploadRef.value?.clearFiles()
    return
  }

  selectedFile.value = file.raw
  fileList.value = [file]
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

function handleFileRemove() {
  selectedFile.value = null
  fileList.value = []
}

function handleClear() {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
  fileList.value = []
}

// ==================== 导入操作 ====================
const importing    = ref(false)
const importResult = ref(null)

async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的 Excel 文件')
    return
  }

  importing.value = true
  importResult.value = null

  try {
    const res = await knowledgeApi.importItems(kbId.value, selectedFile.value)

    // 兼容两种响应：直接返回结果 or 返回 task_id（异步任务）
    if (res.data?.task_id) {
      // 异步任务模式：轮询任务状态
      const total = res.data.total || 0
      ElMessage.success(`导入任务已提交，共 ${total} 条，正在处理中...`)
      await pollTaskStatus(res.data.task_id)
    } else {
      // 同步返回结果
      handleImportResult(res.data, null)
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

// 轮询任务状态（异步导入）
async function pollTaskStatus(taskId) {
  const maxRetry = 60 // 最多等待 60 次（约 2 分钟）
  let retryCount = 0

  const poll = async () => {
    if (retryCount >= maxRetry) {
      ElMessage.warning('导入任务处理超时，请到条目列表查看导入结果')
      return
    }
    retryCount++

    try {
      const res = await knowledgeApi.getImportTask(taskId)
      if (res.data?.status === 'done') {
        handleImportResult(res.data, taskId)
      } else if (res.data?.status === 'failed') {
        importResult.value = {
          success: false,
          message: res.data?.error_msg || '导入任务执行失败',
          total: 0, created: 0, updated: 0, skipped: 0, failed: 0,
          errors: [],
          taskId: taskId,
        }
      } else {
        setTimeout(poll, 2000)
      }
    } catch {
      setTimeout(poll, 3000)
    }
  }

  await poll()
}

// 处理导入结果
function handleImportResult(data, taskId) {
  importResult.value = {
    success: true,
    message: `导入完成！共处理 ${data.total || 0} 条知识条目`,
    total:   data.total   || 0,
    created: data.succeeded || 0,
    updated: 0,
    skipped: 0,
    failed:  data.failed  || 0,
    errors:  [],
    taskId:  taskId,
  }

  // 保存到本地历史记录
  saveToHistory({
    filename: selectedFile.value?.name || 'unknown.xlsx',
    time:     dayjs().format('MM-DD HH:mm'),
    success:  data.failed === 0,
    total:    data.total   || 0,
    created:  data.succeeded || 0,
    updated:  0,
    failed:   data.failed  || 0,
  })

  // 清空已选文件
  handleClear()
}

// 下载错误报告
async function downloadResultFile() {
  if (!importResult.value?.taskId) return

  try {
    const taskId = importResult.value.taskId
    const token = localStorage.getItem('admin_token')
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

    const { default: axiosRaw } = await import('axios')

    const response = await axiosRaw.get(
      `${baseUrl}/api/v1/knowledge/import/download-result/${taskId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
        withCredentials: false,
      }
    )

    const contentType = response.headers['content-type'] || ''
    if (!contentType.includes('spreadsheetml') && !contentType.includes('octet-stream')) {
      const text = await response.data.text()
      const err = JSON.parse(text)
      ElMessage.error(err.detail || '下载失败')
      return
    }

    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `import_result_${taskId.slice(-8)}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    setTimeout(() => window.URL.revokeObjectURL(url), 1000)

    ElMessage.success('结果文件下载成功')
  } catch (e) {
    console.error('[downloadResultFile]', e)
    ElMessage.error('下载失败，请重试')
  }
}

// 重置导入（继续导入）
function resetImport() {
  importResult.value = null
  handleClear()
}

// ==================== 模板下载 ====================
async function downloadTemplate() {
  try {
    const token = localStorage.getItem('admin_token')
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/knowledge/bases/template`,
      { headers: { Authorization: `Bearer ${token}` } }
    )

    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '知识库导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch {
    ElMessage.error('模板下载失败，请参考右侧列格式说明手动创建')
  }
}

// ==================== 导入历史（本地存储） ====================
const importHistory = ref([])
const HISTORY_KEY   = computed(() => `import_history_kb_${kbId.value}`)

function saveToHistory(record) {
  const list = JSON.parse(localStorage.getItem(HISTORY_KEY.value) || '[]')
  list.unshift(record)
  // 最多保留 10 条
  const trimmed = list.slice(0, 10)
  localStorage.setItem(HISTORY_KEY.value, JSON.stringify(trimmed))
  importHistory.value = trimmed
}

function loadHistory() {
  const list = JSON.parse(localStorage.getItem(HISTORY_KEY.value) || '[]')
  importHistory.value = list
}

// ==================== 跳转 ====================
function goItems() {
  router.push(`/admin/knowledge/${kbId.value}/items`)
}

// ==================== 获取知识库名称 ====================
async function fetchKbName() {
  try {
    const res = await knowledgeApi.getBases()
    const kb  = (res.data || []).find(k => k.id === kbId.value)
    kbName.value = kb?.name || ''
  } catch {
    // 不影响主功能
  }
}

// ==================== 工具函数 ====================
function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024)        return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchKbName()
  loadHistory()
})
</script>
<style scoped lang="scss">
.knowledge-import {
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

// Step 卡片
.step-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
  margin-bottom: 16px;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.step-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b8af5, #3d6fd4);
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.badge-success {
    background: linear-gradient(135deg, #67c23a, #4fa021);
  }

  &.badge-error {
    background: linear-gradient(135deg, #f56c6c, #d14343);
  }
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.step-desc {
  font-size: 12px;
  color: #909399;
}

// 列格式说明
.column-tips {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 14px;
}

.column-tip-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 4px;
}

// 上传区域
.upload-area {
  width: 100%;
  margin-bottom: 12px;

  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    height: 140px;
    border: 2px dashed #dcdfe6;
    border-radius: 10px;
    transition: all 0.3s;

    &:hover {
      border-color: #5b8af5;
      background: rgba(91, 138, 245, 0.03);
    }
  }

  // 隐藏默认文件列表（用自定义展示）
  :deep(.el-upload-list) {
    display: none;
  }
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
}

.upload-icon {
  color: #c0c4cc;
  transition: color 0.3s;

  .el-upload-dragger:hover & {
    color: #5b8af5;
  }
}

.upload-text {
  font-size: 14px;
  color: #606266;

  em {
    font-style: normal;
    color: #5b8af5;
    font-weight: 500;
  }
}

.upload-hint {
  font-size: 12px;
  color: #c0c4cc;
}

// 已选文件信息
.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f0f9eb;
  border: 1px solid #b3e19d;
  border-radius: 8px;
  margin-bottom: 14px;
}

.file-icon {
  color: #67c23a;
  font-size: 20px;
  flex-shrink: 0;
}

.file-meta {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: #909399;
}

// 导入选项
.import-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.option-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 4px;
}

// 上传操作按钮
.upload-actions {
  display: flex;
  gap: 10px;
}

// 结果统计
.result-stats {
  display: flex;
  gap: 0;
  background: #f5f7fa;
  border-radius: 10px;
  padding: 16px 0;
  margin-bottom: 16px;
}

.result-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border-right: 1px solid #e4e7ed;

  &:last-child {
    border-right: none;
  }
}

.result-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.result-stat-label {
  font-size: 12px;
  color: #909399;
}

.result-stat--success .result-stat-value { color: #67c23a; }
.result-stat--update  .result-stat-value { color: #5b8af5; }
.result-stat--skip    .result-stat-value { color: #e6a23c; }
.result-stat--fail    .result-stat-value { color: #f56c6c; }

// 错误列表
.error-list {
  margin-bottom: 16px;
}

.error-list-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #f56c6c;
  margin-bottom: 8px;
}

// 结果操作
.result-actions {
  display: flex;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid #f5f7fa;
}

// 注意事项卡片
.tips-card {
  background: #fffbf0;
  border: 1px solid #fde68a;
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 16px;
}

.tips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 12px;

  .el-icon {
    color: #f59e0b;
  }
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;

  li {
    font-size: 13px;
    color: #78350f;
    line-height: 1.6;
  }
}

// 导入历史卡片
.history-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 18px 20px;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 14px;

  .el-icon {
    color: #909399;
  }
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: #ecf5ff;
  }
}

.history-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.history-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.history-filename {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 11px;
  color: #c0c4cc;
  flex-shrink: 0;
  white-space: nowrap;
}

.history-item-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 24px;
}

.history-stat {
  font-size: 12px;
  color: #909399;

  &.success { color: #67c23a; }
  &.update  { color: #5b8af5; }
  &.fail    { color: #f56c6c; }
}
</style>