<template>
  <div class="knowledge-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">知识库管理</h2>
        <span class="page-sub">共 {{ total }} 个知识库</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新建知识库
      </el-button>
    </div>

    <!-- 知识库卡片列表 -->
    <div v-loading="loading" class="kb-grid">
      <div
        v-for="kb in kbList"
        :key="kb.id"
        class="kb-card"
      >
        <!-- 卡片头部 -->
        <div class="kb-card-header">
          <div class="kb-icon">
            <el-icon :size="28"><Collection /></el-icon>
          </div>
          <div class="kb-status">
            <el-tag
              :type="kb.status === 1 ? 'success' : 'info'"
              size="small"
              round
            >
              {{ kb.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="kb-card-body">
          <div class="kb-name">{{ kb.name }}</div>
          <div class="kb-desc">{{ kb.description || '暂无描述' }}</div>

          <!-- 统计数据 -->
          <div class="kb-stats">
            <div class="kb-stat-item">
              <span class="stat-value">{{ formatCount(kb.item_count) }}</span>
              <span class="stat-label">知识条目</span>
            </div>
            <div class="kb-stat-divider"></div>
            <div class="kb-stat-item">
              <span class="stat-value">{{ formatCount(kb.vector_count) }}</span>
              <span class="stat-label">向量数量</span>
            </div>
            <div class="kb-stat-divider"></div>
            <div class="kb-stat-item">
              <span class="stat-value">{{ formatDate(kb.created_at) }}</span>
              <span class="stat-label">创建时间</span>
            </div>
          </div>
        </div>

        <!-- 卡片操作 -->
        <div class="kb-card-footer">
          <el-button
            type="primary"
            plain
            size="small"
            :icon="List"
            @click="goItems(kb)"
          >
            条目管理
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Upload"
            @click="goImport(kb)"
          >
            导入
          </el-button>
          <el-button
            plain
            size="small"
            :icon="Search"
            @click="goSearch(kb)"
          >
            检索测试
          </el-button>
          <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, kb)">
            <el-button plain size="small" :icon="MoreFilled" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit" :icon="Edit">
                  编辑信息
                </el-dropdown-item>
                <el-dropdown-item
                  :command="kb.status === 1 ? 'disable' : 'enable'"
                  :icon="kb.status === 1 ? CircleClose : CircleCheck"
                >
                  {{ kb.status === 1 ? '停用' : '启用' }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 新建卡片入口 -->
      <div class="kb-card kb-card--add" @click="openCreateDialog">
        <el-icon :size="36" class="add-icon"><Plus /></el-icon>
        <span class="add-text">新建知识库</span>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && kbList.length === 0"
        description="暂无知识库，点击右上角新建"
        :image-size="100"
        class="kb-empty"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑知识库' : '新建知识库'"
      width="500px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        class="kb-form"
      >
        <el-form-item label="知识库名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入知识库名称"
            maxlength="50"
            show-word-limit
            clearable
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入知识库描述（可选）"
            :rows="3"
            maxlength="200"
            show-word-limit
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
  Collection,
  List,
  Upload,
  Search,
  MoreFilled,
  Edit,
  CircleClose,
  CircleCheck,
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/admin'
import dayjs from 'dayjs'

const router = useRouter()

// ==================== 列表数据 ====================
const loading  = ref(false)
const kbList   = ref([])
const total    = ref(0)

async function fetchList() {
  loading.value = true
  try {
    const res = await knowledgeApi.getBases()
    kbList.value = res.data || []
    total.value  = kbList.value.length
  } catch {
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

// ==================== 跳转 ====================
function goItems(kb) {
  router.push(`/admin/knowledge/${kb.id}/items`)
}

function goImport(kb) {
  router.push(`/admin/knowledge/${kb.id}/import`)
}

function goSearch(kb) {
  router.push(`/admin/knowledge/${kb.id}/search`)
}

// ==================== 新建 / 编辑弹窗 ====================
const dialogVisible = ref(false)
const submitting    = ref(false)
const isEdit        = ref(false)
const editId        = ref(null)
const formRef       = ref(null)

const form = ref({
  name:        '',
  description: '',
})

const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度 2-50 个字符', trigger: 'blur' },
  ],
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  dialogVisible.value = true
}

function openEditDialog(kb) {
  isEdit.value        = true
  editId.value        = kb.id
  form.value.name        = kb.name
  form.value.description = kb.description || ''
  dialogVisible.value = true
}

function resetForm() {
  form.value = { name: '', description: '' }
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await knowledgeApi.updateBase(editId.value, form.value)
        ElMessage.success('修改成功')
      } else {
        await knowledgeApi.createBase(form.value)
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

// ==================== 更多操作 ====================
async function handleCommand(command, kb) {
  if (command === 'edit') {
    openEditDialog(kb)
    return
  }

  if (command === 'enable' || command === 'disable') {
    const newStatus = command === 'enable' ? 1 : 0
    const label     = command === 'enable' ? '启用' : '停用'
    try {
      await ElMessageBox.confirm(
        `确认要${label}知识库「${kb.name}」吗？`,
        '提示',
        { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
      )
      await knowledgeApi.updateBase(kb.id, { status: newStatus })
      ElMessage.success(`已${label}`)
      fetchList()
    } catch {
      // 用户取消，不处理
    }
  }
}

// ==================== 工具函数 ====================
function formatCount(num) {
  if (num == null) return '0'
  if (num >= 10000) return `${(num / 10000).toFixed(1)}w`
  return num.toString()
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('MM-DD')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchList()
})
</script>
<style scoped lang="scss">
.knowledge-list {
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

// 知识库卡片网格
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.kb-empty {
  grid-column: 1 / -1;
}

// 知识库卡片
.kb-card {
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
    min-height: 200px;
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

  .kb-card--add:hover & {
    transform: rotate(90deg);
  }
}

.add-text {
  font-size: 14px;
  font-weight: 500;
}

// 卡片头部
.kb-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.kb-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: rgba(91, 138, 245, 0.1);
  color: #5b8af5;
  display: flex;
  align-items: center;
  justify-content: center;
}

// 卡片内容
.kb-card-body {
  flex: 1;
  margin-bottom: 16px;
}

.kb-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

// 统计数据
.kb-stats {
  display: flex;
  align-items: center;
  gap: 0;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 0;
}

.kb-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.kb-stat-divider {
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
.kb-card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid #f5f7fa;
  flex-wrap: wrap;
}

// 表单
.kb-form {
  padding: 8px 0;
}
</style>