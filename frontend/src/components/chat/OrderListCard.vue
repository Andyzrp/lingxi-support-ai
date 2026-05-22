<template>
  <div class="order-list-card">
    <div class="order-list-header">
      <span>📦 最近订单</span>
      <span class="order-count">共 {{ orders.length }} 笔</span>
    </div>
    <OrderCard
      v-for="order in orders"
      :key="order.order_no"
      :data="order"
      class="order-list-item"
      @refund="$emit('refund', $event)"
    />
  </div>
</template>

<script setup>
import OrderCard from './OrderCard.vue'

defineProps({
  orders: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.order-list-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 280px;
}
.order-list-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--lx-text-primary);
  padding: 0 2px;
}
.order-count {
  font-size: 12px;
  color: var(--lx-text-secondary);
  font-weight: 400;
}
.order-list-item {
  margin: 0;
}
</style>
