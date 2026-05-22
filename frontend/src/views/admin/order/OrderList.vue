<template>
  <div class="order-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">订单管理</h2>
        <span class="page-sub">共 {{ total }} 笔订单</span>
      </div>
      <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索订单号 / 用户名 / 商品名"
        :prefix-icon="Search"
        clearable
        style="width: 300px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-select
        v-model="filterStatus"
        placeholder="全部状态"
        clearable
        style="width: 140px"
        @change="handleSearch"
      >
        <el-option
          v-for="(item, val) in ORDER_STATUS"
          :key="val"
          :label="item.text"
          :value="Number(val)"
        >
          <div class="status-option">
            <el-tag :type="item.tag" size="small">{{ item.text }}</el-tag>
          </div>
        </el-option>
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

    <!-- 状态快捷筛选 Tab -->
    <div class="status-tabs">
      <div
        v-for="tab in statusTabs"
        :key="tab.value"
        class="status-tab"
        :class="{ active: filterStatus === tab.value }"
        @click="handleTabClick(tab.value)"
      >
        <span>{{ tab.label }}</span>
        <el-badge
          v-if="tab.count"
          :value="tab.count"
          :max="99"
          class="tab-badge"
        />
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrap" v-loading="loading">
      <el-table
        :data="orderList"
        border
        stripe
        row-key="id"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <!-- 订单号 -->
        <el-table-column label="订单号" min-width="200">
          <template #default="{ row }">
            <div class="order-no-cell">
              <span class="order-no">{{ row.order_no }}</span>
              <el-button
                text
                :icon="CopyDocument"
                size="small"
                @click.stop="copyOrderNo(row.order_no)"
              />
            </div>
          </template>
        </el-table-column>

        <!-- 商品信息 -->
        <el-table-column label="商品信息" min-width="220">
          <template #default="{ row }">
            <div class="product-cell">
              <el-image
                v-if="row.product_image"
                :src="row.product_image"
                :preview-src-list="[row.product_image]"
                fit="cover"
                class="product-img"
                @click.stop
              />
              <div class="product-meta">
                <div class="product-name">{{ row.product_name }}</div>
                <div class="product-price">
                  ¥{{ row.product_price }} × {{ row.quantity }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 用户信息 -->
        <el-table-column label="用户" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <span class="user-name">{{ row.username || row.user_id }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 金额 -->
        <el-table-column label="实付金额" width="110" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>

        <!-- 订单状态 -->
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="ORDER_STATUS[row.status]?.tag || 'info'"
              size="small"
              round
            >
              {{ ORDER_STATUS[row.status]?.text || '未知' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 创建时间 -->
        <el-table-column label="创建时间" width="160" align="center">
          <template #default="{ row }">
            <span class="text-time">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button
                type="primary"
                link
                size="small"
                :icon="View"
                @click.stop="openDetailDialog(row)"
              >
                详情
              </el-button>
              <el-dropdown
                trigger="click"
                @command="(cmd) => handleStatusChange(cmd, row)"
              >
                <span class="status-change-btn" @click.stop>
                  <el-button
                    type="warning"
                    link
                    size="small"
                    :icon="Edit"
                  >
                    改状态
                  </el-button>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="(item, val) in ORDER_STATUS"
                      :key="val"
                      :command="Number(val)"
                      :disabled="Number(val) === row.status"
                    >
                      <el-tag :type="item.tag" size="small">{{ item.text }}</el-tag>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
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

    <!-- 订单详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="680px"
      :close-on-click-modal="false"
    >
      <div v-if="currentOrder" class="order-detail">
        <!-- 状态流转进度条 -->
        <div class="status-steps">
          <el-steps
            :active="getStepActive(currentOrder.status)"
            finish-status="success"
            align-center
          >
            <el-step title="待付款" :icon="CreditCard" />
            <el-step title="已付款" :icon="CircleCheck" />
            <el-step title="已发货" :icon="Van" />
            <el-step title="已完成" :icon="SuccessFilled" />
          </el-steps>
          <!-- 特殊状态提示 -->
          <div
            v-if="[4, 5, 6].includes(currentOrder.status)"
            class="special-status"
          >
            <el-tag :type="ORDER_STATUS[currentOrder.status]?.tag" size="large">
              {{ ORDER_STATUS[currentOrder.status]?.text }}
            </el-tag>
          </div>
        </div>

        <el-divider />

        <!-- 基础信息 -->
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单号" :span="2">
            <div class="desc-order-no">
              <code>{{ currentOrder.order_no }}</code>
              <el-button
                text
                :icon="CopyDocument"
                size="small"
                @click="copyOrderNo(currentOrder.order_no)"
              />
            </div>
          </el-descriptions-item>

          <el-descriptions-item label="商品名称">
            {{ currentOrder.product_name }}
          </el-descriptions-item>

          <el-descriptions-item label="商品单价">
            ¥{{ currentOrder.product_price }}
          </el-descriptions-item>

          <el-descriptions-item label="购买数量">
            {{ currentOrder.quantity }} 件
          </el-descriptions-item>

          <el-descriptions-item label="实付金额">
            <span class="amount">¥{{ currentOrder.total_amount }}</span>
          </el-descriptions-item>

          <el-descriptions-item label="订单状态">
            <el-tag
              :type="ORDER_STATUS[currentOrder.status]?.tag"
              size="small"
              round
            >
              {{ ORDER_STATUS[currentOrder.status]?.text }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="创建时间">
            {{ formatDateFull(currentOrder.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">收货信息</el-divider>

        <!-- 收货地址 -->
        <el-descriptions
          v-if="currentOrder.address"
          :column="2"
          border
          size="small"
        >
          <el-descriptions-item label="收货人">
            {{ currentOrder.address.name }}
          </el-descriptions-item>

          <el-descriptions-item label="联系电话">
            {{ currentOrder.address.phone }}
          </el-descriptions-item>

          <el-descriptions-item label="收货地址" :span="2">
            {{ currentOrder.address.province }}
            {{ currentOrder.address.city }}
            {{ currentOrder.address.district }}
            {{ currentOrder.address.detail }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 物流信息（已发货时展示）-->
        <template v-if="currentOrder.status >= 2 && currentOrder.status !== 4">
          <el-divider content-position="left">物流信息</el-divider>
          <div v-if="logistics" class="logistics-wrap">
            <div class="logistics-header">
              <el-icon><Van /></el-icon>
              <span class="logistics-company">
                {{ logistics.logistics_company }}
              </span>
              <span class="logistics-no">单号：{{ logistics.logistics_no }}</span>
            </div>
            <el-timeline class="logistics-timeline">
              <el-timeline-item
                v-for="(track, index) in logistics.tracks"
                :key="index"
                :timestamp="track.time"
                :type="index === 0 ? 'primary' : ''"
                placement="top"
              >
                {{ track.content }}
              </el-timeline-item>
            </el-timeline>
          </div>
          <div v-else-if="loadingLogistics" class="logistics-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载物流信息...</span>
          </div>
          <div v-else class="logistics-empty">暂无物流信息</div>
        </template>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <!-- 状态操作按钮 -->
          <template v-if="currentOrder">
            <el-button
              v-if="currentOrder.status === 1"
              type="primary"
              :icon="Van"
              @click="quickStatusChange(currentOrder, 2)"
            >
              标记已发货
            </el-button>
            <el-button
              v-if="currentOrder.status === 2"
              type="success"
              :icon="SuccessFilled"
              @click="quickStatusChange(currentOrder, 3)"
            >
              标记已完成
            </el-button>
            <el-button
              v-if="currentOrder.status === 4"
              type="warning"
              :icon="RefreshLeft"
              @click="quickStatusChange(currentOrder, 5)"
            >
              确认退款
            </el-button>
          </template>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  View,
  Edit,
  CopyDocument,
  Van,
  CircleCheck,
  SuccessFilled,
  CreditCard,
  RefreshLeft,
  Loading,
} from '@element-plus/icons-vue'
import { adminOrderApi } from '@/api/admin'
import dayjs from 'dayjs'

// ==================== 订单状态枚举（与后端 Order.status 一致）====================
const ORDER_STATUS = {
  0: { text: '待付款',  tag: 'warning' },
  1: { text: '已付款',  tag: 'primary' },
  2: { text: '已发货',  tag: 'success' },
  3: { text: '已收货',  tag: 'info'    },
  4: { text: '退款中',  tag: 'danger'  },
  5: { text: '已退款',  tag: 'info'    },
  6: { text: '已取消',  tag: 'info'    },
}

// ==================== 状态快捷 Tab ====================
const statusTabs = computed(() => [
  { label: '全部',   value: null },
  { label: '待付款', value: 0    },
  { label: '已付款', value: 1    },
  { label: '已发货', value: 2    },
  { label: '已收货', value: 3    },
  { label: '退款中', value: 4, count: refundCount.value },
  { label: '已退款', value: 5    },
  { label: '已取消', value: 6    },
])

const refundCount = ref(0)

function handleTabClick(val) {
  filterStatus.value = val
  page.value = 1
  fetchList()
}

// ==================== 列表数据 ====================
const loading       = ref(false)
const orderList     = ref([])
const total         = ref(0)
const page          = ref(1)
const pageSize      = ref(20)
const searchKeyword = ref('')
const filterStatus  = ref(null)
const dateRange     = ref([])

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page:      page.value,
      page_size: pageSize.value,
      keyword:   searchKeyword.value || undefined,
      status:    filterStatus.value  !== null ? filterStatus.value : undefined,
      start_date: dateRange.value?.[0] || undefined,
      end_date:   dateRange.value?.[1] || undefined,
    }
    const res = await adminOrderApi.getOrders(params)
    orderList.value = res.data || []
    total.value     = res.page_info?.total || 0

    // 统计退款中数量
    refundCount.value = orderList.value.filter(o => o.status === 4).length
  } catch {
    ElMessage.error('获取订单列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handleReset() {
  searchKeyword.value = ''
  filterStatus.value  = null
  dateRange.value     = []
  page.value          = 1
  fetchList()
}

// ==================== 状态流转进度条 ====================
// 将订单状态映射到 Steps 的 active 步骤
function getStepActive(status) {
  const map = { 0: 0, 1: 1, 2: 2, 3: 3, 4: 0, 5: 1, 6: 1 }
  return map[status] ?? 0
}

// ==================== 订单详情弹窗 ====================
const detailDialogVisible = ref(false)
const currentOrder        = ref(null)
const logistics           = ref(null)
const loadingLogistics    = ref(false)

async function openDetailDialog(row) {
  currentOrder.value   = row
  logistics.value      = null
  detailDialogVisible.value = true

  // 已发货以上且不是退款中/已退款/已取消，加载物流
  if ([2, 3].includes(row.status)) {
    loadingLogistics.value = true
    try {
      const res = await adminOrderApi.getOrderDetail(row.order_no)
      // 物流信息从详情接口获取（或单独接口）
      logistics.value = res.data?.logistics || null
    } catch {
      logistics.value = null
    } finally {
      loadingLogistics.value = false
    }
  }
}

function handleRowClick(row) {
  openDetailDialog(row)
}

// ==================== 状态变更 ====================
async function handleStatusChange(newStatus, row) {
  if (newStatus === row.status) return

  const fromText = ORDER_STATUS[row.status]?.text || row.status
  const toText   = ORDER_STATUS[newStatus]?.text   || newStatus

  try {
    await ElMessageBox.confirm(
      `确认将订单「${row.order_no}」状态从「${fromText}」变更为「${toText}」？`,
      '状态变更确认',
      {
        type:              'warning',
        confirmButtonText: '确认变更',
        cancelButtonText:  '取消',
      }
    )
    await adminOrderApi.updateStatus(row.order_no, { status: newStatus })
    ElMessage.success(`订单状态已更新为「${toText}」`)
    fetchList()

    // 如果详情弹窗开着，同步更新状态
    if (currentOrder.value?.order_no === row.order_no) {
      currentOrder.value.status = newStatus
    }
  } catch {
    // 用户取消不处理
  }
}

// 详情弹窗内快捷状态变更
async function quickStatusChange(order, newStatus) {
  const toText = ORDER_STATUS[newStatus]?.text || newStatus
  try {
    await ElMessageBox.confirm(
      `确认将此订单标记为「${toText}」？`,
      '操作确认',
      {
        type:              'warning',
        confirmButtonText: '确认',
        cancelButtonText:  '取消',
      }
    )
    await adminOrderApi.updateStatus(order.order_no, { status: newStatus })
    ElMessage.success(`已标记为「${toText}」`)
    currentOrder.value.status = newStatus
    fetchList()
  } catch {
    // 用户取消不处理
  }
}

// ==================== 复制订单号 ====================
async function copyOrderNo(orderNo) {
  try {
    await navigator.clipboard.writeText(orderNo)
    ElMessage.success('订单号已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
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
  fetchList()
})
</script>
<style scoped lang="scss">
.order-list {
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
  margin-bottom: 12px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

// 状态快捷 Tab
.status-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 14px;
  padding: 0 4px;
  flex-wrap: wrap;
}

.status-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  background: #ffffff;
  border: 1px solid #e4e7ed;

  &:hover {
    color: #5b8af5;
    border-color: #5b8af5;
    background: rgba(91, 138, 245, 0.05);
  }

  &.active {
    color: #5b8af5;
    border-color: #5b8af5;
    background: rgba(91, 138, 245, 0.1);
    font-weight: 600;
  }
}

.tab-badge {
  :deep(.el-badge__content) {
    font-size: 10px;
    height: 16px;
    line-height: 16px;
    padding: 0 5px;
  }
}

// 表格
.table-wrap {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  padding-bottom: 16px;
}

// 订单号单元格
.order-no-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.order-no {
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: #5b8af5;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

// 商品信息单元格
.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.product-img {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  flex-shrink: 0;
  border: 1px solid #f0f0f0;
}

.product-meta {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 3px;
}

.product-price {
  font-size: 12px;
  color: #909399;
}

// 用户单元格
.user-cell {
  display: flex;
  align-items: center;
}

.user-name {
  font-size: 13px;
  color: #606266;
}

// 金额
.amount {
  font-size: 14px;
  font-weight: 700;
  color: #f56c6c;
}

.text-time {
  font-size: 12px;
  color: #909399;
}

// 下拉状态选项
.status-option {
  display: flex;
  align-items: center;
}

// 分页
.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.status-change-btn {
  display: inline-flex;
  align-items: center;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px 0;
}

// 订单详情弹窗
.order-detail {
  padding: 0 4px;
}

// 状态步骤条
.status-steps {
  padding: 10px 0 20px;
  position: relative;
}

.special-status {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

// 描述 - 订单号行
.desc-order-no {
  display: flex;
  align-items: center;
  gap: 6px;

  code {
    font-size: 12px;
    font-family: 'Courier New', monospace;
    color: #5b8af5;
    background: rgba(91, 138, 245, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
  }
}

// 物流信息
.logistics-wrap {
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
}

.logistics-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 14px;

  .el-icon {
    color: #5b8af5;
    font-size: 18px;
  }
}

.logistics-company {
  font-weight: 600;
  color: #303133;
}

.logistics-no {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.logistics-timeline {
  margin-left: 8px;

  :deep(.el-timeline-item__timestamp) {
    font-size: 12px;
  }

  :deep(.el-timeline-item__content) {
    font-size: 13px;
    color: #606266;
  }
}

.logistics-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 13px;
  padding: 12px;

  .el-icon {
    font-size: 18px;
  }
}

.logistics-empty {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 20px;
}

// 弹窗底部
.dialog-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}
</style>