import { ORDER_STATUS } from './constants'

/**
 * 格式化金额
 * formatPrice(7999) → '¥7,999.00'
 */
export function formatPrice(price) {
  if (price == null) return '¥0.00'
  return `¥${Number(price).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * 格式化时间
 * formatTime('2026-04-30T18:02:02') → '04-30 18:02'
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  const date   = new Date(timestamp)
  const month  = String(date.getMonth() + 1).padStart(2, '0')
  const day    = String(date.getDate()).padStart(2, '0')
  const hour   = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

/**
 * 格式化日期
 * formatDate('2026-04-30T18:02:02') → '2026-04-30'
 */
export function formatDate(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  }).replace(/\//g, '-')
}

/**
 * 获取订单状态信息
 * getOrderStatus(2) → { text: '已发货', color: '...', tag: 'success' }
 */
export function getOrderStatus(status) {
  return ORDER_STATUS[status] ?? { text: '未知', color: '#909399', tag: 'info' }
}

/**
 * 截断长文本
 * truncate('很长的文字...', 20) → '很长的文字...（截断）'
 */
export function truncate(text, maxLen = 30) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

// ✅ 新增 —— 商品占位图
export function PLACEHOLDER_IMG(id) {
  const colors = ['FFB347', 'FF6B6B', '4ECDC4', '45B7D1', '96CEB4', 'FFEAA7']
  const color  = colors[(id ?? 0) % colors.length]
  return `https://via.placeholder.com/400x400/${color}/ffffff?text=Product+${id ?? ''}`
}