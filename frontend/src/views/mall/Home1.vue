<template>
  <div class="mall-home">
    <Header />
    <!-- Hero Banner -->
    <section class="hero-banner">
      <div class="hero-inner">
        <div class="hero-content">
          <div class="hero-badge">🤖 AI 智能客服加持</div>
          <h1 class="hero-title">
            灵犀智能商城
            <span class="hero-title-highlight">极速响应每一次服务</span>
          </h1>
          <p class="hero-desc">
            Bot + Agent 双层智能拦截，订单 / 物流 / 退款一键查询
            <br />平均响应不超过 1 秒，7×24 小时在线
          </p>
          <div class="hero-actions">
            <el-button
              size="large"
              class="lx-gradient-btn"
              @click="router.push('/mall/products')"
            >
              立即选购
            </el-button>
            <el-button size="large" plain @click="openChat">
              💬 咨询客服
            </el-button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="hero-card">
            <div class="hero-card-header">
              <span class="dot dot-red" />
              <span class="dot dot-yellow" />
              <span class="dot dot-green" />
            </div>
            <div class="chat-preview">
              <div class="preview-msg assistant">
                您好！我是灵犀客服 🤖 有什么可以帮您？
              </div>
              <div class="preview-msg user">我的订单什么时候发货？</div>
              <div class="preview-msg assistant">
                正在查询您的订单信息...
                <span class="preview-dots"><i /><i /><i /></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心能力 -->
    <section class="features-section">
      <div class="section-inner">
        <div class="section-header">
          <h2>为什么选择灵犀</h2>
          <p>专为电商场景打造的智能客服系统</p>
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
        <div class="section-header">
          <h2>热销商品</h2>
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
            <!-- ✅ 修复：router.push( 加左括号 -->
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
                <span class="product-price">{{ formatPrice(product.price) }}</span>
                <el-button
                  type="primary"
                  size="small"
                  class="lx-gradient-btn"
                  @click.stop="router.push(`/mall/products/${product.id}`)"
                >
                <!-- ✅ 修复：router.push( 加左括号 -->
                  查看详情
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI客服体验区 -->
    <section class="ai-section">
      <div class="section-inner">
        <div class="ai-card">
          <div class="ai-left">
            <h2>体验 AI 智能客服</h2>
            <p>支持订单查询、物流跟踪、退款申请，随时在线为您服务</p>
            <div class="ai-stats">
              <div v-for="stat in aiStats" :key="stat.label" class="ai-stat">
                <span class="stat-value">{{ stat.value }}</span>
                <span class="stat-label">{{ stat.label }}</span>
              </div>
            </div>
            <el-button size="large" class="lx-gradient-btn" @click="openChat">
              💬 立即咨询
            </el-button>
          </div>
          <div class="ai-right">
            <div
              v-for="tag in aiTags"
              :key="tag"
              class="ai-tag lx-faq-tag"
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

const router    = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const loading     = ref(false)
const hotProducts = ref([])

const features = [
  {
    icon: '🎯',
    title: '精准意图识别',
    desc: '7种意图全覆盖，退款、物流、订单查询秒速响应',
  },
  {
    icon: '🤖',
    title: 'Bot + Agent 双层',
    desc: 'FAQ知识库优先拦截，复杂问题 LangGraph Agent 处理',
  },
  {
    icon: '🔧',
    title: '工具调用能力',
    desc: '直连订单/物流系统，实时查询无需等待',
  },
  {
    icon: '👥',
    title: '无缝转人工',
    desc: '情绪激动或复杂投诉自动转接，上下文完整保留',
  },
]

const aiStats = [
  { value: '< 1s',  label: '平均响应时间' },
  { value: '7×24', label: '全天候在线' },
  { value: '98%',  label: '问题解决率' },
  { value: '7+',   label: '意图覆盖' },
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
    // ✅ 适配后端返回格式
    hotProducts.value = Array.isArray(res) ? res : (res.data || [])
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
/* ===== 全局容器 ===== */
.mall-home {
  min-height: 100vh;
}

.hero-inner,
.section-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ===== Hero Banner ===== */
.hero-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 80px 0;
  color: #fff;
}

.hero-inner {
  display: flex;
  align-items: center;
  gap: 60px;
}

.hero-content { flex: 1; }

.hero-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 4px 16px;
  font-size: 14px;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
}

.hero-title-highlight {
  display: block;
  font-size: 32px;
  opacity: 0.85;
}

.hero-desc {
  font-size: 16px;
  opacity: 0.85;
  line-height: 1.8;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

/* ===== Hero 聊天卡片 ===== */
.hero-visual {
  flex: 1;
  display: flex;
  justify-content: center;
}

.hero-card {
  background: #fff;
  border-radius: 16px;
  width: 340px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.hero-card-header {
  background: #f5f5f5;
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
.dot-red    { background: #ff5f56; }
.dot-yellow { background: #ffbd2e; }
.dot-green  { background: #27c93f; }

.chat-preview {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-msg {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  max-width: 85%;
  line-height: 1.5;
  color: #333;
}

.preview-msg.assistant {
  background: #f0f2f5;
  align-self: flex-start;
}

.preview-msg.user {
  background: #667eea;
  color: #fff;
  align-self: flex-end;
}

.preview-dots i {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  margin: 0 2px;
  animation: dot-bounce 1.2s infinite;
}
.preview-dots i:nth-child(2) { animation-delay: 0.2s; }
.preview-dots i:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

/* ===== 核心能力 ===== */
.features-section {
  padding: 80px 0;
  background: #f8f9fa;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-header h2 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.section-header p {
  color: #666;
  font-size: 16px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.feature-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.feature-card p {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

/* ===== 热销商品 ===== */
.products-section {
  padding: 80px 0;
}

.products-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: left;
  margin-bottom: 32px;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.product-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.product-img-wrap {
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: #f5f5f5;
}

.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.product-card:hover .product-img {
  transform: scale(1.05);
}

.product-info { padding: 16px; }

.product-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-price {
  font-size: 20px;
  font-weight: 700;
  color: #ff4757;
}

.product-skeleton {
  border-radius: 16px;
  overflow: hidden;
  padding: 16px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

/* ===== AI 体验区 ===== */
.ai-section {
  padding: 80px 0;
  background: #f8f9fa;
}

.ai-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 24px;
  padding: 60px;
  display: flex;
  align-items: center;
  gap: 60px;
  color: #fff;
}

.ai-left { flex: 1; }

.ai-left h2 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
}

.ai-left p {
  font-size: 16px;
  opacity: 0.85;
  margin-bottom: 32px;
}

.ai-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 32px;
}

.ai-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 13px;
  opacity: 0.75;
}

.ai-right {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.ai-tag {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  border-radius: 24px;
  padding: 10px 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.ai-tag:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* ===== 渐变按钮 ===== */
.lx-gradient-btn {
  background: linear-gradient(135deg, #667eea, #764ba2) !important;
  border: none !important;
  color: #fff !important;
}

.lx-gradient-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .features-grid,
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-inner {
    flex-direction: column;
  }

  .hero-visual {
    display: none;
  }

  .hero-title {
    font-size: 28px;
  }

  .features-grid,
  .products-grid {
    grid-template-columns: 1fr;
  }

  .ai-card {
    flex-direction: column;
    padding: 32px 24px;
  }

  .ai-stats {
    flex-wrap: wrap;
    gap: 16px;
  }
}
</style>