import axios from 'axios'
import { ElMessage } from 'element-plus'

const BASE_URL = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1`

const instance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ==================== 白名单：公开接口，不携带任何 Token ====================
// config.url 是相对路径（不含 baseURL 前缀），所以这里存不含 /api/v1 的部分
const WHITE_LIST = [
  '/auth/login',
  '/auth/register',
  '/admin/auth/login',
  '/products',
  '/products/categories',
]

function _isWhiteList(url) {
  if (!url) return false
  return WHITE_LIST.some(w => url === w || url.startsWith(w + '?'))
}

// ==================== 请求拦截器 ====================
// 策略：当前页面以 /admin 开头 → 用 admin_token；其他 → 用 user token
instance.interceptors.request.use(
  (config) => {
    const url = config.url || ''

    // 白名单接口：不携带任何 Token
    if (_isWhiteList(url)) {
      delete config.headers['Authorization']
      return config
    }

    const isAdminPage = window.location.pathname.startsWith('/admin')

    if (isAdminPage) {
      const adminToken = localStorage.getItem('admin_token')
      if (adminToken) {
        config.headers.Authorization = `Bearer ${adminToken}`
      } else {
        delete config.headers['Authorization']
      }
    } else {
      const userToken = localStorage.getItem('token')
      if (userToken) {
        config.headers.Authorization = `Bearer ${userToken}`
      } else {
        delete config.headers['Authorization']
      }
    }

    return config
  },
  (error) => Promise.reject(error)
)

// ==================== 防重复刷新状态 ====================
let isRefreshing = false
let pendingQueue = []

function onRefreshed(newToken) {
  pendingQueue.forEach(cb => cb(newToken))
  pendingQueue = []
}

// ==================== 工具函数 ====================

function _clearTokenByType(isAdmin) {
  if (isAdmin) {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
  } else {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }
}

function _redirectToLogin(isAdmin) {
  const loginPath = isAdmin ? '/admin/login' : '/login'
  ElMessage.warning(
    isAdmin ? '管理员登录已过期，请重新登录' : '登录已过期，请重新登录'
  )
  setTimeout(() => {
    window.location.href = loginPath
  }, 1000)
}

// ==================== 响应拦截器 ====================
instance.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 200) {
      return res
    }
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message))
  },
  async (error) => {
    const { response, config } = error

    if (!response) {
      ElMessage.error('网络连接失败，请检查网络')
      return Promise.reject(error)
    }

    const { status } = response

    // ── 401：尝试刷新 Token ──
    if (status === 401 && !config._retry) {
      const url = config.url || ''

      // 白名单接口的 401（登录接口账号密码错误）→ 不走刷新，直接报错
      if (_isWhiteList(url)) {
        const msg = response.data?.message || '账号或密码错误'
        ElMessage.error(msg)
        return Promise.reject(error)
      }

      const isAdminRequest = window.location.pathname.startsWith('/admin')

      const refreshTokenKey = isAdminRequest
        ? 'admin_refresh_token'
        : 'refresh_token'
      const refreshUrl = isAdminRequest
        ? '/api/v1/admin/auth/refresh'
        : '/api/v1/auth/refresh'
      const tokenKey = isAdminRequest ? 'admin_token' : 'token'

      const storedRefresh = localStorage.getItem(refreshTokenKey)

      if (!storedRefresh) {
        _clearTokenByType(isAdminRequest)
        _redirectToLogin(isAdminRequest)
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingQueue.push((newToken) => {
            config.headers['Authorization'] = `Bearer ${newToken}`
            resolve(instance(config))
          })
        })
      }

      config._retry = true
      isRefreshing = true

      try {
        const res = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${refreshUrl}`,
          { refresh_token: storedRefresh },
          { headers: { 'Content-Type': 'application/json' } }
        )

        const newAccessToken = res.data?.data?.access_token
        if (!newAccessToken) throw new Error('刷新失败')

        localStorage.setItem(tokenKey, newAccessToken)
        config.headers['Authorization'] = `Bearer ${newAccessToken}`

        onRefreshed(newAccessToken)

        return instance(config)

      } catch {
        pendingQueue = []
        _clearTokenByType(isAdminRequest)
        _redirectToLogin(isAdminRequest)
        return Promise.reject(error)

      } finally {
        isRefreshing = false
      }
    }

    // ── 403 无权限 ──
    if (status === 403) {
      ElMessage.error('您没有权限执行此操作')
    } else if (status === 404) {
      ElMessage.error('请求资源不存在')
    } else if (status >= 500) {
      ElMessage.error('服务器异常，请稍后重试')
    } else {
      const msg = response.data?.message || '操作失败'
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  }
)

export default instance
