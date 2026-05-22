<template>
  <div class="login-page">

    <!-- 左侧品牌介绍 -->
    <div class="login-left">
      <div class="brand">
        <!-- Logo 从 appConfig 读取 -->
        <img
          :src="appConfig.logo.mallLogo"
          :alt="appConfig.systemName"
          class="brand-svg-logo"
        />
        <p class="brand-desc">
          精选好物，极速配送，AI客服全程守护
        </p>
      </div>
      <ul class="feature-list">
        <li v-for="item in features" :key="item.text">
          <span class="feature-icon">{{ item.icon }}</span>
          <span>{{ item.text }}</span>
        </li>
      </ul>
    </div>

    <!-- 右侧登录卡片 -->
    <div class="login-right">
      <div class="login-card">
        <div class="login-card-header">
          <h2>欢迎回来</h2>
          <!-- 系统名称从 appConfig 读取 -->
          <p>登录{{ appConfig.systemName }}</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item>
            <el-button
              class="login-btn lx-gradient-btn"
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import appConfig from '@/config/app.js'

const router    = useRouter()
const route     = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度 3-20 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

const features = [
  { icon: '🛍️', text: '精选优质商品，品质有保障' },
  { icon: '🚚', text: '极速发货，全程物流跟踪' },
  { icon: '💬', text: 'AI智能客服，7×24小时在线' },
  { icon: '↩️', text: '七天无理由退换，购物无忧' },
]

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.login({
      username: form.username,
      password: form.password,
    })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/mall'
    router.push(redirect)
  } catch (err) {
    console.error('登录失败:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 30px;
  background:
    radial-gradient(circle at 20% 20%, rgba(96, 165, 250, 0.2), transparent 30%),
    radial-gradient(circle at 80% 30%, rgba(124, 58, 237, 0.1), transparent 28%),
    linear-gradient(135deg, #eff6ff 0%, #f8fafc 50%, #ffffff 100%);
}

/* 左侧 */
.login-left {
  width: 440px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.brand { margin-bottom: 48px; }
.brand-svg-logo {
  width: 360px;
  max-width: 100%;
  display: block;
  margin-bottom: 20px;
}
.brand-desc {
  font-size: 16px;
  color: var(--lx-text-secondary);
  margin: 0;
  line-height: 1.6;
}
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.feature-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: var(--lx-text-regular);
}
.feature-icon {
  font-size: 20px;
  width: 32px;
  text-align: center;
}

/* 右侧 */
.login-right {
  width: 480px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(12px);
}
.login-card-header {
  margin-bottom: 32px;
  text-align: center;
}
.login-card-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--lx-text-primary);
}
.login-card-header p {
  margin: 0;
  font-size: 14px;
  color: var(--lx-text-secondary);
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
}
.login-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: var(--lx-text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .login-left  { display: none; }
  .login-right { width: 100%;  }
}
</style>