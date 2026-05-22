<template>
  <div class="order-card">
    <div class="order-card-header">
      <span class="order-card-icon">📦</span>
      <span class="order-card-title">订单信息</span>
      <el-tag :type="statusInfo.tag" size="small" round>
        {{ statusInfo.text }}
      </el-tag>
    </div>

    <div class="order-card-body">
      <div class="order-card-row">
        <span class="row-label">订单号</span>
        <span class="row-value order-no">{{ data.order_no }}</span>
      </div>
      <div class="order-card-row">
        <span class="row-label">商品</span>
        <span class="row-value">{{ data.product_name }}</span>
      </div>
      <div class="order-card-row">
        <span class="row-label">金额</span>
        <span class="row-value price">{{ formatPrice(data.total_amount) }}</span>
      </div>
      <div class="order-card-row">
        <span class="row-label">下单时间</span>
        <span class="row-value">{{ formatDate(data.created_at) }}</span>
      </div>
      <template v-if="data.logistics_no">
        <div class="order-card-divider" />
        <div class="order-card-row">
          <span class="row-label">快递单号</span>
          <span class="row-value">{{ data.logistics_no }}</span>
        </div>
        <div class="order-card-row">
          <span class="row-label">物流状态</span>
          <span class="row-value">{{ data.logistics_status }}</span>
        </div>
      </template>
    </div>

    <div v-if="!data.refund_eligible && data.refund_tip" class="refund-tip">
      <el-icon><WarningFilled /></el-icon>
      {{ data.refund_tip }}
    </div>

    <div class="order-card-footer">
      <el-button size="small" text type="primary" @click="goToOrder">
        📦 查看详情 →
      </el-button>
      <el-button
        v-if="data.refund_eligible"
        size="small"
        text
        type="danger"
        @click="applyRefund"
      >
        申请退款
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { WarningFilled } from '@element-plus/icons-vue'
import { formatPrice, formatDate, getOrderStatus } from '@/utils/format'

const props = defineProps({
  data: { type: Object, required: true },
})

const emit = defineEmits(['refund'])
const router = useRouter()

const statusInfo = computed(() => getOrderStatus(props.data.status))

async function goToOrder() {
  const target = `/mall/orders?no=${props.data.order_no}`
  try {
    await router.push(target)
  } catch {
    window.open(target, '_blank')
  }
}

function applyRefund() {
  emit('refund', props.data.order_no)
}
</script>

<style scoped>
.order-card {
  width: 280px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid var(--lx-border);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
  overflow: hidden;
  margin: 4px 0;
}

.order-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: var(--lx-bg-muted);
  border-bottom: 1px solid var(--lx-border);
}
.order-card-icon { font-size: 16px; }
.order-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--lx-text-primary);
  flex: 1;
}

.order-card-body {
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.order-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}
.row-label {
  color: var(--lx-text-secondary);
  flex-shrink: 0;
  width: 60px;
}
.row-value {
  color: var(--lx-text-regular);
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}
.row-value.order-no {
  font-family: monospace;
  font-size: 11px;
  color: var(--lx-text-secondary);
}
.row-value.price {
  color: var(--lx-danger);
  font-weight: 700;
  font-size: 14px;
}

.order-card-divider {
  height: 1px;
  background: var(--lx-border-light);
  margin: 4px 0;
}

.order-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 8px 10px;
  border-top: 1px solid var(--lx-border-light);
  background: var(--lx-bg-muted);
}

.refund-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: #fef0f0;
  color: #f56c6c;
  font-size: 12px;
}
</style>
