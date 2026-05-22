<template>
  <div class="message-item" :class="itemClass">

    <!-- 系统消息（居中展示）-->
    <div v-if="isSystem" class="lx-msg-system">
      {{ message.content }}
    </div>

    <!-- 用户消息 -->
    <template v-else-if="isUser">
      <div class="message-bubble user-bubble">
        {{ message.content }}
      </div>
      <div class="message-time">{{ formatTime(message.timestamp) }}</div>
    </template>

    <!-- 客服消息（Bot / Agent / Human）-->
    <template v-else>
      <!-- 头像 -->
      <div class="bot-avatar" :class="botAvatarClass">
        {{ botAvatar }}
      </div>
      <div class="bot-message-wrap">
        <!-- 工具调用状态 -->
        <div
          v-if="message.source === 'tool' && message.intent && !message.content"
          class="lx-tool-running"
          style="margin-bottom: 6px;"
        >
          <el-icon class="is-loading"><Loading /></el-icon>
          {{ toolRunningText }}
        </div>

        <!-- 消息气泡 -->
        <div v-if="message.content" class="message-bubble bot-bubble" v-html="message.content"></div>

        <!-- 单个订单卡片 -->
        <OrderCard
          v-if="message.cardType === 'order' && message.cardData"
          :data="message.cardData"
          @refund="handleRefund"
        />

        <!-- 订单列表卡片 -->
        <OrderListCard
          v-if="message.cardType === 'order_list' && message.cardData"
          :orders="message.cardData"
        />

        <!-- 物流信息卡片 -->
        <LogisticsCard
          v-if="message.cardType === 'logistics' && message.cardData"
          :card-data="message.cardData"
        />

        <!-- 商品卡片 -->
        <ProductCard
          v-if="message.cardType === 'product' && message.cardData"
          :card-data="message.cardData"
        />

        <!-- 商品列表卡片 -->
        <ProductListCard
          v-if="message.cardType === 'product_list' && message.cardData"
          :products="message.cardData"
        />

        <!-- 订单列表卡片（简化版） -->
        <OrdersCard
          v-if="message.cardType === 'orders_list' && message.cardData"
          :orders="message.cardData"
        />

        <!-- 底部元信息 -->
        <div class="message-meta">
          <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          <!-- 来源标签（开发调试用，可配置隐藏）-->
          <span
            v-if="message.source && showSource"
            class="source-tag"
            :style="{ color: sourceColor }"
          >
            {{ sourceText }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatTime } from '@/utils/format'
import { ANSWER_SOURCE } from '@/utils/constants'
import OrderCard from './OrderCard.vue'
import OrderListCard from './OrderListCard.vue'
import LogisticsCard from './LogisticsCard.vue'
import ProductCard from './ProductCard.vue'
import ProductListCard from './ProductListCard.vue'
import OrdersCard from './OrdersCard.vue'

const emit = defineEmits(['apply-refund'])

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
})

// 是否显示来源标签（开发环境显示）
const showSource = import.meta.env.DEV

const isSystem = computed(() => props.message.role === 'system')
const isUser   = computed(() => props.message.role === 'user')
const isBot    = computed(() => ['bot', 'agent'].includes(props.message.role))

const itemClass = computed(() => ({
  'item-system': isSystem.value,
  'item-user':   isUser.value,
  'item-bot':    isBot.value || props.message.role === 'human',
}))

// 客服头像
const botAvatar = computed(() => {
  const role = props.message.role
  if (role === 'agent') return '✨'
  if (role === 'human') return '👤'
  return '🤖'
})

const botAvatarClass = computed(() => {
  const role = props.message.role
  if (role === 'agent') return 'avatar-agent'
  if (role === 'human') return 'avatar-human'
  return 'avatar-bot'
})

// 工具调用文案
const toolRunningText = computed(() => {
  const intentMap = {
    refund_request:  '正在查询退款信息...',
    logistics_query: '正在查询物流状态...',
    order_query:     '正在查询订单信息...',
    product_query:   '正在查找相关商品...',
  }
  return intentMap[props.message.intent] || '正在处理中...'
})

// 来源标签
const sourceInfo = computed(() => ANSWER_SOURCE[props.message.source] || null)
const sourceText  = computed(() => sourceInfo.value?.text  || '')
const sourceColor = computed(() => sourceInfo.value?.color || '#909399')

async function handleRefund(orderNo) {
  try {
    await ElMessageBox.confirm(
      `确定要为订单 ${orderNo} 申请退款？`,
      '申请退款',
      { confirmButtonText: '确认申请', cancelButtonText: '取消', type: 'warning' }
    )
    const { value: reason } = await ElMessageBox.prompt(
      '请填写退款原因（必填）',
      '退款申请',
      {
        confirmButtonText: '提交申请',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：商品质量问题、不想要了...',
        inputValidator: (val) => (val && val.trim() ? true : '请填写退款原因'),
      }
    )
    emit('apply-refund', { orderNo, reason: reason.trim() })
  } catch {
    // 用户取消不处理
  }
}
</script>

<style scoped>
.message-item {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

/* 系统消息 */
.item-system {
  justify-content: center;
}

/* 用户消息：右对齐 */
.item-user {
  flex-direction: column;
  align-items: flex-end;
}

/* 客服消息：左对齐 */
.item-bot {
  flex-direction: row;
  align-items: flex-start;
}

/* 头像 */
.bot-avatar {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 2px;
}
.avatar-bot   { background: #eff6ff; border: 1px solid #bfdbfe; }
.avatar-agent { background: #f3e8ff; border: 1px solid #ddd6fe; }
.avatar-human { background: #dcfce7; border: 1px solid #bbf7d0; }

/* 消息气泡 */
.message-bubble {
  max-width: 240px;
  padding: 10px 13px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 用户气泡 */
.user-bubble {
  background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
  color: #fff;
  border-radius: 16px 16px 4px 16px;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

/* 客服气泡 */
.bot-bubble {
  background: #fff;
  color: var(--lx-text-regular);
  border: 1px solid var(--lx-border);
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.bot-message-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 时间和来源 */
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px;
}
.message-time {
  font-size: 11px;
  color: var(--lx-text-placeholder);
}
.source-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--lx-bg-muted);
}
</style>