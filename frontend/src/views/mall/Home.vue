<template>
  <div class="mall-home">
    <Header />

    <!-- 商城 Hero -->
    <section class="hero-banner">
      <div class="hero-inner">
        <div class="hero-content">
          <div class="hero-kicker">LINGXI MALL</div>

          <h1 class="hero-title">
            探索灵犀精选商城
            <span>品质好物，为日常而来</span>
          </h1>

          <p class="hero-desc">
            精选数码、智能生活与高品质好物，带来更可靠、更轻松的购物体验。
          </p>

          <div class="hero-actions">
            <el-button
              size="large"
              class="lx-gradient-btn"
              @click="router.push('/mall/products')"
            >
              立即选购
            </el-button>

            <el-button
              size="large"
              class="hero-secondary-btn"
              plain
              @click="router.push('/mall/products')"
            >
              浏览全部商品
            </el-button>
          </div>
        </div>

        <div class="hero-visual">
          <div class="showcase-card main-showcase">
            <div class="showcase-label">NEW ARRIVAL</div>
            <div class="showcase-title">智能生活精选</div>
            <div class="showcase-desc">Discover more possibilities</div>
          </div>

          <div class="showcase-card small-showcase top">
            <span>品质精选</span>
          </div>

          <div class="showcase-card small-showcase bottom">
            <span>快速发货</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 商城服务优势 -->
    <section class="features-section">
      <div class="section-inner">
        <div class="section-header">
          <h2>安心购物体验</h2>
          <p>从选购到售后，为你提供稳定可靠的商城服务</p>
        </div>

        <div class="features-grid">
          <div
            v-for="item in features"
            :key="item.title"
            class="feature-card lx-hover-card"
          >
            <div class="feature-icon">{{ item.icon }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 热销商品 -->
    <section class="products-section">
      <div class="section-inner">
        <div class="section-header products-header">
          <div>
            <h2>热销商品</h2>
            <p>甄选近期人气好物</p>
          </div>

          <el-button text type="primary" @click="router.push('/mall/products')">
            查看全部 →
          </el-button>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="products-grid">
          <el-skeleton
            v-for="i in 4"
            :key="i"
            :rows="4"
            animated
            class="product-skeleton"
          />
        </div>

        <!-- 商品列表 -->
        <div v-else class="products-grid">
          <div
            v-for="product in hotProducts"
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
            </div>

            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-desc">{{ product.description }}</p>

              <div class="product-footer">
                <span class="product-price">
                  {{ formatPrice(product.price) }}
                </span>

                <el-button
                  type="primary"
                  size="small"
                  class="lx-gradient-btn"
                  @click.stop="router.push(`/mall/products/${product.id}`)"
                >
                  查看详情
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 售后服务入口 -->
    <section class="service-section">
      <div class="section-inner">
        <div class="service-card">
          <div class="service-left">
            <div class="service-kicker">SERVICE SUPPORT</div>

            <h2>需要帮助？我们随时在线</h2>

            <p>
              支持订单查询、物流跟踪、退款退货申请等常见售后服务。
            </p>

            <div class="service-actions">
              <el-button size="large" class="dark-btn" @click="openChat">
                联系客服
              </el-button>

              <el-button
                size="large"
                plain
                class="light-outline-btn"
                @click="router.push('/mall/products')"
              >
                继续购物
              </el-button>
            </div>
          </div>

          <div class="service-right">
            <div
              v-for="tag in aiTags"
              :key="tag"
              class="service-tag"
              @click="openChat"
            >
              {{ tag }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { productApi } from '@/api/product'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { formatPrice, PLACEHOLDER_IMG } from '@/utils/format'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const loading = ref(false)
const hotProducts = ref([])

const features = [
  {
    icon: '🚚',
    title: '快速配送',
    desc: '多仓协同发货，订单状态实时同步。',
  },
  {
    icon: '✅',
    title: '正品保障',
    desc: '精选优质商品，严格把控商品品质。',
  },
  {
    icon: '↩️',
    title: '无忧售后',
    desc: '支持退款、退货、订单查询等售后服务。',
  },
  {
    icon: '💬',
    title: '在线服务',
    desc: '购物疑问随时咨询，获得更及时的帮助。',
  },
]

const aiTags = [
  '📦 查询订单状态',
  '🚚 物流跟踪',
  '↩️ 申请退款',
  '🔄 申请退货',
  '💬 商品咨询',
  '⭐ 售后评价',
  '👤 转接人工',
]

/* -------- 方法 -------- */
const openChat = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再咨询客服')
    router.push('/login')
    return
  }

  chatStore.openChat()
}

async function fetchHotProducts() {
  loading.value = true

  try {
    const res = await productApi.getList({ page: 1, page_size: 4 })

    // 适配后端返回格式
    hotProducts.value = Array.isArray(res) ? res : res.data || []
  } catch {
    // 静默失败，首页不显示错误提示
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHotProducts()
})
</script>

<style scoped>
/* ===== 页面基础 ===== */
.mall-home {
  min-height: 100vh;
  background: #f5f5f7;
  color: #1d1d1f;
}

.hero-inner,
.section-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}

/* ===== Hero Banner：商城风格 ===== */
.hero-banner {
  position: relative;
  overflow: hidden;
  min-height: 620px;
  padding: 96px 0 88px;
  background:
    radial-gradient(
      circle at 72% 35%,
      rgba(255, 255, 255, 0.9) 0,
      rgba(255, 255, 255, 0.2) 24%,
      transparent 42%
    ),
    linear-gradient(135deg, #eef1f6 0%, #f8f9fb 46%, #e9edf5 100%);
}

.hero-banner::before {
  content: '';
  position: absolute;
  inset: auto -120px -260px auto;
  width: 720px;
  height: 720px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.18),
    rgba(118, 75, 162, 0.08)
  );
  filter: blur(4px);
}

.hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 80px;
}

.hero-content {
  flex: 1;
  max-width: 560px;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 14px;
  margin-bottom: 24px;
  border-radius: 999px;
  background: rgba(29, 29, 31, 0.06);
  color: #5f6673;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.hero-title {
  margin: 0 0 20px;
  color: #111;
  font-size: 56px;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -0.04em;
}

.hero-title span {
  display: block;
  margin-top: 10px;
  color: #515761;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.hero-desc {
  max-width: 480px;
  margin: 0 0 36px;
  color: #6e6e73;
  font-size: 17px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-secondary-btn {
  border-color: rgba(29, 29, 31, 0.16) !important;
  color: #1d1d1f !important;
  background: rgba(255, 255, 255, 0.65) !important;
  backdrop-filter: blur(12px);
}

.hero-secondary-btn:hover {
  border-color: #1d1d1f !important;
  background: #fff !important;
}

/* ===== Hero 右侧视觉 ===== */
.hero-visual {
  position: relative;
  flex: 1;
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.showcase-card {
  position: absolute;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow:
    0 28px 80px rgba(15, 23, 42, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(18px);
}

.main-showcase {
  position: relative;
  width: 420px;
  height: 420px;
  padding: 36px;
  overflow: hidden;
  background:
    radial-gradient(
      circle at 58% 54%,
      rgba(102, 126, 234, 0.24),
      transparent 32%
    ),
    linear-gradient(
      145deg,
      rgba(255, 255, 255, 0.92),
      rgba(238, 241, 248, 0.84)
    );
}

.main-showcase::before {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 62px;
  width: 240px;
  height: 150px;
  border-radius: 48px;
  background: linear-gradient(145deg, #1f2937, #64748b);
  transform: translateX(-50%) rotate(-8deg);
  box-shadow: 0 28px 60px rgba(31, 41, 55, 0.28);
}

.main-showcase::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 102px;
  width: 160px;
  height: 92px;
  border-radius: 28px;
  background: linear-gradient(145deg, #f8fafc, #cbd5e1);
  transform: translateX(-50%) rotate(-8deg);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.showcase-label {
  color: #667eea;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.showcase-title {
  margin-top: 10px;
  color: #111827;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.showcase-desc {
  margin-top: 8px;
  color: #6b7280;
  font-size: 14px;
}

.small-showcase {
  width: 148px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1f2937;
  font-size: 15px;
  font-weight: 700;
}

.small-showcase.top {
  top: 34px;
  right: 28px;
}

.small-showcase.bottom {
  left: 20px;
  bottom: 44px;
}

/* ===== 通用 Section ===== */
.features-section,
.products-section,
.service-section {
  padding: 88px 0;
}

.features-section {
  background: #fff;
}

.products-section {
  background: #f5f5f7;
}

.section-header {
  margin-bottom: 44px;
  text-align: center;
}

.section-header h2 {
  margin: 0 0 10px;
  color: #1d1d1f;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.section-header p {
  margin: 0;
  color: #6e6e73;
  font-size: 16px;
}

.products-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  text-align: left;
}

/* ===== 服务优势卡片 ===== */
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.feature-card {
  min-height: 210px;
  padding: 34px 26px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-radius: 28px;
  background: #f7f8fa;
  text-align: left;
  box-shadow: none;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    background 0.25s ease;
}

.feature-card:hover {
  transform: translateY(-6px);
  background: #fff;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.feature-icon {
  width: 52px;
  height: 52px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: #fff;
  font-size: 26px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.feature-card h3 {
  margin: 0 0 10px;
  color: #1d1d1f;
  font-size: 19px;
  font-weight: 800;
}

.feature-card p {
  margin: 0;
  color: #6e6e73;
  font-size: 14px;
  line-height: 1.7;
}

/* ===== 商品区 ===== */
.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

.product-card {
  overflow: hidden;
  border-radius: 28px;
  background: #fff;
  box-shadow: none;
  cursor: pointer;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 22px 50px rgba(15, 23, 42, 0.12);
}

.product-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 0.88;
  overflow: hidden;
  background:
    radial-gradient(circle at center, #fff 0%, #eef1f6 58%, #e5e7eb 100%);
}

.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.45s ease;
}

.product-card:hover .product-img {
  transform: scale(1.06);
}

.product-info {
  padding: 22px 22px 24px;
}

.product-name {
  margin: 0 0 8px;
  color: #1d1d1f;
  font-size: 17px;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-desc {
  height: 42px;
  margin: 0 0 18px;
  color: #7a7a80;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.product-price {
  color: #111827;
  font-size: 21px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.product-skeleton {
  padding: 18px;
  overflow: hidden;
  border-radius: 28px;
  background: #fff;
}

/* ===== 售后服务入口 ===== */
.service-section {
  background: #fff;
}

.service-card {
  overflow: hidden;
  min-height: 360px;
  padding: 56px;
  border-radius: 36px;
  display: flex;
  align-items: center;
  gap: 64px;
  background:
    radial-gradient(
      circle at 82% 24%,
      rgba(255, 255, 255, 0.22),
      transparent 28%
    ),
    linear-gradient(135deg, #111827 0%, #1f2937 48%, #374151 100%);
  color: #fff;
}

.service-left {
  flex: 1;
}

.service-kicker {
  margin-bottom: 18px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.service-left h2 {
  margin: 0 0 14px;
  font-size: 34px;
  font-weight: 850;
  letter-spacing: -0.03em;
}

.service-left p {
  max-width: 460px;
  margin: 0 0 32px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 16px;
  line-height: 1.8;
}

.service-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.service-right {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

.service-tag {
  padding: 11px 18px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.88);
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(12px);
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

.service-tag:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.16);
}

/* ===== 按钮 ===== */
.lx-gradient-btn {
  border: none !important;
  border-radius: 999px !important;
  background: #111827 !important;
  color: #fff !important;
  font-weight: 700 !important;
  box-shadow: 0 12px 26px rgba(17, 24, 39, 0.18);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    opacity 0.2s ease;
}

.lx-gradient-btn:hover {
  opacity: 0.92;
  transform: translateY(-2px);
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.24);
}

.dark-btn {
  border: none !important;
  border-radius: 999px !important;
  background: #fff !important;
  color: #111827 !important;
  font-weight: 800 !important;
}

.dark-btn:hover {
  opacity: 0.92;
}

.light-outline-btn {
  border-radius: 999px !important;
  border-color: rgba(255, 255, 255, 0.32) !important;
  background: transparent !important;
  color: #fff !important;
}

.light-outline-btn:hover {
  background: rgba(255, 255, 255, 0.12) !important;
}

/* ===== 响应式 ===== */
@media (max-width: 1100px) {
  .hero-inner {
    gap: 48px;
  }

  .hero-title {
    font-size: 46px;
  }

  .main-showcase {
    width: 360px;
    height: 360px;
  }

  .features-grid,
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .service-card {
    gap: 40px;
  }
}

@media (max-width: 768px) {
  .hero-inner,
  .section-inner {
    padding: 0 20px;
  }

  .hero-banner {
    min-height: auto;
    padding: 72px 0 64px;
  }

  .hero-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-content {
    max-width: none;
  }

  .hero-title {
    font-size: 36px;
  }

  .hero-title span {
    font-size: 23px;
  }

  .hero-desc {
    font-size: 15px;
  }

  .hero-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .hero-visual {
    width: 100%;
    min-height: 300px;
  }

  .main-showcase {
    width: 100%;
    height: 300px;
    border-radius: 28px;
  }

  .small-showcase {
    display: none;
  }

  .features-section,
  .products-section,
  .service-section {
    padding: 64px 0;
  }

  .section-header,
  .products-header {
    margin-bottom: 30px;
  }

  .products-header {
    align-items: flex-start;
  }

  .section-header h2 {
    font-size: 28px;
  }

  .features-grid,
  .products-grid {
    grid-template-columns: 1fr;
  }

  .feature-card {
    min-height: auto;
  }

  .service-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 36px 24px;
    border-radius: 28px;
  }

  .service-left h2 {
    font-size: 28px;
  }

  .service-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .service-right {
    justify-content: flex-start;
  }
}
</style>