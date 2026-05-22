<template>
  <footer class="lx-footer">
    <div class="lx-footer-inner">

      <!-- 品牌区：Logo 和 Slogan 从 appConfig 读取 -->
      <div class="footer-brand">
        <img
          :src="appConfig.logo.mallMono"
          :alt="appConfig.systemName"
          class="footer-logo-img"
        />
        <p class="footer-slogan">
          贴心服务全程在线，让每一次购物都更安心
        </p>
      </div>

      <!-- 链接区 -->
      <div class="footer-links">
        <div class="link-group">
          <h4>商城</h4>
          <router-link to="/mall">商城首页</router-link>
          <router-link to="/mall/products">全部商品</router-link>
          <router-link to="/mall/orders">我的订单</router-link>
        </div>
        <div class="link-group">
          <h4>客服</h4>
          <span @click="openChat">在线客服</span>
          <span>7×24 小时服务</span>
          <span>平均响应 &lt; 1s</span>
        </div>
        <div class="link-group">
          <h4>技术</h4>
          <span>Vue3 + FastAPI</span>
          <span>LangGraph Agent</span>
          <span>私有化部署</span>
        </div>
      </div>
    </div>

    <!-- 底部版权：从 appConfig 读取 -->
    <div class="footer-bottom">
      <span>{{ appConfig.copyright }}</span>
      <span class="footer-tech">
        Powered by
        <span
          v-for="tag in appConfig.techTags"
          :key="tag"
          class="tech-tag"
        >
          {{ tag }}
        </span>
      </span>
    </div>
  </footer>
</template>

<script setup>
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import appConfig from '@/config/app.js'

const chatStore = useChatStore()
const userStore = useUserStore()

function openChat() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后使用客服功能')
    return
  }
  chatStore.openChat()
}
</script>

<style scoped>
.lx-footer {
  background: var(--lx-text-primary);
  color: rgba(255, 255, 255, 0.7);
  margin-top: auto;
}
.lx-footer-inner {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 48px var(--lx-content-padding) 32px;
  display: flex;
  gap: 60px;
  align-items: flex-start;
}

/* 品牌区 */
.footer-brand { flex: 1.5; }
.footer-logo-img {
  width: 160px;
  height: auto;
  display: block;
  margin-bottom: 12px;
}
.footer-slogan {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.5);
  max-width: 260px;
}

/* 链接区 */
.footer-links {
  display: flex;
  gap: 60px;
  flex: 2;
}
.link-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.link-group h4 {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.link-group a,
.link-group span {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s ease;
  line-height: 1;
}
.link-group a:hover,
.link-group span:hover {
  color: rgba(255, 255, 255, 0.9);
}

/* 版权行 */
.footer-bottom {
  max-width: var(--lx-content-max-width);
  margin: 0 auto;
  padding: 16px var(--lx-content-padding);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}
.footer-tech {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tech-tag {
  padding: 2px 8px;
  border-radius: var(--lx-radius-full);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}

/* 响应式 */
@media (max-width: 768px) {
  .lx-footer-inner {
    flex-direction: column;
    gap: 32px;
    padding: 32px 16px 24px;
  }
  .footer-links  { gap: 32px; }
  .footer-bottom {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>