<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="not-found-code">404</div>
      <h2 class="not-found-title">页面不存在</h2>
      <p class="not-found-desc">你访问的页面已经飞走了 🚀</p>
      <div class="not-found-actions">
        <el-button
          type="primary"
          size="large"
          class="lx-gradient-btn"
          @click="router.push('/mall')"
        >
          回到商城
        </el-button>
        <el-button size="large" @click="router.back()">
          返回上一页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--lx-bg-page);
}
.not-found-content {
  text-align: center;
  padding: 40px;
}
.not-found-code {
  font-size: 96px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}
.not-found-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--lx-text-primary);
  margin: 0 0 10px;
}
.not-found-desc {
  font-size: 15px;
  color: var(--lx-text-secondary);
  margin: 0 0 32px;
}
.not-found-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>