<template>
  <div class="logistics-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="card-header-left">
        <el-icon class="header-icon"><Van /></el-icon>
        <span class="header-title">物流信息</span>
      </div>
      <el-tag
        :type="getStatusType(cardData.status_text)"
        size="small"
        round
      >
        {{ cardData.status_text || '运输中' }}
      </el-tag>
    </div>

    <!-- 快递公司 + 单号 -->
    <div class="logistics-meta">
      <div class="meta-item">
        <span class="meta-label">快递公司</span>
        <span class="meta-value">
          {{ cardData.logistics_company || '暂未更新' }}
        </span>
      </div>
      <div class="meta-item">
        <span class="meta-label">快递单号</span>
        <div class="meta-value-row">
          <span class="meta-value logistics-no">
            {{ cardData.logistics_no || '暂无单号' }}
          </span>
          <el-button
            v-if="cardData.logistics_no"
            text
            :icon="CopyDocument"
            size="small"
            class="copy-btn"
            @click="copyNo(cardData.logistics_no)"
          />
        </div>
      </div>
      <div class="meta-item" v-if="cardData.order_no">
        <span class="meta-label">关联订单</span>
        <span class="meta-value order-no">
          {{ cardData.order_no }}
        </span>
      </div>
    </div>

    <!-- 物流时间线 -->
    <div class="tracks-wrap" v-if="cardData.tracks?.length">
      <div class="tracks-title">物流轨迹</div>
      <el-timeline class="tracks-timeline">
        <el-timeline-item
          v-for="(track, index) in cardData.tracks"
          :key="index"
          :type="index === 0 ? 'primary' : ''"
          :hollow="index !== 0"
          :timestamp="track.time"
          placement="top"
          :size="index === 0 ? 'large' : 'normal'"
        >
          <div
            class="track-content"
            :class="{ 'track-content--latest': index === 0 }"
          >
            {{ track.content }}
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 暂无物流信息 -->
    <div class="tracks-empty" v-else>
      <el-icon><Clock /></el-icon>
      <span>暂无物流轨迹，请耐心等待</span>
    </div>

    <!-- 卡片底部 -->
    <div class="card-footer" v-if="cardData.order_no">
      <el-button
        text
        type="primary"
        size="small"
        :icon="Document"
        @click="goOrder"
      >
        查看订单详情
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { Van, CopyDocument, Clock, Document } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // card_data 字段内容 [2]
  // {
  //   order_no:           "ORD20260513...",
  //   logistics_no:       "SF1234567890",
  //   logistics_company:  "顺丰速运",
  //   status_text:        "运输中",
  //   tracks: [
  //     { time: "2026-05-13 14:00", content: "运输中，预计明日送达" },
  //     { time: "2026-05-13 12:00", content: "已从深圳发出" }
  //   ]
  // }
  cardData: {
    type:     Object,
    required: true,
    default:  () => ({}),
  },
})

const router = useRouter()

// ── 物流状态 → Tag 颜色 ──
function getStatusType(statusText) {
  if (!statusText) return 'info'
  if (statusText.includes('已签收') || statusText.includes('已送达')) {
    return 'success'
  }
  if (statusText.includes('运输') || statusText.includes('派件')) {
    return 'primary'
  }
  if (statusText.includes('揽件') || statusText.includes('已发出')) {
    return 'warning'
  }
  return 'info'
}

// ── 复制快递单号 ──
async function copyNo(no) {
  try {
    await navigator.clipboard.writeText(no)
    ElMessage.success('快递单号已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// ── 跳转订单详情 ──
async function goOrder() {
  if (!props.cardData.order_no) return
  const target = `/mall/orders?no=${props.cardData.order_no}`
  try {
    await router.push(target)
  } catch {
    window.open(target, '_blank')
  }
}
</script>

<style scoped lang="scss">
.logistics-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  min-width: 280px;
  max-width: 360px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

// 卡片头部
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 10px;
  background: linear-gradient(
    135deg,
    rgba(91, 138, 245, 0.08),
    rgba(91, 138, 245, 0.03)
  );
  border-bottom: 1px solid #f0f2f5;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 7px;
}

.header-icon {
  color: #5b8af5;
  font-size: 18px;
}

.header-title {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
}

// 快递信息
.logistics-meta {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid #f5f7fa;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-label {
  font-size: 12px;
  color: #909399;
  width: 56px;
  flex-shrink: 0;
}

.meta-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.meta-value-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.logistics-no {
  font-family: 'Courier New', monospace;
  color: #5b8af5;
  font-size: 13px;
}

.order-no {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #909399;
}

.copy-btn {
  padding: 2px;
  color: #c0c4cc;

  &:hover {
    color: #5b8af5;
  }
}

// 物流时间线
.tracks-wrap {
  padding: 12px 14px 6px;
}

.tracks-title {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tracks-timeline {
  :deep(.el-timeline-item__timestamp) {
    font-size: 11px;
    color: #c0c4cc;
  }

  :deep(.el-timeline-item__tail) {
    border-left: 2px dashed #e4e7ed;
  }
}

.track-content {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;

  &--latest {
    font-size: 13px;
    color: #303133;
    font-weight: 600;
  }
}

// 暂无物流
.tracks-empty {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 14px;
  font-size: 13px;
  color: #c0c4cc;

  .el-icon {
    font-size: 16px;
  }
}

// 卡片底部
.card-footer {
  padding: 8px 14px 12px;
  border-top: 1px solid #f5f7fa;
}
</style>