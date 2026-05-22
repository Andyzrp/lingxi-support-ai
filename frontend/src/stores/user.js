import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userId: (state) => state.userInfo?.id ?? null,
    nickname: (state) => state.userInfo?.nickname || state.userInfo?.username || '用户',
  },

  actions: {
    async login(credentials) {
      const res = await authApi.login(credentials)
      this.token = res.data.access_token
      localStorage.setItem('token', this.token)
      if (res.data.refresh_token) {
        localStorage.setItem('refresh_token', res.data.refresh_token)
      }
      await this.fetchUserInfo()
    },

    async fetchUserInfo() {
      try {
        const res = await authApi.getMe()
        this.userInfo = res.data
      } catch {
        this.logout()
      }
    },

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
    },

    // 页面刷新后恢复状态
    async init() {
      if (this.token && !this.userInfo) {
        await this.fetchUserInfo()
      }
    },
  },
})