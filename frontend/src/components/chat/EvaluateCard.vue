<template>
  <div class="evaluate-card">
    <div class="evaluate-inner">

      <!-- 标题 -->
      <div class="evaluate-title">
        <span class="evaluate-icon">🎉</span>
        <span>问题解决了吗？给我们评个分吧</span>
      </div>

      <!-- 星级评分 -->
      <el-rate
        v-model="rating"
        :texts="rateTexts"
        show-text
        class="evaluate-rate"
      />

      <!-- 快捷评价标签 -->
      <div class="evaluate-tags" v-if="rating > 0">
        <span
          v-for="tag in currentTags"
          :key="tag"
          class="evaluate-tag"
          :class="{ active: selectedTags.includes(tag) }"
          @click="toggleTag(tag)"
        >
          {{ tag }}
        </span>
      </div>

      <!-- 补充说明 -->
      <el-input
        v-if="rating > 0"
        v-model="remark"
        type="textarea"
        :rows="2"
        placeholder="还有什么想说的？（选填）"
        resize="none"
        class="evaluate-remark"
      />

      <!-- 操作按钮 -->
      <div class="evaluate-actions">
        <el-button
          text
          size="small"
          class="skip-btn"
          @click="handleSkip"
        >
          跳过
        </el-button>
        <el-button
          type="primary"
          size="small"
          class="lx-gradient-btn submit-btn"
          :disabled="rating === 0"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交评价
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api/chat'
import { useChatStore } from '@/stores/chat'

const emit = defineEmits(['submitted'])

const chatStore  = useChatStore()
const rating     = ref(0)
const remark     = ref('')
const submitting = ref(false)
const selectedTags = ref([])

const rateTexts = ['非常差', '较差', '一般', '满意', '非常满意']

// 根据评分显示不同的快捷标签
const tagMap = {
  1: ['回复太慢', '问题没解决', '态度不好', '答非所问'],
  2: ['回复太慢', '问题没解决', '答非所问', '需要改进'],
  3: ['基本解决', '还算满意', '有待提升'],
  4: ['回复及时', '问题解决', '态度友好', '很满意'],
  5: ['非常专业', '秒速响应', '完美解决', '强烈推荐'],
}

const currentTags = computed(() => tagMap[rating.value] || [])

// 切换快捷标签选中状态
function toggleTag(tag) {
  const idx = selectedTags.value.indexOf(tag)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

// 提交评价
async function handleSubmit() {
  if (rating.value === 0) return
  if (!chatStore.conversationId) {
    ElMessage.warning('会话信息异常，无法提交评价')
    return
  }

  submitting.value = true
  try {
    await chatApi.evaluate(chatStore.conversationId, {
      rating: rating.value,
      comment: remark.value || undefined,
    })
    ElMessage.success('感谢您的评价 😊')
    emit('submitted')
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 跳过评价
function handleSkip() {
  emit('submitted')
}
</script>

<style scoped>
.evaluate-card {
  border-top: 1px solid var(--lx-border);
  background: #fff;
  flex-shrink: 0;
  padding: 14px 16px;
}
.evaluate-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 标题 */
.evaluate-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--lx-text-primary);
}
.evaluate-icon { font-size: 16px; }

/* 星级 */
.evaluate-rate {
  align-self: flex-start;
}
:deep(.evaluate-rate .el-rate__text) {
  font-size: 13px;
  color: var(--lx-text-secondary);
}

/* 快捷标签 */
.evaluate-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.evaluate-tag {
  padding: 4px 12px;
  border-radius: var(--lx-radius-full);
  font-size: 12px;
  color: var(--lx-text-secondary);
  background: var(--lx-bg-muted);
  border: 1px solid var(--lx-border);
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}
.evaluate-tag:hover {
  color: var(--lx-primary);
  border-color: var(--lx-primary-border);
  background: var(--lx-primary-soft);
}
.evaluate-tag.active {
  color: var(--lx-primary);
  border-color: var(--lx-primary);
  background: var(--lx-primary-soft);
  font-weight: 500;
}

/* 补充说明 */
.evaluate-remark {}
:deep(.evaluate-remark .el-textarea__inner) {
  font-size: 13px;
  border-radius: var(--lx-radius-md);
}

/* 操作按钮 */
.evaluate-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}
.skip-btn {
  font-size: 13px;
  color: var(--lx-text-secondary) !important;
}
.submit-btn {
  height: 32px;
  font-size: 13px;
  font-weight: 600;
  padding: 0 16px;
}
</style>