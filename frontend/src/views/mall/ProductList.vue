<template>
  <div class="product-list-page">
    <Header />
    <div class="page-body">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-inner">
          <!-- 分类 -->
          <div class="filter-cats">
            <span
              class="cat-item"
              :class="{ active: !selectedCategory }"
              @click="selectedCategory = ''"
            >
              全部
            </span>
            <span
              v-for="cat in categories"
              :key="cat"
              class="cat-item"
              :class="{ active: selectedCategory === cat }"
              @click="selectedCategory = cat"
            >
              {{ cat }}
            </span>
          </div>

          <!-- 搜索 -->
          <el-input
            v-model="keyword"
            placeholder="搜索商品..."
            clearable
            style="width: 220px"
            :prefix-icon="Search"
            @keyup.enter="fetchProducts"
            @clear="fetchProducts"
          />
        </div>
      </div>

      <!-- 内容区 -->
      <div class="content-inner">
        <!-- 结果信息 -->
        <div class="result-info" v-if="!loading">
          共 <strong>{{ total }}</strong> 件商品
          <span v-if="selectedCategory">
            · 分类：{{ selectedCategory }}
          </span>
        </div>

        <!-- 骨架屏 -->
        <div v-if="loading" class="products-grid">
          <el-skeleton
            v-for="i in 8"
            :key="i"
            animated
            class="product-skeleton"
          >
            <template #template>
              <el-skeleton-item variant="image" style="width: 100%; aspect-ratio: 1/1; border-radius: 12px 12px 0 0;" />
              <div style="padding: 14px;">
                <el-skeleton-item variant="h3" style="width: 80%;" />
                <el-skeleton-item variant="text" style="width: 60%; margin-top: 8px;" />
                <el-skeleton-item variant="text" style="width: 40%; margin-top: 8px;" />
              </div>
            </template>
          </el-skeleton>
        </div>

        <!-- 商品网格 -->
        <div v-else-if="products.length" class="products-grid">
          <div
            v-for="product in products"
            :key="product.id"
            class="product-card lx-hover-card"
            @click="router.push(`/mall/products/${product.id}`)"
          >
            <div class="product-img-wrap">
              <img
                :src="product.images?.[0] || PLACEHOLDER_IMG(product.id)"
                :alt="product.name"
                class="product-img"
              />
              <div class="product-category-tag">{{ product.category }}</div>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-desc">{{ product.description }}</p>
              <div class="product-footer">
                <span class="product-price">{{ formatPrice(product.price) }}</span>
                <span class="product-stock">库存 {{ product.stock }}</span>
              </div>
              <el-button
                type="primary"
                class="lx-gradient-btn buy-btn"
                @click.stop="router.push(`/mall/products/${product.id}`)"
              >
                查看详情
              </el-button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="lx-empty">
          <el-empty description="暂无相关商品" />
        </div>

        <!-- 分页 -->
        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            background
            @current-change="fetchProducts"
          />
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { productApi } from '@/api/product'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMG } from '@/utils/constants'

const router = useRouter()

const loading          = ref(false)
const products         = ref([])
const categories       = ref([])
const total            = ref(0)
const page             = ref(1)
const pageSize         = ref(12)
const keyword          = ref('')
const selectedCategory = ref('')

// 分类切换重置页码并刷新
watch(selectedCategory, () => {
  page.value = 1
  fetchProducts()
})

async function fetchProducts() {
  loading.value = true
  try {
    const res = await productApi.getList({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      category: selectedCategory.value || undefined,
    })
    products.value = res.data || []
    total.value    = res.page_info?.total || 0
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const res = await productApi.getCategories()
    categories.value = res.data || []
  } catch {
    // 静默
  }
}

onMounted(() => {
  fetchCategories()
  fetchProducts()
})
</script>

<style scoped>
.product-list-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--lx-bg-page);
}
.page-body {
  flex: 1;
  margin-top: var(--lx-header-height);
}

/* 筛选栏 */
.filter-bar {
  background: #fff;
  border-bottom: 1px solid var(--lx-border);
  position: sticky;
  top: var(--lx-header-height);
  z-index: 100;
}
.filter-inner {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 0 var(--lx-content-padding);
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.filter-cats {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.cat-item {
  padding: 5px 14px;
  border-radius: var(--lx-radius-full);
  font-size: 13px;
  font-weight: 500;
  color: var(--lx-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.cat-item:hover {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
}
.cat-item.active {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
  border: 1px solid var(--lx-primary-border);
}

/* 内容区 */
.content-inner {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 24px var(--lx-content-padding);
}
.result-info {
  font-size: 13px;
  color: var(--lx-text-secondary);
  margin-bottom: 16px;
}
.result-info strong {
  color: var(--lx-text-primary);
  font-weight: 600;
}

/* 商品网格 */
.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.product-skeleton {
  border-radius: var(--lx-radius-xl);
  background: #fff;
  border: 1px solid var(--lx-border);
  overflow: hidden;
}
.product-card {
  border-radius: var(--lx-radius-xl);
  background: #fff;
  border: 1px solid var(--lx-border);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}
.product-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: var(--lx-bg-muted);
  overflow: hidden;
}
.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.product-card:hover .product-img {
  transform: scale(1.04);
}
.product-category-tag {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  border-radius: var(--lx-radius-full);
  background: rgba(255, 255, 255, 0.9);
  font-size: 11px;
  font-weight: 500;
  color: var(--lx-text-secondary);
  backdrop-filter: blur(4px);
}
.product-info {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}
.product-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--lx-text-primary);
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-desc {
  font-size: 12px;
  color: var(--lx-text-secondary);
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  flex: 1;
}
.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.product-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--lx-danger);
}
.product-stock {
  font-size: 12px;
  color: var(--lx-text-placeholder);
}
.buy-btn {
  width: 100%;
  margin-top: 4px;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .products-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .products-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .filter-inner  { flex-direction: column; height: auto; padding: 12px 16px; }
}
</style>