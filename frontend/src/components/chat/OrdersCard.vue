<template>
  <div class="orders-card">
    <div class="orders-card-header">
      <span>我的订单</span>
      <span class="orders-count">共 {{ orders.length }} 笔</span>
    </div>
    <div class="orders-list">
      <div
        v-for="order in orders"
        :key="order.order_no"
        class="order-item"
        @click="goOrder(order)"
      >
        <div class="order-item-img">
          <el-image
            v-if="order.image"
            :src="order.image"
            fit="cover"
            class="product-img"
          >
            <template #error>
              <div class="img-placeholder">
                <el-icon :size="20"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div v-else class="img-placeholder">
            <el-icon :size="20"><Picture /></el-icon>
          </div>
        </div>
        <div class="order-item-info">
          <div class="order-product-name">{{ order.product_name }}</div>
          <div class="order-item-no">{{ order.order_no }}</div>
          <div class="order-item-date">{{ order.created_at }}</div>
        </div>
        <div class="order-item-right">
          <div class="order-item-price">¥{{ order.total_amount.toFixed(2) }}</div>
          <el-tag :type="getStatusType(order.status)" size="small" round>
            {{ order.status_text }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Picture } from '@element-plus/icons-vue'

defineProps({
  orders: {
    type: Array,
    default: () => []
  }
})

function getStatusType(status) {
  const map = {
    0: 'info',
    1: 'success',
    2: 'warning',
    3: '',
    4: 'info',
    5: 'danger',
    6: 'info',
  }
  return map[status] || 'info'
}

function goOrder(order) {
  window.open(`/mall/orders?no=${order.order_no}`, '_blank')
}
</script>

<style scoped lang="scss">
.orders-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 320px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.orders-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}

.orders-count {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border: 1px solid #f5f7fa;

  &:hover {
    background: #fafafa;
    border-color: #e4e7ed;
  }
}

.order-item-img {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.product-img {
  width: 100%;
  height: 100%;
}

.img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
}

.order-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.order-product-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.order-item-no {
  font-size: 11px;
  font-family: monospace;
  color: #909399;
}

.order-item-date {
  font-size: 11px;
  color: #c0c4cc;
}

.order-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.order-item-price {
  font-size: 14px;
  font-weight: 700;
  color: #f56c6c;
}
</style>
