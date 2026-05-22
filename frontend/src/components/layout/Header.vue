<template>
  <header class="lx-header">
    <div class="lx-header-inner">

      <!-- Logo：从 appConfig 读取路径和名称 -->
      <div class="header-logo" @click="router.push('/mall')">
        <img
          :src="appConfig.logo.mallHeader"
          :alt="appConfig.systemName"
          class="header-logo-img"
        />
      </div>

      <!-- 中间导航 -->
      <nav class="header-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <!-- 右侧操作区 -->
      <div class="header-actions">

        <!-- 未登录 -->
        <template v-if="!userStore.isLoggedIn">
          <el-button text @click="router.push('/login')">登录</el-button>
          <el-button
            type="primary"
            class="lx-gradient-btn"
            @click="router.push('/register')"
          >
            注册
          </el-button>
        </template>

        <!-- 已登录 -->
        <template v-else>
          <el-button
            text
            :icon="List"
            @click="router.push('/mall/orders')"
          >
            我的订单
          </el-button>

          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-avatar">
              <div class="avatar-circle">
                {{ userStore.nickname.charAt(0).toUpperCase() }}
              </div>
              <span class="user-name">{{ userStore.nickname }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon> 个人信息
                </el-dropdown-item>
                <el-dropdown-item command="orders">
                  <el-icon><List /></el-icon> 我的订单
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span style="color: #ef4444">退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { List, ArrowDown, User, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import appConfig from '@/config/app.js'

const router    = useRouter()
const route     = useRoute()
const userStore = useUserStore()
const chatStore = useChatStore()

// 导航菜单
const navItems = [
  { label: '商城首页', path: '/mall'          },
  { label: '全部商品', path: '/mall/products' },
  { label: '我的订单', path: '/mall/orders'   },
]

function isActive(path) {
  if (path === '/mall') {
    return route.path === '/mall'
  }
  return route.path.startsWith(path)
}

async function handleCommand(command) {
  switch (command) {
    case 'profile':
      ElMessage.info('个人信息功能开发中')
      break
    case 'orders':
      router.push('/mall/orders')
      break
    case 'logout':
      await ElMessageBox.confirm(
        '确定要退出登录吗？', '提示',
        {
          confirmButtonText: '退出',
          cancelButtonText:  '取消',
          type: 'warning',
        }
      )
      userStore.logout()
      chatStore.reset()
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.lx-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: var(--lx-header-height);
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid var(--lx-border);
  backdrop-filter: blur(12px);
  box-shadow: 0 1px 8px rgba(15, 23, 42, 0.06);
}
.lx-header-inner {
  max-width: var(--lx-content-max-width);
  height: 100%;
  margin: 0 auto;
  padding: 0 var(--lx-content-padding);
  display: flex;
  align-items: center;
  gap: 32px;
}

/* Logo */
.header-logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}
.header-logo-img {
  width: 160px;
  height: 36px;
  object-fit: contain;
  display: block;
}

/* 导航 */
.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}
.nav-item {
  padding: 6px 14px;
  border-radius: var(--lx-radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--lx-text-regular);
  transition: all 0.2s ease;
  text-decoration: none;
}
.nav-item:hover {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
}
.nav-item.active {
  color: var(--lx-primary);
  background: var(--lx-primary-soft);
  font-weight: 600;
}

/* 右侧操作 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 用户头像 */
.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: var(--lx-radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.user-avatar:hover {
  background: var(--lx-bg-muted);
  border-color: var(--lx-border);
}
.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--lx-text-regular);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.arrow-icon {
  font-size: 12px;
  color: var(--lx-text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .header-nav { display: none; }
  .user-name  { display: none; }
}
</style>