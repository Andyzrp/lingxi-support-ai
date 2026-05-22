<template>
  <div class="admin-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Logo 区域 -->
    <div class="sidebar-logo">
      <img src="/brand/lingxi-admin-logo-light.svg" alt="logo" class="logo-icon" />
      <span v-if="!isCollapsed" class="logo-text">灵犀客服</span>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      class="sidebar-menu"
      background-color="#1a1f3c"
      text-color="rgba(255, 255, 255, 0.65)"
      active-text-color="#5b8af5"
      router
    >
      <!-- 工作台 -->
      <el-menu-item index="/admin/dashboard">
        <el-icon><DataLine /></el-icon>
        <template #title>工作台</template>
      </el-menu-item>

      <!-- 知识库管理 -->
      <el-sub-menu index="knowledge">
        <template #title>
          <el-icon><Collection /></el-icon>
          <span>知识库管理</span>
        </template>
        <el-menu-item index="/admin/knowledge">知识库列表</el-menu-item>
      </el-sub-menu>

      <!-- Bot 管理 -->
      <el-sub-menu index="bot">
        <template #title>
          <el-icon><Service /></el-icon>
          <span>Bot 管理</span>
        </template>
        <el-menu-item index="/admin/bots">Bot 列表</el-menu-item>
      </el-sub-menu>

      <!-- Agent 管理 -->
      <el-sub-menu index="agent">
        <template #title>
          <el-icon><Cpu /></el-icon>
          <span>Agent 管理</span>
        </template>
        <el-menu-item index="/admin/agents">Agent 列表</el-menu-item>
      </el-sub-menu>

      <!-- 渠道管理 -->
      <el-menu-item index="/admin/channels">
        <el-icon><Connection /></el-icon>
        <template #title>渠道管理</template>
      </el-menu-item>

      <!-- 订单管理 -->
      <el-menu-item index="/admin/orders">
        <el-icon><List /></el-icon>
        <template #title>订单管理</template>
      </el-menu-item>

      <!-- 会话记录 -->
      <el-menu-item index="/admin/conversations">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>会话记录</template>
      </el-menu-item>

      <!-- 数据标注 -->
      <el-menu-item index="/admin/annotations">
        <el-icon><Collection /></el-icon>
        <template #title>数据标注</template>
      </el-menu-item>

      <!-- 数据报表 -->
      <el-menu-item index="/admin/reports">
        <el-icon><TrendCharts /></el-icon>
        <template #title>数据报表</template>
      </el-menu-item>

      <!-- 系统设置 -->
      <el-menu-item index="/admin/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系统设置</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataLine,
  Collection,
  Service,
  Cpu,
  Connection,
  List,
  ChatDotRound,
  TrendCharts,
  Setting,
} from '@element-plus/icons-vue'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()

// 当前激活菜单（精确匹配路径）
const activeMenu = computed(() => {
  const path = route.path
  // 子页面高亮父菜单
  if (path.startsWith('/admin/knowledge')) return '/admin/knowledge'
  if (path.startsWith('/admin/bots')) return '/admin/bots'
  if (path.startsWith('/admin/agents')) return '/admin/agents'
  return path
})
</script>

<style scoped lang="scss">
.admin-sidebar {
  width: 220px;
  height: 100vh;
  background: #1a1f3c;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;

  &.collapsed {
    width: 64px;
  }
}

// Logo
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.logo-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
  letter-spacing: 1px;
}

// 菜单
.sidebar-menu {
  flex: 1;
  border: none;
  overflow-y: auto;
  overflow-x: hidden;
  background: transparent;

  // 滚动条美化
  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    color: rgba(255, 255, 255, 0.65);
    height: 48px;
    line-height: 48px;
    margin: 2px 8px;
    border-radius: 8px;
    transition: all 0.2s;

    &:hover {
      background: rgba(91, 138, 245, 0.12) !important;
      color: #ffffff;
    }
  }

  :deep(.el-menu-item.is-active) {
    background: rgba(91, 138, 245, 0.2) !important;
    color: #5b8af5 !important;
    font-weight: 600;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 20px;
      background: #5b8af5;
      border-radius: 0 3px 3px 0;
    }
  }

  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 48px !important;
    height: 42px;
    line-height: 42px;
    font-size: 13px;
  }

  // 折叠时隐藏子菜单文字
  :deep(.el-menu--collapse) {
    .el-sub-menu__title span,
    .el-menu-item span {
      display: none;
    }
  }

  // 子菜单弹出层（dark 主题）
  :deep(.el-menu--popup) {
    background: #1a1f3c !important;
    border: none !important;
    min-width: 160px;

    .el-menu-item,
    .el-sub-menu__title {
      color: rgba(255, 255, 255, 0.65) !important;
      background: transparent !important;

      &:hover {
        background: rgba(91, 138, 245, 0.12) !important;
        color: #ffffff !important;
      }
    }

    .el-menu-item.is-active {
      background: rgba(91, 138, 245, 0.2) !important;
      color: #5b8af5 !important;
    }
  }
}
</style>