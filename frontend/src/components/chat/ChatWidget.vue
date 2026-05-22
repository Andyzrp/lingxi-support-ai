<template>
  <!-- 悬浮按钮 -->
  <div class="chat-widget">
    <!-- 未读消息气泡 -->
    <transition name="bubble">
      <div
        v-if="!chatStore.isOpen && unreadCount > 0"
        class="unread-badge"
      >
        {{ unreadCount }}
      </div>
    </transition>

    <!-- 悬浮按钮 -->
    <button
      class="chat-float-btn"
      :class="{ 'is-open': chatStore.isOpen }"
      @click="toggleChat"
      :title="chatStore.isOpen ? '关闭客服' : '联系客服'"
    >
      <!-- 使用品牌图标，从 appConfig 读取 [1] -->
      <img
        v-if="!chatStore.isOpen"
        :src="appConfig.logo.chatButton"
        :alt="appConfig.systemNameFull"
        class="chat-float-icon"
      />
      <!-- 打开状态显示关闭图标 -->
      <el-icon v-else class="close-icon"><Close /></el-icon>
    </button>

    <!-- 对话窗口 -->
    <transition name="chat-window">
      <ChatWindow v-if="chatStore.isOpen" :visible="chatStore.isOpen" />
    </transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import appConfig from '@/config/app.js'
import ChatWindow from './ChatWindow.vue'

const chatStore = useChatStore()
const userStore = useUserStore()


// 统一用 chatStore
const chatStoreReal = useChatStore()

// 未读消息数（关闭状态下收到消息时累计）
const unreadCount = ref(0)

watch(() => chatStoreReal.messages.length, (newLen, oldLen) => {
  if (!chatStoreReal.isOpen && newLen > oldLen) {
    const last = chatStoreReal.messages[newLen - 1]
    if (last?.role !== 'user') {
      unreadCount.value++
    }
  }
})

function toggleChat() {
  if (chatStoreReal.isOpen) {
    chatStoreReal.closeChat()
  } else {
    chatStoreReal.openChat()
    unreadCount.value = 0
  }
}
</script>

<style scoped>
.chat-widget {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 9998;
}

/* 悬浮按钮 */
.chat-float-btn {
  position: relative;
  width: 64px;
  height: 64px;
  border: none;
  border-radius: 20px;
  padding: 0;
  cursor: pointer;
  background: transparent;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.35);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-float-btn:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 16px 36px rgba(37, 99, 235, 0.45);
}
.chat-float-btn:active {
  transform: scale(0.96);
}
.chat-float-btn.is-open {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.chat-float-icon {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 20px;
}
.close-icon {
  font-size: 24px;
  color: #fff;
}

/* 未读角标 */
.unread-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  border: 2px solid #fff;
}

/* 窗口弹出动画 */
.chat-window-enter-active,
.chat-window-leave-active {
  transition: all 0.25s ease;
}
.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

/* 气泡动画 */
.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.2s ease;
}
.bubble-enter-from,
.bubble-leave-to {
  opacity: 0;
  transform: scale(0.5);
}
</style>