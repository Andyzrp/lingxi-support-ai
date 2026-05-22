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
          注册即享会员权益，AI客服全程守护您的购物体验
        </p>
      </div>
	  <!-- ✅ 加上特性列表 -->
	  <ul class="feature-list">
		<li v-for="item in features" :key="item.text">
			<span class="feature-icon">{{ item.icon }}</span>
			<span>{{ item.text }}</span>
		</li>
	  </ul>
    </div>

    <!-- 右侧注册卡片 -->
    <div class="login-right">
      <div class="login-card">
        <div class="login-card-header">
          <h2>创建账号</h2>
          <p>加入灵犀商城，开启智能购物体验</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="3-20位字母或数字"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="昵称" prop="nickname">
            <el-input
              v-model="form.nickname"
              placeholder="你的昵称（选填）"
              size="large"
              :prefix-icon="Avatar"
            />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="请输入手机号（选填）"
              size="large"
              :prefix-icon="Phone"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="至少6位"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button
              class="login-btn lx-gradient-btn"
              size="large"
              :loading="loading"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '立即注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          已有账号？
          <router-link to="/login">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Phone, Avatar } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import appConfig from '@/config/app.js'

const router  = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username:        '',
  nickname:        '',
  phone:           '',
  password:        '',
  confirmPassword: '',
})

// 确认密码校验
const validateConfirmPwd = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度 3-20 位', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '只能包含字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '手机号格式不正确',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' },
  ],
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    // 对接后端注册接口 [1]
    await authApi.register({
      username: form.username,
      nickname: form.nickname  || undefined,
      phone:    form.phone     || undefined,
      password: form.password,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
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

/* 右侧 */
.login-right {
  width: 480px;
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
  margin-bottom: 24px;
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
  letter-spacing: 1px;
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