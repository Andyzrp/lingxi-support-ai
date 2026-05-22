<template>
  <div class="product-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="card-header-left">
        <el-icon class="header-icon"><ShoppingCart /></el-icon>
        <span class="header-title">商品信息</span>
      </div>
      <el-tag
        :type="getStockType(cardData.stock)"
        size="small"
        round
      >
        {{ getStockLabel(cardData.stock) }}
      </el-tag>
    </div>

    <!-- 商品主体 -->
    <div class="product-body" @click="goProduct">
      <!-- 商品图片 -->
      <div class="product-img-wrap">
        <el-image
          v-if="cardData.image"
          :src="cardData.image"
          fit="cover"
          class="product-img"
          :preview-src-list="[cardData.image]"
          @click.stop
        >
          <template #error>
            <div class="product-img-error">
              <el-icon><Picture /></el-icon>
            </div>
          </template>
        </el-image>
        <div v-else class="product-img-placeholder">
          <el-icon :size="32"><Picture /></el-icon>
        </div>
      </div>

      <!-- 商品信息 -->
      <div class="product-info">
        <div class="product-name">{{ cardData.name || '暂无商品名称' }}</div>

        <div class="product-category" v-if="cardData.category">
          <el-tag type="info" size="small" effect="plain">
            {{ cardData.category }}
          </el-tag>
        </div>

        <div class="product-desc" v-if="cardData.description">
          {{ cardData.description }}
        </div>

        <div class="product-meta">
          <div class="product-price">
            <span class="price-symbol">¥</span>
            <span class="price-num">{{ cardData.price }}</span>
          </div>
          <div class="product-stock" v-if="cardData.stock != null">
            <span class="stock-label">库存</span>
            <span
              class="stock-num"
              :class="{ 'stock-low': cardData.stock < 10 }"
            >
              {{ cardData.stock > 0 ? cardData.stock : '无货' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片底部操作 -->
    <div class="card-footer">
      <el-button
        type="primary"
        size="small"
        :icon="ShoppingCart"
        :disabled="cardData.stock <= 0"
        @click="goProduct"
      >
        {{ cardData.stock > 0 ? '立即购买' : '已售罄' }}
      </el-button>
      <el-button
        plain
        size="small"
        :icon="View"
        @click="goProduct"
      >
        查看详情
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ShoppingCart, View, Picture } from '@element-plus/icons-vue'

const props = defineProps({
  cardData: {
    type:     Object,
    required: true,
    default:  () => ({}),
  },
})

const router = useRouter()

function getStockType(stock) {
  if (stock == null)  return 'info'
  if (stock <= 0)     return 'danger'
  if (stock < 10)     return 'warning'
  return 'success'
}

function getStockLabel(stock) {
  if (stock == null)  return '未知库存'
  if (stock <= 0)     return '已售罄'
  if (stock < 10)     return '库存紧张'
  return '有货'
}

function goProduct() {
  if (!props.cardData.id || props.cardData.stock <= 0) return
  window.open(`/mall/products/${props.cardData.id}`, '_blank')
}
</script>

<style scoped lang="scss">
.product-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  min-width: 280px;
  max-width: 360px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 10px;
  background: linear-gradient(
    135deg,
    rgba(103, 194, 58, 0.08),
    rgba(103, 194, 58, 0.03)
  );
  border-bottom: 1px solid #f0f2f5;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 7px;
}

.header-icon {
  color: #67c23a;
  font-size: 18px;
}

.header-title {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
}

.product-body {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #fafafa;
  }
}

.product-img-wrap {
  width: 90px;
  height: 90px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.product-img {
  width: 100%;
  height: 100%;
}

.product-img-error,
.product-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
}

.product-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.product-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-category {
  display: flex;
}

.product-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.price-symbol {
  font-size: 13px;
  color: #f56c6c;
  font-weight: 600;
}

.price-num {
  font-size: 20px;
  font-weight: 800;
  color: #f56c6c;
  line-height: 1;
}

.product-stock {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.stock-label {
  color: #c0c4cc;
}

.stock-num {
  color: #67c23a;
  font-weight: 500;

  &.stock-low {
    color: #e6a23c;
  }
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 12px;
  border-top: 1px solid #f5f7fa;
}
</style>
