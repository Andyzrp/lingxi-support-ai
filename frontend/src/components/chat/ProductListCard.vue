<template>
  <div class="product-list-card">
    <div class="product-list-header">
      <span>🛍️ 热销商品</span>
      <span class="product-count">共 {{ products.length }} 款</span>
    </div>
    <div class="product-list-items">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-item"
        @click="goProduct(product)"
      >
        <div class="product-item-img">
          <el-image
            v-if="product.image"
            :src="product.image"
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
        <div class="product-item-info">
          <div class="product-item-name">{{ product.name }}</div>
          <div class="product-item-meta">
            <span class="product-item-price">¥{{ product.price }}</span>
            <el-tag :type="getStockType(product.stock)" size="small" round>
              {{ getStockLabel(product.stock) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Picture } from '@element-plus/icons-vue'

defineProps({
  products: {
    type: Array,
    default: () => []
  }
})

function getStockType(stock) {
  if (stock == null) return 'info'
  if (stock <= 0) return 'danger'
  if (stock < 10) return 'warning'
  return 'success'
}

function getStockLabel(stock) {
  if (stock == null) return '未知'
  if (stock <= 0) return '已售罄'
  if (stock < 10) return '库存紧张'
  return '有货'
}

function goProduct(product) {
  if (!product.id || product.stock <= 0) return
  window.open(`/mall/products/${product.id}`, '_blank')
}
</script>

<style scoped lang="scss">
.product-list-card {
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

.product-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}

.product-count {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}

.product-list-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.product-item {
  display: flex;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border: 1px solid #f5f7fa;

  &:hover {
    background: #fafafa;
    border-color: #e4e7ed;
  }
}

.product-item-img {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 6px;
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

.product-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.product-item-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.product-item-price {
  font-size: 15px;
  font-weight: 700;
  color: #f56c6c;
}
</style>
