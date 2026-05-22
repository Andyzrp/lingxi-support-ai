import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminAuthApi } from '@/api/admin'

export const useAdminStore = defineStore('admin', () => {
  // ==================== State ====================
  const token = ref(localStorage.getItem('admin_token') || '')
  const adminInfo = ref(null)

  // ==================== Getters ====================
  const isLoggedIn = computed(() => !!token.value)
  const adminName = computed(() => adminInfo.value?.nickname || adminInfo.value?.username || '管理员')
  const adminRole = computed(() => adminInfo.value?.role || '')

  const roleText = computed(() => {
    const roleMap = {
      super_admin: '超级管理员',
      admin: '管理员',
      operator: '运营人员',
      viewer: '只读用户',
    }
    return roleMap[adminRole.value] || adminRole.value
  })

  // ==================== Actions ====================

  // 登录
  async function login(username, password) {
    const res = await adminAuthApi.login({ username, password })
    const access_token = res.data?.access_token
    const refresh_token = res.data?.refresh_token
    const admin_info = res.data?.admin_info

    if (!access_token) {
      throw new Error('登录响应中未找到 access_token')
    }

    token.value = access_token
    localStorage.setItem('admin_token', access_token)
    if (refresh_token) {
      localStorage.setItem('admin_refresh_token', refresh_token)
    }

    if (admin_info) {
      adminInfo.value = admin_info
    } else {
      await fetchAdminInfo()
    }

    return res
  }

  // 获取当前管理员信息
  async function fetchAdminInfo() {
    try {
      const res = await adminAuthApi.getMe()
      adminInfo.value = res.data
      return res.data
    } catch (error) {
      console.error('获取管理员信息失败:', error)
      throw error
    }
  }

  // 退出登录
  function logout() {
    token.value = ''
    adminInfo.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
  }

  // 检查是否已有 token，初始化时加载管理员信息
  async function init() {
    if (token.value) {
      try {
        await fetchAdminInfo()
      } catch {
        logout()
      }
    }
  }

  return {
    token,
    adminInfo,
    isLoggedIn,
    adminName,
    adminRole,
    roleText,
    login,
    fetchAdminInfo,
    logout,
    init,
  }
})