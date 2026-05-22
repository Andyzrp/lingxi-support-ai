<template>
  <div class="product-detail-page">
    <Header />

    <div class="page-body">
      <!-- 加载中 -->
      <div v-if="loading" class="detail-inner">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 商品详情 -->
      <div v-else-if="product" class="detail-inner">
        <!-- 面包屑 -->
        <el-breadcrumb class="breadcrumb" separator="/">
          <el-breadcrumb-item :to="{ path: '/mall' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/mall/products' }">全部商品</el-breadcrumb-item>
          <el-breadcrumb-item>{{ product.name }}</el-breadcrumb-item>
        </el-breadcrumb>

        <!-- 主体区域 -->
        <div class="detail-main">
          <!-- 左侧图片 -->
          <div class="detail-gallery">
            <div class="main-img-wrap">
              <img
                :src="currentImg || PLACEHOLDER_IMG(product.id)"
                :alt="product.name"
                class="main-img"
              />
              <!-- 库存不足蒙层 -->
              <div v-if="product.stock === 0" class="out-of-stock-mask">
                <span>已售罄</span>
              </div>
            </div>
            <!-- 缩略图列表 -->
            <div class="thumb-list" v-if="product.images?.length > 1">
              <div
                v-for="(img, idx) in product.images"
                :key="idx"
                class="thumb-item"
                :class="{ active: currentImg === img }"
                @click="currentImg = img"
              >
                <img :src="img" :alt="`图片${idx + 1}`" />
              </div>
            </div>
          </div>

          <!-- 右侧信息 -->
          <div class="detail-info">
            <!-- 分类标签 -->
            <div class="detail-category">{{ product.category }}</div>

            <!-- 商品名称 -->
            <h1 class="detail-name">{{ product.name }}</h1>

            <!-- 价格区 -->
            <div class="detail-price-box">
              <span class="detail-price">{{ formatPrice(product.price) }}</span>
              <span class="detail-stock-tag" :class="stockClass">
                {{ stockText }}
              </span>
            </div>

            <!-- 商品描述 -->
            <div class="detail-desc">
              <p>{{ product.description }}</p>
            </div>

            <!-- 数量选择 -->
            <div class="detail-quantity">
              <span class="quantity-label">购买数量</span>
              <el-input-number
                v-model="quantity"
                :min="1"
                :max="product.stock"
                :disabled="product.stock === 0"
                size="large"
              />
              <span class="stock-hint">库存 {{ product.stock }} 件</span>
            </div>

            <!-- 操作按钮 -->
            <div class="detail-actions">
              <el-button
                type="primary"
                size="large"
                class="lx-gradient-btn buy-now-btn"
                :disabled="product.stock === 0"
                :loading="ordering"
                @click="handleOrder"
              >
                {{ product.stock === 0 ? '已售罄' : '立即下单' }}
              </el-button>
              <el-button
                size="large"
                plain
                @click="openChat"
              >
                💬 咨询客服
              </el-button>
            </div>

            <!-- 服务保障 -->
            <div class="detail-guarantee">
              <div
                v-for="item in guarantees"
                :key="item.text"
                class="guarantee-item"
              >
                <span class="guarantee-icon">{{ item.icon }}</span>
                <span>{{ item.text }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 商品详情描述 -->
        <div class="detail-content-section">
          <div class="section-tab">商品详情</div>
          <div class="detail-content">
            <p>{{ product.description }}</p>
            <div class="detail-attrs">
              <div class="attr-row">
                <span class="attr-label">商品分类</span>
                <span class="attr-value">{{ product.category }}</span>
              </div>
              <div class="attr-row">
                <span class="attr-label">库存数量</span>
                <span class="attr-value">{{ product.stock }} 件</span>
              </div>
              <div class="attr-row">
                <span class="attr-label">上架时间</span>
                <span class="attr-value">{{ formatDate(product.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 商品不存在 -->
      <div v-else class="detail-inner">
        <el-empty description="商品不存在或已下架">
          <el-button type="primary" @click="router.push('/mall/products')">
            返回商品列表
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 下单弹窗 -->
    <el-dialog
      v-model="showOrderDialog"
      title="确认订单"
      width="480px"
      border-radius="16px"
      :close-on-click-modal="false"
    >
      <div class="order-dialog-body">
        <!-- 商品信息 -->
        <div class="order-product-info">
          <img
            :src="currentImg || PLACEHOLDER_IMG(product?.id)"
            class="order-product-img"
          />
          <div class="order-product-detail">
            <div class="order-product-name">{{ product?.name }}</div>
            <div class="order-product-price">
              {{ formatPrice(product?.price) }} × {{ quantity }}
            </div>
            <div class="order-product-total">
              合计：<strong>{{ formatPrice((product?.price || 0) * quantity) }}</strong>
            </div>
          </div>
        </div>

        <!-- 收货地址表单 -->
        <el-form
          ref="orderFormRef"
          :model="orderForm"
          :rules="orderRules"
          label-width="80px"
          style="margin-top: 20px;"
        >
          <el-form-item label="收货人" prop="name">
            <el-input v-model="orderForm.name" placeholder="请输入收货人姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="orderForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="省市区" prop="city">
            <el-input v-model="orderForm.city" placeholder="如：广东省深圳市南山区" />
          </el-form-item>
          <el-form-item label="详细地址" prop="detail">
            <el-input
              v-model="orderForm.detail"
              type="textarea"
              :rows="2"
              placeholder="请输入详细地址"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="showOrderDialog = false">取消</el-button>
        <el-button
          type="primary"
          class="lx-gradient-btn"
          :loading="ordering"
          @click="submitOrder"
        >
          确认下单
        </el-button>
      </template>
    </el-dialog>

    <Footer />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { productApi } from '@/api/product'
import { orderApi } from '@/api/order'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { formatPrice, formatDate } from '@/utils/format'
import { PLACEHOLDER_IMG } from '@/utils/constants'

const router    = useRouter()
const route     = useRoute()
const chatStore = useChatStore()
const userStore = useUserStore()

const loading        = ref(false)
const ordering       = ref(false)
const product        = ref(null)
const currentImg     = ref('')
const quantity       = ref(1)
const showOrderDialog = ref(false)
const orderFormRef   = ref(null)

const orderForm = ref({
  name:   '',
  phone:  '',
  city:   '',
  detail: '',
})

const orderRules = {
  name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  city: [
    { required: true, message: '请输入省市区', trigger: 'blur' }
  ],
  detail: [
    { required: true, message: '请输入详细地址', trigger: 'blur' }
  ],
}

const guarantees = [
  { icon: '🔒', text: '正品保障' },
  { icon: '🚚', text: '极速发货' },
  { icon: '↩️', text: '7天退换' },
  { icon: '💬', text: '24h客服' },
]

const stockClass = computed(() => {
  if (!product.value) return ''
  if (product.value.stock === 0) return 'stock-empty'
  if (product.value.stock <= 10) return 'stock-low'
  return 'stock-normal'
})

const stockText = computed(() => {
  if (!product.value) return ''
  if (product.value.stock === 0) return '已售罄'
  if (product.value.stock <= 10) return `仅剩 ${product.value.stock} 件`
  return '库存充足'
})

function openChat() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后使用客服功能')
    router.push('/login')
    return
  }
  chatStore.openChat()
}

function handleOrder() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后下单')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  showOrderDialog.value = true
}

async function submitOrder() {
  await orderFormRef.value.validate()
  ordering.value = true
  try {
    // 拆分城市字段 [1]
    const cityParts = orderForm.value.city.split(/省|市|区/).filter(Boolean)
    await orderApi.create({
      product_id: product.value.id,
      quantity: quantity.value,
      address: {
        name:     orderForm.value.name,
        phone:    orderForm.value.phone,
        province: cityParts[0] ? cityParts[0] + '省' : orderForm.value.city,
        city:     cityParts[1] ? cityParts[1] + '市' : '',
        district: cityParts[2] ? cityParts[2] + '区' : '',
        detail:   orderForm.value.detail,
      },
    })
    ElMessage.success('下单成功！')
    showOrderDialog.value = false
    router.push('/mall/orders')
  } finally {
    ordering.value = false
  }
}

async function fetchProduct() {
  loading.value = true
  try {
    const res = await productApi.getDetail(route.params.id)
    product.value = res.data
    currentImg.value = res.data.images?.[0] || ''
  } catch {
    product.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProduct()
})
</script>

<style scoped>
.product-detail-page {
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
.detail-inner {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 0 var(--lx-content-padding);
}

/* 面包屑 */
.breadcrumb { margin-bottom: 20px; }

/* 主体区域 */
.detail-main {
  display: grid;
  grid-template-columns: 480px 1fr;
  gap: 40px;
  margin-bottom: 32px;
}

/* 图片区 */
.detail-gallery {}
.main-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: var(--lx-radius-xl);
  overflow: hidden;
  background: var(--lx-bg-muted);
  border: 1px solid var(--lx-border);
  margin-bottom: 12px;
}
.main-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.main-img-wrap:hover .main-img { transform: scale(1.03); }
.out-of-stock-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.out-of-stock-mask span {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
}
.thumb-list {
  display: flex;
  gap: 8px;
}
.thumb-item {
  width: 64px;
  height: 64px;
  border-radius: var(--lx-radius-md);
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color 0.2s ease;
}
.thumb-item.active {
  border-color: var(--lx-primary);
}
.thumb-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 信息区 */
.detail-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.detail-category {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: var(--lx-radius-full);
  background: var(--lx-primary-soft);
  color: var(--lx-primary);
  font-size: 12px;
  font-weight: 500;
  width: fit-content;
}
.detail-name {
  font-size: 26px;
  font-weight: 700;
  color: var(--lx-text-primary);
  margin: 0;
  line-height: 1.3;
}
.detail-price-box {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--lx-bg-muted);
  border-radius: var(--lx-radius-lg);
}
.detail-price {
  font-size: 32px;
  font-weight: 800;
  color: var(--lx-danger);
}
.detail-stock-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: var(--lx-radius-full);
}
.stock-normal {
  color: var(--lx-success);
  background: var(--lx-success-soft);
}
.stock-low {
  color: var(--lx-warning);
  background: var(--lx-warning-soft);
}
.stock-empty {
  color: var(--lx-text-secondary);
  background: var(--lx-bg-muted);
}
.detail-desc {
  font-size: 14px;
  color: var(--lx-text-secondary);
  line-height: 1.8;
}
.detail-desc p { margin: 0; }

/* 数量 */
.detail-quantity {
  display: flex;
  align-items: center;
  gap: 16px;
}
.quantity-label {
  font-size: 14px;
  color: var(--lx-text-regular);
  font-weight: 500;
  flex-shrink: 0;
}
.stock-hint {
  font-size: 13px;
  color: var(--lx-text-placeholder);
}

/* 按钮 */
.detail-actions {
  display: flex;
  gap: 12px;
}
.buy-now-btn {
  flex: 1;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

/* 保障 */
.detail-guarantee {
  display: flex;
  gap: 20px;
  padding: 16px;
  background: var(--lx-bg-muted);
  border-radius: var(--lx-radius-lg);
}
.guarantee-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--lx-text-secondary);
}
.guarantee-icon { font-size: 16px; }

/* 详情内容 */
.detail-content-section {
  background: #fff;
  border: 1px solid var(--lx-border);
  border-radius: var(--lx-radius-xl);
  overflow: hidden;
}
.section-tab {
  padding: 16px 24px;
  font-size: 15px;
  font-weight: 600;
  color: var(--lx-primary);
  border-bottom: 2px solid var(--lx-primary);
  display: inline-block;
  background: var(--lx-bg-muted);
  width: 100%;
  box-sizing: border-box;
}
.detail-content { padding: 24px; }
.detail-attrs { margin-top: 20px; }
.attr-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid var(--lx-border-light);
  font-size: 14px;
}
.attr-row:last-child { border-bottom: none; }
.attr-label {
  width: 100px;
  color: var(--lx-text-secondary);
  flex-shrink: 0;
}
.attr-value { color: var(--lx-text-regular); }

/* 下单弹窗 */
.order-dialog-body {}
.order-product-info {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--lx-bg-muted);
  border-radius: var(--lx-radius-lg);
  margin-bottom: 4px;
}
.order-product-img {
  width: 80px;
  height: 80px;
  border-radius: var(--lx-radius-md);
  object-fit: cover;
  flex-shrink: 0;
}
.order-product-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}
.order-product-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--lx-text-primary);
}
.order-product-price {
  font-size: 13px;
  color: var(--lx-text-secondary);
}
.order-product-total {
  font-size: 14px;
  color: var(--lx-text-regular);
}
.order-product-total strong {
  color: var(--lx-danger);
  font-size: 16px;
}

/* 响应式 */
@media (max-width: 900px) {
  .detail-main { grid-template-columns: 1fr; }
}
</style>