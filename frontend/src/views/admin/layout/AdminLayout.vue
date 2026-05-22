<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <AdminSidebar :is-collapsed="isCollapsed" />

    <!-- 右侧主体 -->
    <div class="admin-main" :class="{ expanded: isCollapsed }">
      <!-- 顶部导航 -->
      <AdminHeader
        :is-collapsed="isCollapsed"
        @toggle-collapse="toggleCollapse"
      />

      <!-- 页面内容区 -->
      <div class="admin-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AdminSidebar from './AdminSidebar.vue'
import AdminHeader from './AdminHeader.vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()
const isCollapsed = ref(false)

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  // 持久化折叠状态
  localStorage.setItem('admin_sidebar_collapsed', isCollapsed.value)
}

onMounted(async () => {
  // 恢复折叠状态
  const saved = localStorage.getItem('admin_sidebar_collapsed')
  if (saved === 'true') isCollapsed.value = true

  // 如果没有管理员信息，重新拉取
  if (!adminStore.adminInfo) {
    await adminStore.init()
  }
})
</script>

<style scoped lang="scss">
.admin-layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #f5f7fa;
}

// 右侧主体
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.3s ease;
  min-width: 0; // 防止 flex 子项溢出
}

// 内容区
.admin-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;

  // 滚动条美化
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #dcdfe6;
    border-radius: 3px;

    &:hover {
      background: #c0c4cc;
    }
  }
}

// 路由切换动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>