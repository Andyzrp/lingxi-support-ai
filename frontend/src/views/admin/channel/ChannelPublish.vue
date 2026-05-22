<template>
  <el-dialog
    v-model="visible"
    title="渠道发布 / 接入"
    width="620px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <!-- 渠道信息 -->
    <div class="publish-channel-info" v-if="channel">
      <el-icon><Link /></el-icon>
      <span class="channel-name">{{ channel.name }}</span>
      <el-tag size="small" type="success">已发布</el-tag>
    </div>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="publish-tabs">

      <!-- ==================== Tab 1：独立页面 ==================== -->
      <el-tab-pane label="独立页面" name="standalone">
        <div class="tab-desc">
          用户直接访问链接即可开始对话，适合微信/邮件/二维码分发
        </div>

        <!-- 完整链接 -->
        <div class="code-block-label">对话链接</div>
        <div class="code-block">
          <code class="code-text">{{ standaloneUrl }}</code>
          <el-button
            text
            :icon="CopyDocument"
            size="small"
            @click="copy(standaloneUrl, '链接已复制')"
          />
        </div>

        <!-- 二维码 -->
        <div class="qrcode-wrap">
          <div class="qrcode-box" ref="qrcodeRef"></div>
          <div class="qrcode-hint">扫码体验对话</div>
        </div>

        <!-- 操作按钮 -->
        <div class="tab-actions">
          <el-button
            type="primary"
            :icon="ChromeFilled"
            @click="openUrl(standaloneUrl)"
          >
            打开测试
          </el-button>
          <el-button
            :icon="CopyDocument"
            @click="copy(standaloneUrl, '链接已复制')"
          >
            复制链接
          </el-button>
        </div>
      </el-tab-pane>

      <!-- ==================== Tab 2：iframe 嵌入 ==================== -->
      <el-tab-pane label="iframe 嵌入" name="iframe">
        <div class="tab-desc">
          将以下代码粘贴到您网站的 HTML 中，即可嵌入客服窗口
        </div>

        <!-- 尺寸配置 -->
        <div class="iframe-size-row">
          <span class="size-label">窗口尺寸</span>
          <el-input-number
            v-model="iframeWidth"
            :min="320"
            :max="1200"
            size="small"
            style="width: 120px"
          />
          <span class="size-x">×</span>
          <el-input-number
            v-model="iframeHeight"
            :min="400"
            :max="900"
            size="small"
            style="width: 120px"
          />
          <span class="size-unit">px</span>
        </div>

        <!-- iframe 代码 -->
        <div class="code-block-label">嵌入代码</div>
        <div class="code-block code-block--multi">
          <pre class="code-pre">{{ iframeCode }}</pre>
          <el-button
            text
            :icon="CopyDocument"
            size="small"
            class="copy-btn-top"
            @click="copy(iframeCode, 'iframe 代码已复制')"
          />
        </div>

        <!-- 使用说明 -->
        <el-alert type="info" :closable="false" style="margin-top: 12px">
          <template #default>
            将以上代码粘贴到您网页 <code>&lt;body&gt;</code> 内任意位置即可
          </template>
        </el-alert>
      </el-tab-pane>

      <!-- ==================== Tab 3：JS 挂件 ==================== -->
      <el-tab-pane label="JS 挂件" name="widget">
        <div class="tab-desc">
          一行代码接入，自动在页面右下角显示悬浮客服按钮（推荐）
        </div>

        <!-- 挂件配置 -->
        <div class="widget-config">
          <div class="config-row">
            <span class="config-label">主题色</span>
            <el-color-picker
              v-model="widgetColor"
              size="small"
              :predefine="['#5b8af5', '#1a1a1a', '#67c23a', '#e6a23c', '#f56c6c']"
            />
            <span class="config-value">{{ widgetColor }}</span>
          </div>
          <div class="config-row">
            <span class="config-label">按钮位置</span>
            <el-radio-group v-model="widgetPosition" size="small">
              <el-radio-button label="right">右下角</el-radio-button>
              <el-radio-button label="left">左下角</el-radio-button>
            </el-radio-group>
          </div>
          <div class="config-row">
            <span class="config-label">按钮文字</span>
            <el-input
              v-model="widgetText"
              size="small"
              maxlength="6"
              show-word-limit
              style="width: 150px"
            />
          </div>
        </div>

        <!-- script 代码 -->
        <div class="code-block-label">接入代码（粘贴到网页 &lt;/body&gt; 前）</div>
        <div class="code-block code-block--multi">
          <pre class="code-pre">{{ widgetCode }}</pre>
          <el-button
            text
            :icon="CopyDocument"
            size="small"
            class="copy-btn-top"
            @click="copy(widgetCode, 'JS 挂件代码已复制')"
          />
        </div>

        <!-- 效果预览 -->
        <div class="widget-preview">
          <div class="widget-preview-label">按钮预览</div>
          <div class="widget-preview-btn" :style="{ background: widgetColor }">
            <el-icon><ChatDotRound /></el-icon>
            {{ widgetText }}
          </div>
        </div>

        <el-alert type="warning" :closable="false" style="margin-top: 12px">
          <template #default>
            ⚠️ JS 挂件需要先部署前端到公网，开发环境仅供预览代码
          </template>
        </el-alert>
      </el-tab-pane>

    </el-tabs>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Link, CopyDocument, ChromeFilled, ChatDotRound,
} from '@element-plus/icons-vue'

// ==================== Props / Emits ====================
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  channel:    { type: Object,  default: null  },
})
const emit = defineEmits(['update:modelValue'])

// ==================== 弹窗控制 ====================
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function handleClosed() {
  activeTab.value = 'standalone'
}

// ==================== Tab ====================
const activeTab = ref('standalone')

// ==================== 基础 URL ====================
const BASE_URL = window.location.origin

const channelToken = computed(
  () => props.channel?.channel_token || ''
)

// ==================== Tab 1：独立页面 ====================
const standaloneUrl = computed(
  () => `${BASE_URL}/chat?channel=${channelToken.value}`
)

const qrcodeRef = ref(null)

watch([() => props.modelValue, standaloneUrl], async ([show]) => {
  if (!show) return
  await nextTick()
  if (!qrcodeRef.value) return
  qrcodeRef.value.innerHTML =
    `<div style="color:#c0c4cc;font-size:12px;padding:20px;text-align:center">
      二维码功能<br/>
      <span style="font-size:11px">生产环境可用</span>
    </div>`
})

// ==================== Tab 2：iframe 嵌入 ====================
const iframeWidth  = ref(380)
const iframeHeight = ref(600)

const iframeCode = computed(() => `<iframe
  src="${standaloneUrl.value}"
  width="${iframeWidth.value}"
  height="${iframeHeight.value}"
  frameborder="0"
  allow="microphone"
  style="border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.15)">
</iframe>`)

// ==================== Tab 3：JS 挂件 ====================
const widgetColor    = ref('#5b8af5')
const widgetPosition = ref('right')
const widgetText     = ref('联系客服')

const widgetCode = computed(() => `<script
  src="${BASE_URL}/widget.js"
  data-channel="${channelToken.value}"
  data-color="${widgetColor.value}"
  data-position="${widgetPosition.value}"
  data-text="${widgetText.value}">
<\/script>`)

// ==================== 工具函数 ====================
async function copy(text, msg = '已复制') {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(msg)
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

function openUrl(url) {
  window.open(url, '_blank')
}
</script>

<style scoped lang="scss">
.publish-channel-info {
  display:       flex;
  align-items:   center;
  gap:           8px;
  padding:       10px 14px;
  background:    #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size:     13px;

  .el-icon { color: #5b8af5; font-size: 16px; }
}

.channel-name {
  font-weight: 600;
  color:       #303133;
  flex:        1;
}

.tab-desc {
  font-size:     13px;
  color:         #909399;
  margin-bottom: 14px;
  padding:       8px 10px;
  background:    #f5f7fa;
  border-radius: 6px;
}

.code-block-label {
  font-size:     12px;
  color:         #606266;
  font-weight:   500;
  margin-bottom: 6px;
  margin-top:    12px;
}

.code-block {
  display:       flex;
  align-items:   center;
  gap:           8px;
  background:    #1a1a2e;
  border-radius: 8px;
  padding:       10px 14px;
  position:      relative;

  &--multi {
    align-items: flex-start;
  }
}

.code-text {
  flex:        1;
  font-size:   12px;
  color:       #67c23a;
  font-family: 'Courier New', monospace;
  word-break:  break-all;
}

.code-pre {
  flex:        1;
  font-size:   11px;
  color:       #67c23a;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break:  break-all;
  margin:      0;
  line-height: 1.6;
}

.copy-btn-top {
  position:   absolute;
  top:        8px;
  right:      8px;
  color:      #909399;

  &:hover { color: #ffffff; }
}

.qrcode-wrap {
  display:        flex;
  flex-direction: column;
  align-items:    center;
  padding:        16px 0;
  gap:            8px;
}

.qrcode-box {
  background:    #ffffff;
  border-radius: 8px;
  padding:       8px;
  display:       inline-block;
  box-shadow:    0 2px 8px rgba(0, 0, 0, 0.1);
}

.qrcode-hint {
  font-size: 12px;
  color:     #909399;
}

.tab-actions {
  display:    flex;
  gap:        10px;
  margin-top: 14px;
}

.iframe-size-row {
  display:     flex;
  align-items: center;
  gap:         10px;
  margin-bottom: 4px;
  font-size:   13px;
}

.size-label {
  color:      #606266;
  flex-shrink: 0;
}

.size-x, .size-unit {
  color:      #909399;
  font-size:  12px;
}

.widget-config {
  background:    #f5f7fa;
  border-radius: 8px;
  padding:       12px 14px;
  margin-bottom: 12px;
  display:       flex;
  flex-direction: column;
  gap:           10px;
}

.config-row {
  display:     flex;
  align-items: center;
  gap:         12px;
}

.config-label {
  font-size:   12px;
  color:       #606266;
  width:       60px;
  flex-shrink: 0;
}

.config-value {
  font-size:   12px;
  color:       #909399;
}

.widget-preview {
  display:        flex;
  flex-direction: column;
  align-items:    flex-end;
  gap:            6px;
  margin-top:     12px;
}

.widget-preview-label {
  font-size: 12px;
  color:     #909399;
}

.widget-preview-btn {
  display:       flex;
  align-items:   center;
  gap:           6px;
  padding:       10px 16px;
  border-radius: 24px;
  color:         #ffffff;
  font-size:     13px;
  font-weight:   600;
  box-shadow:    0 4px 12px rgba(0, 0, 0, 0.15);
  cursor:        pointer;

  .el-icon { font-size: 16px; }
}

.publish-tabs {
  :deep(.el-tabs__item) {
    font-size: 13px;
  }
}
</style>
