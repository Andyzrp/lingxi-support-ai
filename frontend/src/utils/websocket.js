/**
 * 灵犀智能客服 WebSocket 管理器
 * 发送类型：chat / transfer / ping  [1]
 * 接收类型：message / thinking / transfer / error / pong  [1]
 */
import { CHANNEL_TOKEN } from '@/utils/constants'

export class ChatWebSocket {
  constructor(userId = null) {
    this.CHANNEL_TOKEN = CHANNEL_TOKEN
    this.userId = userId
    this.ws = null
    this.listeners = {}
    this.heartbeatTimer = null
    this.isManualClose = false
    this.reconnectCount = 0
    this.maxReconnect = 3
  }

  connect() {
    const base = 'ws://localhost:8000'
    let url = `${base}/api/v1/chat/ws/${this.CHANNEL_TOKEN}`
    if (this.userId) {
      url += `?user_id=${this.userId}`
    }

    console.log('🔌 WebSocket 连接中...', url)
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('✅ WebSocket 连接成功')
      this.reconnectCount = 0
      this.isManualClose = false
      this._startHeartbeat()
      this._emit('open')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type !== 'pong') {
          console.log('📩 收到消息:', data.type, data)
        }
        this._emit(data.type, data)
      } catch (e) {
        console.error('消息解析失败', e)
      }
    }

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket 断开', event.code)
      this._stopHeartbeat()
      this._emit('close', event)
      if (!this.isManualClose) {
        this._scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket 错误', error)
      this._emit('error', error)
    }
  }

  // 发送对话消息 [1]
  sendChat(content) {
    this._send({ type: 'chat', content })
  }

  // 发送转人工请求 [1]
  sendTransfer() {
    this._send({ type: 'transfer' })
  }

  // 发送退款申请
  sendRefund(orderNo, reason) {
    this._send({ type: 'refund', order_no: orderNo, reason })
  }

  // 注册事件监听
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
    return this
  }

  off(event, callback) {
    if (!this.listeners[event]) return
    this.listeners[event] = this.listeners[event]
      .filter(cb => cb !== callback)
  }

  disconnect() {
    this.isManualClose = true
    this._stopHeartbeat()
    this.ws?.close()
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }

  _send(data) {
    if (this.isConnected) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket 未连接', data)
    }
  }

  _emit(event, data) {
    this.listeners[event]?.forEach(cb => {
      try { cb(data) } catch (e) { console.error('监听器错误', e) }
    })
  }

  _startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this._send({ type: 'ping' })
    }, 30000)
  }

  _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  _scheduleReconnect() {
    if (this.reconnectCount >= this.maxReconnect) {
      console.warn('❌ 重连次数已达上限')
      this._emit('reconnect_failed')
      return
    }
    this.reconnectCount++
    const delay = 2000 * this.reconnectCount
    console.log(`🔄 ${delay / 1000}s 后第 ${this.reconnectCount} 次重连...`)
    setTimeout(() => this.connect(), delay)
  }
}