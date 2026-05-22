<template>
  <div class="admin-login-page">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo 区域 -->
      <div class="login-header">
        <div class="logo-wrap">
          <img src="/brand/lingxi-login-logo-dark.svg" alt="灵犀客服" class="logo-img" />
        </div>
        <h1 class="system-title">灵犀智能客服</h1>
        <p class="system-subtitle">后台管理平台</p>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入管理员账号"
            size="large"
            clearable
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部提示 -->
      <div class="login-footer">
        <span>灵犀智能客服系统 &copy; 2026</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123456',
})

const rules = {
  username: [
    { required: true, message: '请输入管理员账号', trigger: 'blur' },
    { min: 2, max: 50, message: '账号长度 2-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于 6 位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await adminStore.login(form.username, form.password)
      ElMessage.success('登录成功，欢迎回来！')
      router.push('/admin/dashboard')
    } catch (error) {
      const status = error?.response?.status
      let msg = '登录失败，请检查账号密码'
      if (status === 401) {
        msg = '账号或密码错误'
      } else if (error?.message) {
        msg = error.message
      } else if (error?.response?.data?.message) {
        msg = error.response.data.message
      }
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>
<style scoped lang="scss">
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1f3c 0%, #2d3561 50%, #1a1f3c 100%);
  position: relative;
  overflow: hidden;
}

// 背景动画圆
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
  background: radial-gradient(circle, #5b8af5, transparent);
  animation: float 8s ease-in-out infinite;
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  top: -150px;
  left: -150px;
  animation-delay: 0s;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  right: -100px;
  animation-delay: 3s;
}

.bg-circle-3 {
  width: 300px;
  height: 300px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 6s;
}

@keyframes float {
  0%, 100% { transform: scale(1) translateY(0); }
  50%       { transform: scale(1.1) translateY(-20px); }
}

// 登录卡片
.login-card {
  position: relative;
  width: 420px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
  z-index: 10;
}

// Header
.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-wrap {
  margin-bottom: 16px;
  text-align: center;
}

.logo-img {
  width: 240px;
  height: auto;
  display: block;
  margin: 0 0 16px 80px;
  filter: drop-shadow(0 4px 12px rgba(91, 138, 245, 0.5));
}

.system-title {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 6px;
  letter-spacing: 2px;
}

.system-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  letter-spacing: 1px;
}

// 表单
.login-form {
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: none;
    border-radius: 10px;
    transition: all 0.3s;

    &:hover {
      border-color: rgba(91, 138, 245, 0.5);
    }

    &.is-focus {
      border-color: #5b8af5;
      background: rgba(91, 138, 245, 0.1);
      box-shadow: 0 0 0 3px rgba(91, 138, 245, 0.15);
    }
  }

  :deep(.el-input__inner) {
    color: #ffffff;
    font-size: 14px;

    &::placeholder {
      color: rgba(255, 255, 255, 0.35);
    }
  }

  :deep(.el-input__prefix-icon) {
    color: rgba(255, 255, 255, 0.4);
  }

  :deep(.el-form-item) {
    margin-bottom: 20px;
  }

  :deep(.el-form-item__error) {
    color: #ff7875;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  border-radius: 10px;
  background: linear-gradient(135deg, #5b8af5, #3d6fd4);
  border: none;
  margin-top: 8px;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(91, 138, 245, 0.5);
  }

  &:active {
    transform: translateY(0);
  }
}

// 底部
.login-footer {
  text-align: center;
  margin-top: 28px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.25);
}
</style>
