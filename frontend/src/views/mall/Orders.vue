<template>
  <div class="orders-page">
    <Header />

    <div class="page-body">
      <div class="orders-inner">
        <!-- 页面标题 -->
        <div class="lx-page-header">
          <div>
            <h1 class="lx-page-title">我的订单</h1>
            <p class="lx-page-desc">查看和管理您的所有订单</p>
          </div>
        </div>

        <!-- 状态筛选 Tab -->
        <div class="status-tabs">
          <span
            v-for="tab in statusTabs"
            :key="tab.value"
            class="status-tab"
            :class="{ active: activeStatus === tab.value }"
            @click="switchStatus(tab.value)"
          >
            {{ tab.label }}
          </span>
        </div>

        <!-- 加载中 -->
        <div v-if="loading">
          <div v-for="i in 3" :key="i" class="order-skeleton">
            <el-skeleton :rows="4" animated />
          </div>
        </div>

        <!-- 订单列表 -->
        <template v-else-if="orders.length">
          <div
            v-for="order in orders"
            :key="order.order_no"
            class="order-card"
          >
            <!-- 订单头部 -->
            <div class="order-card-header">
              <div class="order-meta">
                <span class="order-no">订单号：{{ order.order_no }}</span>
                <span class="order-time">{{ formatTime(order.created_at) }}</span>
              </div>
              <el-tag
                :type="getOrderStatus(order.status).tag"
                size="small"
                round
              >
                {{ getOrderStatus(order.status).text }}
              </el-tag>
            </div>

            <!-- 商品信息 -->
            <div class="order-product-row">
              <img
                :src="order.product_image || PLACEHOLDER_IMG(order.product_id)"
                class="order-product-img"
                :alt="order.product_name"
              />
              <div class="order-product-info">
                <div class="order-product-name">{{ order.product_name }}</div>
                <div class="order-product-qty">× {{ order.quantity }}</div>
              </div>
              <div class="order-product-price">
                {{ formatPrice(order.total_amount) }}
              </div>
            </div>

            <!-- 收货地址 -->
            <div class="order-address" v-if="order.address">
              📍 {{ formatAddress(order.address) }}
            </div>

            <!-- 订单底部操作 -->
            <div class="order-card-footer">
              <div class="order-total">
                实付：<strong>{{ formatPrice(order.total_amount) }}</strong>
              </div>
              <div class="order-actions">
                <!-- 查看物流 -->
                <el-button
                  v-if="[2, 3].includes(order.status)"
                  size="small"
                  plain
                  @click="viewLogistics(order)"
                >
                  查看物流
                </el-button>

                <!-- 申请退款 -->
                <el-button
                  v-if="[1, 2].includes(order.status)"
                  size="small"
                  type="danger"
                  plain
                  @click="handleRefund(order)"
                >
                  申请退款
                </el-button>

                <!-- 咨询客服 -->
                <el-button
                  size="small"
                  type="primary"
                  class="lx-gradient-btn"
                  @click="contactService(order)"
                >
                  💬 咨询客服
                </el-button>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div class="pagination-wrap" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              background
              @current-change="fetchOrders"
            />
          </div>
        </template>

        <!-- 空状态 -->
        <div v-else class="lx-empty">
          <el-empty :description="emptyText">
            <el-button
              type="primary"
              class="lx-gradient-btn"
              @click="router.push('/mall/products')"
            >
              去购物
            </el-button>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 物流弹窗 -->
    <el-dialog
      v-model="showLogisticsDialog"
      title="物流信息"
      width="480px"
    >
      <div v-if="logisticsLoading" class="logistics-loading">
        <el-skeleton :rows="4" animated />
      </div>
      <div v-else-if="logistics" class="logistics-content">
        <div class="logistics-status">
          <span class="logistics-status-icon">🚚</span>
          <span class="logistics-status-text">{{ logistics.status_text }}</span>
        </div>
        <el-timeline class="logistics-timeline">
          <el-timeline-item
            v-for="(item, idx) in logistics.tracks"
            :key="idx"
            :timestamp="item.time"
            :type="idx === 0 ? 'primary' : ''"
          >
            {{ item.content }}
          </el-timeline-item>
        </el-timeline>
      </div>
      <div v-else class="lx-empty">
        <el-empty description="暂无物流信息" />
      </div>
    </el-dialog>

    <!-- 退款弹窗 -->
    <el-dialog
      v-model="showRefundDialog"
      title="申请退款"
      width="420px"
    >
      <div class="refund-body">
        <el-alert
          title="退款申请提交后将由客服审核处理"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        />
        <el-form
          ref="refundFormRef"
          :model="refundForm"
          label-width="80px"
        >
          <el-form-item label="退款原因" prop="reason"
            :rules="[{ required: true, message: '请选择退款原因', trigger: 'change' }]"
          >
            <el-select
              v-model="refundForm.reason"
              placeholder="请选择退款原因"
              style="width: 100%"
            >
              <el-option label="商品质量问题" value="质量问题" />
              <el-option label="收到商品与描述不符" value="描述不符" />
              <el-option label="不想要了" value="不想要" />
              <el-option label="物流问题" value="物流问题" />
              <el-option label="其他原因" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="补充说明">
            <el-input
              v-model="refundForm.remark"
              type="textarea"
              :rows="3"
              placeholder="请描述具体问题（选填）"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showRefundDialog = false">取消</el-button>
        <el-button
          type="danger"
          :loading="refunding"
          @click="submitRefund"
        >
          提交退款申请
        </el-button>
      </template>
    </el-dialog>

    <Footer />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { orderApi } from '@/api/order'
import { useChatStore } from '@/stores/chat'
import { formatPrice, formatTime, getOrderStatus } from '@/utils/format'
import { PLACEHOLDER_IMG } from '@/utils/constants'

const router    = useRouter()
const chatStore = useChatStore()

// ── 列表状态 ──────────────────────────────
const loading      = ref(false)
const orders       = ref([])
const total        = ref(0)
const page         = ref(1)
const pageSize     = ref(10)
const activeStatus = ref('')

// ── 物流弹窗 ──────────────────────────────
const showLogisticsDialog = ref(false)
const logisticsLoading    = ref(false)
const logistics           = ref(null)

// ── 退款弹窗 ──────────────────────────────
const showRefundDialog = ref(false)
const refundFormRef    = ref(null)
const currentOrder     = ref(null)
const refundForm       = ref({
  reason: '',
  remark: '',
})

// ── 状态Tab配置（与后端 ORDER_STATUS 一致）───────────────────────
const statusTabs = [
  { label: '全部',   value: '' },
  { label: '待付款', value: '0' },
  { label: '已付款', value: '1' },
  { label: '已发货', value: '2' },
  { label: '已收货', value: '3' },
  { label: '退款中', value: '4' },
  { label: '已退款', value: '5' },
  { label: '已取消', value: '6' },
]

const emptyText = computed(() => {
  const tab = statusTabs.find(t => t.value === activeStatus.value)
  return tab && tab.value ? `暂无${tab.label}订单` : '暂无订单记录'
})

// ── 格式化收货地址 ────────────────────────
function formatAddress(address) {
  if (!address) return ''
  if (typeof address === 'string') return address
  const { name, phone, province, city, district, detail } = address
  return [name, phone, province, city, district, detail]
    .filter(Boolean)
    .join(' ')
}

// ── 切换状态Tab ───────────────────────────
function switchStatus(value) {
  activeStatus.value = value
  page.value = 1
  fetchOrders()
}

// ── 获取订单列表 [1] ──────────────────────
async function fetchOrders() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (activeStatus.value !== '') {
      params.status = activeStatus.value
    }
    const res = await orderApi.getMyList(params)
    orders.value = res.data || []
    total.value  = res.page_info?.total || 0
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

// ── 查看物流 [1] ──────────────────────────
async function viewLogistics(order) {
  showLogisticsDialog.value = true
  logisticsLoading.value = true
  logistics.value = null
  try {
    const data = await orderApi.getLogistics(order.order_no)
    logistics.value = data
  } catch {
    logistics.value = null
  } finally {
    logisticsLoading.value = false
  }
}

// ── 申请退款 ──────────────────────────────
function handleRefund(order) {
  currentOrder.value = order
  refundForm.value = { reason: '', remark: '' }
  showRefundDialog.value = true
}

async function submitRefund() {
  await refundFormRef.value.validate()
  if (!currentOrder.value) return
  try {
    await orderApi.applyRefund({
      order_no: currentOrder.value.order_no,
      reason:   refundForm.value.reason,
      remark:   refundForm.value.remark || undefined,
    })
    ElMessage.success('退款申请已提交，请等待审核')
    showRefundDialog.value = false
    fetchOrders()
  } catch (e) {
    const status = e?.response?.status
    const msg    = e?.response?.data?.message || ''
    if (status === 400 && msg.includes('当前订单状态不支持退款')) {
      ElMessage.warning('此订单已申请退款，请勿重复提交')
    }
  }
}

// ── 咨询客服 ──────────────────────────────
function contactService(order) {
  chatStore.openChat()
  // 延迟等待对话窗口打开后预填消息提示
  setTimeout(() => {
    chatStore.addMessage({
      role: 'system',
      content: `用户正在咨询订单：${order.order_no}`,
    })
  }, 300)
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.orders-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--lx-bg-page);
}
.page-body {
  flex: 1;
  margin-top: var(--lx-header-height);
  padding: 24px 0 48px;
}
.orders-inner {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 0 var(--lx-content-padding);
}

/* 状态Tab */
.status-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #fff;
  padding: 6px;
  border-radius: var(--lx-radius-lg);
  border: 1px solid var(--lx-border);
  width: fit-content;
}
.status-tab {
  padding: 7px 18px;
  border-radius: var(--lx-radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--lx-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.status-tab:hover {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
}
.status-tab.active {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
  border: 1px solid var(--lx-primary-border);
}

/* 骨架屏 */
.order-skeleton {
  padding: 20px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: var(--lx-radius-xl);
  border: 1px solid var(--lx-border);
}

/* 订单卡片 */
.order-card {
  background: #fff;
  border: 1px solid var(--lx-border);
  border-radius: var(--lx-radius-xl);
  margin-bottom: 12px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}
.order-card:hover {
  box-shadow: var(--lx-shadow-md);
}

/* 卡片头部 */
.order-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--lx-bg-muted);
  border-bottom: 1px solid var(--lx-border-light);
}
.order-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}
.order-no {
  font-size: 13px;
  font-weight: 600;
  color: var(--lx-text-primary);
  font-family: monospace;
}
.order-time {
  font-size: 12px;
  color: var(--lx-text-placeholder);
}

/* 商品行 */
.order-product-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--lx-border-light);
}
.order-product-img {
  width: 72px;
  height: 72px;
  border-radius: var(--lx-radius-md);
  object-fit: cover;
  border: 1px solid var(--lx-border);
  flex-shrink: 0;
}
.order-product-info {
  flex: 1;
}
.order-product-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--lx-text-primary);
  margin-bottom: 4px;
}
.order-product-qty {
  font-size: 13px;
  color: var(--lx-text-secondary);
}
.order-product-price {
  font-size: 16px;
  font-weight: 700;
  color: var(--lx-danger);
  flex-shrink: 0;
}

/* 地址 */
.order-address {
  padding: 10px 20px;
  font-size: 12px;
  color: var(--lx-text-secondary);
  border-bottom: 1px solid var(--lx-border-light);
  background: var(--lx-bg-muted);
}

/* 卡片底部 */
.order-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
}
.order-total {
  font-size: 14px;
  color: var(--lx-text-secondary);
}
.order-total strong {
  color: var(--lx-danger);
  font-size: 18px;
  font-weight: 700;
}
.order-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

/* 物流弹窗 */
.logistics-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--lx-primary-soft);
  border-radius: var(--lx-radius-lg);
  margin-bottom: 20px;
}
.logistics-status-icon { font-size: 22px; }
.logistics-status-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--lx-primary);
}
.logistics-timeline { padding: 0 8px; }

/* 退款弹窗 */
.refund-body {}

/* 响应式 */
@media (max-width: 768px) {
  .orders-inner { padding: 0 12px; }
  .status-tabs  { overflow-x: auto; width: 100%; }
  .order-card-footer { flex-direction: column; gap: 12px; align-items: flex-end; }
}
</style>