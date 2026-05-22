<template>
  <div class="admin-header">
    <!-- 左侧：折叠按钮 + 面包屑 -->
    <div class="header-left">
      <el-button
        text
        class="collapse-btn"
        @click="$emit('toggle-collapse')"
      >
        <el-icon size="20">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>

      <!-- 面包屑 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">
          工作台
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="currentPageName">
          {{ currentPageName }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 右侧：管理员信息 -->
    <div class="header-right">
      <!-- 刷新按钮 -->
      <el-tooltip content="刷新页面" placement="bottom">
        <el-button text class="icon-btn" @click="handleRefresh">
          <el-icon size="18"><Refresh /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 管理员头像 + 下拉菜单 -->
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="admin-info">
          <el-avatar :size="32" class="admin-avatar">
            {{ adminStore.adminName?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="admin-meta">
            <span class="admin-name">{{ adminStore.adminName }}</span>
            <span class="admin-role">{{ adminStore.roleText }}</span>
          </div>
          <el-icon class="arrow-icon"><ArrowDown /></el-icon>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile" :icon="User">
              个人信息
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" :icon="SwitchButton">
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Fold,
  Expand,
  Refresh,
  ArrowDown,
  User,
  SwitchButton,
} from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle-collapse'])

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

// 当前页面名称（面包屑用）
const pageNameMap = {
  '/admin/dashboard':     '工作台',
  '/admin/knowledge':     '知识库管理',
  '/admin/bots':          'Bot 管理',
  '/admin/agents':        'Agent 管理',
  '/admin/channels':      '渠道管理',
  '/admin/orders':        '订单管理',
  '/admin/conversations': '会话记录',
  '/admin/annotations':   '数据标注',
  '/admin/reports':       '数据报表',
  '/admin/settings':      '系统设置',
}

const currentPageName = computed(() => {
  return pageNameMap[route.path] || route.meta?.title || ''
})

function handleRefresh() {
  window.location.reload()
}

async function handleCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确认退出登录？', '提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      })
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_refresh_token')
      router.push('/admin/login')
      ElMessage.success('已退出登录')
    } catch {
      // 用户取消
    }
  } else if (command === 'profile') {
    ElMessage.info('个人信息功能开发中')
  }
}

</script>

<style scoped lang="scss">
.admin-header {
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

// 左侧
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  color: #606266;
  border-radius: 6px;

  &:hover {
    background: #f5f7fa;
    color: #409eff;
  }
}

.breadcrumb {
  :deep(.el-breadcrumb__inner) {
    color: #909399;
    font-size: 13px;

    &.is-link:hover {
      color: #409eff;
    }
  }

  :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
    color: #303133;
    font-weight: 500;
  }
}

// 右侧
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  color: #606266;
  border-radius: 6px;

  &:hover {
    background: #f5f7fa;
    color: #409eff;
  }
}

// 管理员信息
.admin-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f5f7fa;
  }
}

.admin-avatar {
  background: linear-gradient(135deg, #5b8af5, #3d6fd4);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.admin-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.admin-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.admin-role {
  font-size: 11px;
  color: #909399;
}

.arrow-icon {
  color: #909399;
  font-size: 12px;
  transition: transform 0.2s;
}
</style>