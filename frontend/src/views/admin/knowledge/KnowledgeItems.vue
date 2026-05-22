<template>
  <div class="knowledge-items">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">{{ kbName || '知识条目管理' }}</h2>
          <span class="page-sub">共 {{ total }} 条知识条目</span>
        </div>
      </div>
      <div class="page-header-right">
        <el-button :icon="Upload" @click="goImport">Excel 导入</el-button>
        <el-button :icon="Search" @click="goSearch">检索测试</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">
          新建条目
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索知识标题或内容关键词"
        :prefix-icon="Search"
        clearable
        style="width: 320px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-select
        v-model="filterCategory"
        placeholder="全部分类"
        clearable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option
          v-for="cat in categoryList"
          :key="cat"
          :label="cat"
          :value="cat"
        />
      </el-select>
      <el-button type="primary" :icon="Search" @click="handleSearch">
        搜索
      </el-button>
      <el-button :icon="Refresh" @click="handleReset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="table-wrap" v-loading="loading">
      <div class="table-toolbar" v-if="selectedItems.length">
        <el-checkbox v-model="selectAll" @change="handleSelectAllChange" />
        <span class="selected-count">已选择 {{ selectedItems.length }} 项</span>
        <el-button type="danger" size="small" :loading="batchDeleting" @click="handleBatchDelete">
          批量删除
        </el-button>
      </div>
      <el-table
        :data="itemList"
        border
        stripe
        row-key="id"
        style="width: 100%"
        @row-click="handleRowClick"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="45" />

        <el-table-column type="index" label="#" width="55" align="center" />

        <el-table-column label="知识标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="item-title">
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="分类" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.category" type="info" size="small">
              {{ row.category }}
            </el-tag>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <el-table-column label="相似问法" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small" round>
              {{ row.similar_questions?.length || 0 }} 条
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="标签" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="tag-list" v-if="row.tags?.length">
              <el-tag
                v-for="tag in row.tags.slice(0, 3)"
                :key="tag"
                size="small"
                style="margin-right: 4px"
              >
                {{ tag }}
              </el-tag>
              <el-tag v-if="row.tags.length > 3" size="small" type="info">
                +{{ row.tags.length - 3 }}
              </el-tag>
            </div>
            <span v-else class="text-placeholder">—</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" round>
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="120" align="center">
          <template #default="{ row }">
            <span class="text-time">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :icon="Edit"
              @click.stop="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :icon="Delete"
              @click.stop="handleDelete(row)"
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

    <!-- 新建/编辑抽屉 -->
    <KnowledgeItemEdit
      v-model="editDrawerVisible"
      :item="editingItem"
      :kb-id="kbId"
      :category-list="categoryList"
      @saved="fetchList"
    />

    <!-- 详情抽屉（点击行查看） -->
    <el-drawer
      v-model="drawerVisible"
      title="条目详情"
      size="480px"
      direction="rtl"
    >
      <div v-if="currentItem" class="item-detail">
        <div class="detail-section">
          <div class="detail-label">知识标题</div>
          <div class="detail-value title">{{ currentItem.title }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">答案内容</div>
          <div class="detail-value content">{{ currentItem.content }}</div>
        </div>

        <div class="detail-section" v-if="currentItem.similar_questions?.length">
          <div class="detail-label">
            相似问法（{{ currentItem.similar_questions.length }} 条）
          </div>
          <div class="similar-list">
            <div
              v-for="(q, i) in currentItem.similar_questions"
              :key="i"
              class="similar-item"
            >
              <span class="similar-index">{{ i + 1 }}</span>
              <span>{{ q }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section" v-if="currentItem.tags?.length">
          <div class="detail-label">标签</div>
          <div class="tag-list">
            <el-tag
              v-for="tag in currentItem.tags"
              :key="tag"
              size="small"
              style="margin-right: 6px"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <div class="detail-section">
          <div class="detail-label">分类 / 状态</div>
          <div class="detail-meta">
            <el-tag type="info" size="small">{{ currentItem.category || '未分类' }}</el-tag>
            <el-tag :type="currentItem.status === 1 ? 'success' : 'info'" size="small">
              {{ currentItem.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </div>
        </div>

        <div class="detail-section">
          <div class="detail-label">创建时间</div>
          <div class="detail-value">{{ formatDateFull(currentItem.created_at) }}</div>
        </div>

        <div class="drawer-footer">
          <el-button type="primary" :icon="Edit" @click="openEditFromDrawer">
            编辑条目
          </el-button>
          <el-button type="danger" plain :icon="Delete" @click="handleDeleteFromDrawer">
            删除条目
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Search,
  Refresh,
  Upload,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/admin'
import dayjs from 'dayjs'
import KnowledgeItemEdit from './KnowledgeItemEdit.vue'

const route  = useRoute()
const router = useRouter()

// 从路由参数取知识库 ID
const kbId   = computed(() => Number(route.params.id))
const kbName = ref('')

// ==================== 列表数据 ====================
const loading       = ref(false)
const itemList      = ref([])
const total         = ref(0)
const page          = ref(1)
const pageSize      = ref(20)
const searchKeyword = ref('')
const filterCategory= ref('')
const categoryList  = ref([])

// ==================== 批量选择 ====================
const selectedItems  = ref([])
const selectAll      = ref(false)
const batchDeleting  = ref(false)

function handleSelectionChange(selection) {
  selectedItems.value = selection
  selectAll.value = selection.length === itemList.value.length && itemList.value.length > 0
}

function handleSelectAllChange(val) {
  if (val) {
    // 实现全选
    itemList.value.forEach(row => {
      // already selected
    })
  } else {
    selectedItems.value = []
  }
}

async function handleBatchDelete() {
  if (!selectedItems.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedItems.value.length} 条知识条目吗？此操作不可恢复。`,
      '批量删除确认',
      { type: 'warning' }
    )
  } catch {
    return
  }

  batchDeleting.value = true
  try {
    const ids = selectedItems.value.map(item => item.id)
    await knowledgeApi.batchDeleteItems(ids)
    ElMessage.success('批量删除成功')
    selectedItems.value = []
    selectAll.value = false
    await fetchList()
  } catch (e) {
    ElMessage.error(e?.message || '批量删除失败')
  } finally {
    batchDeleting.value = false
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await knowledgeApi.getItems(kbId.value, {
      page:      page.value,
      page_size: pageSize.value,
      keyword:   searchKeyword.value || undefined,
      category:  filterCategory.value || undefined,
    })
    itemList.value = res.data || []
    total.value    = res.page_info?.total || 0

    // 提取分类列表（去重）
    const cats = itemList.value
      .map(i => i.category)
      .filter(Boolean)
    categoryList.value = [...new Set([...categoryList.value, ...cats])]
  } catch {
    ElMessage.error('获取知识条目失败')
  } finally {
    loading.value = false
  }
}

// 获取知识库信息（用于展示名称）
async function fetchKbInfo() {
  try {
    const res = await knowledgeApi.getBases()
    const kb  = (res.data || []).find(k => k.id === kbId.value)
    kbName.value = kb?.name || ''
  } catch {
    // 不影响主功能
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handleReset() {
  searchKeyword.value  = ''
  filterCategory.value = ''
  page.value           = 1
  fetchList()
}

// ==================== 跳转 ====================
function goImport() {
  router.push(`/admin/knowledge/${kbId.value}/import`)
}

function goSearch() {
  router.push(`/admin/knowledge/${kbId.value}/search`)
}

// ==================== 详情抽屉 ====================
const drawerVisible = ref(false)
const currentItem   = ref(null)

function handleRowClick(row) {
  currentItem.value   = row
  drawerVisible.value = true
}

function openEditFromDrawer() {
  drawerVisible.value = false
  nextTick(() => openEditDialog(currentItem.value))
}

async function handleDeleteFromDrawer() {
  drawerVisible.value = false
  await nextTick()
  handleDelete(currentItem.value)
}

// ==================== 新建 / 编辑抽屉 ====================
const editDrawerVisible = ref(false)
const editingItem = ref(null)

function openCreateDialog() {
  editingItem.value = null
  editDrawerVisible.value = true
}

function openEditDialog(row) {
  editingItem.value = row
  editDrawerVisible.value = true
}

// ==================== 删除 ====================
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除知识条目「${row.title}」？删除后不可恢复！`,
      '删除确认',
      {
        type:                'warning',
        confirmButtonText:   '确认删除',
        cancelButtonText:    '取消',
        confirmButtonClass:  'el-button--danger',
      }
    )
    await knowledgeApi.deleteItem(row.id)
    ElMessage.success('删除成功')
    // 如果当前页只剩一条且不是第一页，跳上一页
    if (itemList.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch {
    // 用户取消不处理
  }
}

// ==================== 工具函数 ====================
function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('MM-DD HH:mm')
}

function formatDateFull(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchKbInfo()
  fetchList()
})
</script>
<style scoped lang="scss">
.knowledge-items {
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
  gap: 8px;
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
  padding: 0 0 16px;
  overflow: hidden;
}

.item-title {
  font-weight: 500;
  color: #303133;
  cursor: pointer;

  &:hover {
    color: #5b8af5;
  }
}

.text-placeholder {
  color: #c0c4cc;
  font-size: 13px;
}

.text-time {
  font-size: 12px;
  color: #909399;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

// 分页
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px 0;
}

// 表单
.item-form {
  padding: 8px 0;
}

// 相似问法编辑器
.similar-questions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.similar-question-item {
  display: flex;
  align-items: center;
  gap: 8px;
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
.item-detail {
  padding: 0 4px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.detail-section {
  padding: 16px 0;
  border-bottom: 1px solid #f5f7fa;

  &:last-child {
    border-bottom: none;
  }
}

.detail-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;

  &.title {
    font-weight: 600;
    font-size: 15px;
  }

  &.content {
    white-space: pre-wrap;
    background: #f5f7fa;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 13px;
    color: #606266;
  }
}

.detail-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.similar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

.similar-index {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #5b8af5;
  color: #ffffff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.drawer-footer {
  padding-top: 20px;
  display: flex;
  gap: 10px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e4e7ed;
  border-bottom: none;
}

.selected-count {
  font-size: 13px;
  color: #606266;
  flex: 1;
}
</style>