<template>
  <div class="input-box">

    <!-- FAQ 快捷问题（无消息时显示）-->
    <div class="faq-bar" v-if="showFaq">
      <span
        v-for="tag in faqTags"
        :key="tag"
        class="lx-faq-tag"
        @click="sendFaq(tag)"
      >
        {{ tag }}
      </span>
    </div>

    <!-- 输入区 -->
    <div class="input-bar">
      <el-input
        ref="inputRef"
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入消息，Enter 发送..."
        resize="none"
        class="chat-textarea"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.exact="handleNewLine"
      />
      <div class="input-actions">
        <!-- 转人工按钮 -->
        <el-tooltip content="转人工客服" placement="top">
          <el-button
            text
            size="small"
            class="transfer-icon-btn"
            @click="emit('transfer')"
          >
            <el-icon><Service /></el-icon>
          </el-button>
        </el-tooltip>

        <!-- 发送按钮 -->
        <el-button
          type="primary"
          size="small"
          class="lx-gradient-btn send-btn"
          :disabled="!inputText.trim()"
          :loading="!chatStore.isConnected"
          @click="handleSend"
        >
          {{ chatStore.isConnected ? '发送' : '连接中' }}
        </el-button>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="input-hint">
      <span>Enter 发送</span>
      <span>Shift + Enter 换行</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Service } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'

const emit = defineEmits(['send', 'transfer'])

const chatStore = useChatStore()
const inputRef  = ref(null)
const inputText = ref('')

const showFaq = computed(() => chatStore.messages.length <= 1)

const faqTags = [
  '我的订单在哪里？',
  '怎么申请退款？',
  '快递多久到？',
  '地址填错了怎么办？',
]

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  if (!chatStore.isConnected) {
    ElMessage.warning('正在连接中，请稍候...')
    return
  }
  emit('send', text)
  inputText.value = ''
  inputRef.value?.focus()
}

function handleNewLine() {
  inputText.value += '\n'
}

function sendFaq(tag) {
  if (!chatStore.isConnected) {
    ElMessage.warning('正在连接中，请稍候...')
    return
  }
  emit('send', tag)
}
</script>

<style scoped>
.input-box {
  border-top: 1px solid var(--lx-border);
  background: #fff;
  flex-shrink: 0;
}

/* FAQ 标签栏 */
.faq-bar {
  padding: 10px 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 输入栏 */
.input-bar {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px;
}

/* 输入框 */
.chat-textarea {
  flex: 1;
}
:deep(.chat-textarea .el-textarea__inner) {
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  border-color: var(--lx-border);
  box-shadow: none;
  transition: border-color 0.2s ease;
}
:deep(.chat-textarea .el-textarea__inner:focus) {
  border-color: var(--lx-primary);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}
:deep(.chat-textarea .el-textarea__inner:disabled) {
  background: var(--lx-bg-muted);
  cursor: not-allowed;
}

/* 操作按钮区 */
.input-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* 转人工图标按钮 */
.transfer-icon-btn {
  color: var(--lx-text-secondary) !important;
  padding: 4px !important;
  font-size: 18px;
  transition: color 0.2s ease;
}
.transfer-icon-btn:hover {
  color: var(--lx-primary) !important;
}

/* 发送按钮 */
.send-btn {
  width: 56px;
  height: 32px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--lx-radius-md);
}

/* 底部快捷键提示 */
.input-hint {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 12px 8px;
  font-size: 11px;
  color: var(--lx-text-disabled);
}
</style>