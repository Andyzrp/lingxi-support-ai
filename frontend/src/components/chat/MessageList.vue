<template>
  <div class="message-list" ref="listRef">
    <!-- 空状态 -->
    <div v-if="!chatStore.messages.length" class="empty-hint">
      <p>有什么可以帮您的吗？😊</p>
    </div>

    <!-- 消息列表 -->
    <template v-else>
      <MessageItem
        v-for="msg in chatStore.messages"
        :key="msg.id"
        :message="msg"
        @apply-refund="$emit('apply-refund', $event)"
      />
    </template>

    <!-- AI 思考中 -->
    <div v-if="chatStore.isThinking" class="thinking-bubble">
      <div class="thinking-avatar">🤖</div>
      <div class="thinking-content">
        <span class="lx-typing-dots">
          <span class="lx-typing-dot" />
          <span class="lx-typing-dot" />
          <span class="lx-typing-dot" />
        </span>
      </div>
    </div>

    <!-- 滚动锚点 -->
    <div ref="anchorRef" />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageItem from './MessageItem.vue'

const emit = defineEmits(['apply-refund'])
const chatStore = useChatStore()
const listRef   = ref(null)
const anchorRef = ref(null)

// 消息变化时自动滚到底部
watch(
  () => [chatStore.messages.length, chatStore.isThinking],
  () => {
    nextTick(() => {
      anchorRef.value?.scrollIntoView({ behavior: 'smooth' })
    })
  }
)
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8fafc;
}

/* 空状态提示 */
.empty-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--lx-text-placeholder);
}

/* AI思考气泡 */
.thinking-bubble {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.thinking-avatar {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--lx-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.thinking-content {
  padding: 12px 14px;
  background: #fff;
  border: 1px solid var(--lx-border);
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 2px 8px rgba(15,23,42,0.05);
}
</style>