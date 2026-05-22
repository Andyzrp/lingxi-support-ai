import appConfig from '@/config/app.js'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/mall'
  },

  // ── 认证 ──────────────────────────────
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { guest: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { guest: true, title: '注册' }
  },

  // ── 商城前台 ───────────────────────────
  {
    path: '/mall',
    name: 'Mall',
    component: () => import('@/views/mall/Home.vue'),
    meta: { title: '灵犀商城' }
  },
  {
    path: '/mall/products',
    name: 'ProductList',
    component: () => import('@/views/mall/ProductList.vue'),
    meta: { title: '全部商品' }
  },
  {
    path: '/mall/products/:id',
    name: 'ProductDetail',
    component: () => import('@/views/mall/ProductDetail.vue'),
    meta: { title: '商品详情' }
  },
  {
    path: '/mall/orders',
    name: 'Orders',
    component: () => import('@/views/mall/Orders.vue'),
    meta: { requiresAuth: true, title: '我的订单' }
  },

  // ── 访客对话页（免登录）──
  {
    path: '/chat',
    name: 'ChatPage',
    component: () => import('@/views/chat/ChatPage.vue'),
    meta: { title: '灵犀智能客服', requiresAuth: false, requiresAdmin: false },
  },

  // ── 后台管理 ───────────────────────────
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/Login.vue'),
    meta: { adminGuest: true, title: '管理员登录' }
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/layout/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      // 工作台
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '工作台' }
      },
      // 知识库管理
      {
        path: 'knowledge',
        name: 'KnowledgeList',
        component: () => import('@/views/admin/knowledge/KnowledgeList.vue'),
        meta: { title: '知识库管理' }
      },
      {
        path: 'knowledge/:id/items',
        name: 'KnowledgeItems',
        component: () => import('@/views/admin/knowledge/KnowledgeItems.vue'),
        meta: { title: '知识条目管理' }
      },
      {
        path: 'knowledge/:id/import',
        name: 'KnowledgeImport',
        component: () => import('@/views/admin/knowledge/KnowledgeImport.vue'),
        meta: { title: 'Excel 导入' }
      },
      {
        path: 'knowledge/:id/search',
        name: 'KnowledgeSearch',
        component: () => import('@/views/admin/knowledge/KnowledgeSearch.vue'),
        meta: { title: '检索效果测试' }
      },
      // Bot 管理
      {
        path: 'bots',
        name: 'BotList',
        component: () => import('@/views/admin/bot/BotList.vue'),
        meta: { title: 'Bot 管理' }
      },
      {
        path: 'bots/:id/keywords',
        name: 'BotKeywords',
        component: () => import('@/views/admin/bot/BotKeywords.vue'),
        meta: { title: '关键词管理' }
      },
      // Agent 管理
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('@/views/admin/agent/AgentList.vue'),
        meta: { title: 'Agent 管理' }
      },
      {
        path: 'agents/:id/versions',
        name: 'AgentVersions',
        component: () => import('@/views/admin/agent/AgentVersions.vue'),
        meta: { title: 'Agent 版本管理' }
      },
      // 渠道管理
      {
        path: 'channels',
        name: 'ChannelList',
        component: () => import('@/views/admin/channel/ChannelList.vue'),
        meta: { title: '渠道管理' }
      },
      {
        path: 'channels/:id/config',
        name: 'ChannelConfig',
        component: () => import('@/views/admin/channel/ChannelConfig.vue'),
        meta: { title: '渠道内容配置' }
      },
      // 订单管理
      {
        path: 'orders',
        name: 'AdminOrders',
        component: () => import('@/views/admin/order/OrderList.vue'),
        meta: { title: '订单管理' }
      },
      // 会话记录
      {
        path: 'conversations',
        name: 'ConversationList',
        component: () => import('@/views/admin/conversation/ConversationList.vue'),
        meta: { title: '会话记录' }
      },
      // 数据标注
      {
        path: 'annotations',
        name: 'AdminAnnotations',
        component: () => import('@/views/admin/conversation/AnnotationList.vue'),
        meta: { title: '数据标注' }
      },
      // 数据报表
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/admin/reports/ReportsDashboard.vue'),
        meta: { title: '数据报表' }
      },
      // 系统设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/admin/settings/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },

  // ── 404 ───────────────────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

// ── 路由守卫 ──────────────────────────────
router.beforeEach((to, from, next) => {
  // 动态设置页面标题
  const isAdminRoute = to.path.startsWith('/admin')
  const suffix = isAdminRoute ? appConfig.titleSuffixAdmin : appConfig.titleSuffix
  document.title = to.meta.title
    ? `${to.meta.title}${suffix}`
    : appConfig.systemName

  const token      = localStorage.getItem('token')
  const adminToken = localStorage.getItem('admin_token')
  const isLoggedIn      = !!token
  const isAdminLoggedIn = !!adminToken

  // ── 前台守卫 ──────────────────────────
  // 需要用户登录但未登录 → 跳用户登录页
  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  // 已登录用户访问登录/注册页 → 跳商城首页
  if (to.meta.guest && isLoggedIn) {
    next({ name: 'Mall' })
    return
  }

  // ── 后台守卫 ──────────────────────────
  // 需要管理员登录但未登录 → 跳管理员登录页
  if (to.meta.requiresAdmin && !isAdminLoggedIn) {
    next({ name: 'AdminLogin', query: { redirect: to.fullPath } })
    return
  }
  // 已登录管理员访问管理员登录页 → 跳工作台
  if (to.meta.adminGuest && isAdminLoggedIn) {
    next({ name: 'AdminDashboard' })
    return
  }

  next()
})

export default router