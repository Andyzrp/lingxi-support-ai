<template>
  <div class="channel-config">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="$router.back()">
          返回渠道列表
        </el-button>
        <h2 class="page-title">渠道内容配置</h2>
        <el-tag type="info" size="small">{{ channelName }}</el-tag>
      </div>
      <el-button type="primary" :loading="saving" @click="handleSave">
        保存配置
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 左侧配置区 -->
      <el-col :span="14">

        <!-- 热点问题 -->
        <div class="config-card">
          <div class="config-card-header">
            <div class="config-card-title">
              <el-icon><ChatDotRound /></el-icon>
              猜您想问
            </div>
            <div class="config-card-actions">
              <el-switch v-model="config.hot_questions_enabled" />
              <el-button
                type="primary"
                plain
                size="small"
                :icon="Plus"
                @click="addItem('hot_questions')"
                :disabled="!config.hot_questions_enabled || config.hot_questions.length >= 8"
              >
                添加 ({{ config.hot_questions.length }}/8)
              </el-button>
            </div>
          </div>
          <div class="config-card-body" v-if="config.hot_questions_enabled">
            <div class="hint-text">💡 用户打开对话窗口时展示，点击后自动发送该问题</div>
            <div
              v-for="(item, index) in config.hot_questions"
              :key="item.id || index"
              class="item-row"
            >
              <span class="item-index">{{ index + 1 }}</span>
              <el-input
                v-model="item.text"
                placeholder="请输入热点问题，如：如何申请退款？"
                maxlength="30"
                show-word-limit
                clearable
              />
              <el-button type="danger" text :icon="Delete" @click="removeItem('hot_questions', index)" />
            </div>
            <el-empty v-if="!config.hot_questions.length" description="暂无热点问题" :image-size="60" />
          </div>
        </div>

        <!-- Banner -->
        <div class="config-card">
          <div class="config-card-header">
            <div class="config-card-title">
              <el-icon><Picture /></el-icon>
              活动 Banner
            </div>
            <div class="config-card-actions">
              <el-switch v-model="config.banners_enabled" />
              <el-button
                type="primary"
                plain
                size="small"
                :icon="Plus"
                @click="addItem('banners')"
                :disabled="!config.banners_enabled || config.banners.length >= 5"
              >
                添加 ({{ config.banners.length }}/5)
              </el-button>
            </div>
          </div>
          <div class="config-card-body" v-if="config.banners_enabled">
            <div class="hint-text">💡 展示在热点问题下方，支持图片 + 标题 + 跳转链接</div>
            <div
              v-for="(item, index) in config.banners"
              :key="item.id || index"
              class="banner-row"
            >
              <div class="banner-preview">
                <el-image v-if="item.image_url" :src="item.image_url" fit="cover" class="banner-img" />
                <div v-else class="banner-img-placeholder">
                  <el-icon><Picture /></el-icon>
                </div>
              </div>
              <div class="banner-fields">
                <el-input v-model="item.image_url" placeholder="图片链接" size="small" clearable />
                <el-input v-model="item.title" placeholder="Banner 标题" maxlength="20" show-word-limit size="small" clearable />
                <el-input v-model="item.content" placeholder="副标题" maxlength="30" show-word-limit size="small" clearable />
                <el-input v-model="item.link_url" placeholder="点击跳转链接（留空则不跳转）" size="small" clearable />
              </div>
              <el-button type="danger" text :icon="Delete" @click="removeItem('banners', index)" />
            </div>
            <el-empty v-if="!config.banners.length" description="暂无 Banner" :image-size="60" />
          </div>
        </div>

        <!-- 快捷标签 -->
        <div class="config-card">
          <div class="config-card-header">
            <div class="config-card-title">
              <el-icon><Lightning /></el-icon>
              快捷标签
            </div>
            <div class="config-card-actions">
              <el-switch v-model="config.quick_tags_enabled" />
              <el-button
                type="primary"
                plain
                size="small"
                :icon="Plus"
                @click="addItem('quick_tags')"
                :disabled="!config.quick_tags_enabled || config.quick_tags.length >= 10"
              >
                添加 ({{ config.quick_tags.length }}/10)
              </el-button>
            </div>
          </div>
          <div class="config-card-body" v-if="config.quick_tags_enabled">
            <div class="hint-text">💡 展示在输入框上方，点击后自动发送对应内容</div>
            <div
              v-for="(item, index) in config.quick_tags"
              :key="item.id || index"
              class="tag-row"
            >
              <el-input v-model="item.icon" placeholder="🔥" maxlength="2" style="width: 60px" size="small" />
              <el-input v-model="item.label" placeholder="标签文字" maxlength="10" show-word-limit size="small" style="flex:1" clearable />
              <el-input v-model="item.content" placeholder="点击后发送内容（留空则发送标签文字）" maxlength="50" size="small" style="flex:2" clearable />
              <el-button type="danger" text :icon="Delete" @click="removeItem('quick_tags', index)" />
            </div>
            <el-empty v-if="!config.quick_tags.length" description="暂无快捷标签" :image-size="60" />
          </div>
        </div>

      </el-col>

      <!-- 右侧预览 -->
      <el-col :span="10">
        <div class="preview-wrap">
          <div class="preview-title">实时预览</div>
          <div class="phone-frame">
            <div class="phone-screen">
              <div class="preview-header">
                <img :src="BOT_AVATAR_IMG" class="preview-logo" />
                <div>
                  <div class="preview-name">灵犀智能客服</div>
                  <div class="preview-status">● 在线</div>
                </div>
              </div>
              <div class="preview-messages">
                <div class="preview-welcome">
                  <img :src="BOT_AVATAR_IMG" class="preview-avatar" />
                  <div class="preview-bubble">您好！我是灵犀智能客服，请问有什么可以帮助您？</div>
                </div>
                <!-- 热点问题预览 -->
                <div class="preview-section" v-if="config.hot_questions_enabled && config.hot_questions.length">
                  <div class="preview-section-title">猜您想问</div>
                  <div
                    v-for="(q, i) in config.hot_questions.slice(0, 4)"
                    :key="i"
                    class="preview-question-item"
                  >
                    {{ q.text || `热点问题 ${i + 1}` }}
                  </div>
                </div>
                <!-- Banner 预览 -->
                <div class="preview-section" v-if="config.banners_enabled && config.banners.length">
                  <div
                    v-for="(b, i) in config.banners.slice(0, 2)"
                    :key="i"
                    class="preview-banner-item"
                  >
                    <div class="preview-banner-img">
                      <el-image v-if="b.image_url" :src="b.image_url" fit="cover" style="width:100%;height:100%" />
                      <div v-else class="preview-banner-placeholder"><el-icon><Picture /></el-icon></div>
                    </div>
                    <div class="preview-banner-info">
                      <div class="preview-banner-title">{{ b.title || 'Banner 标题' }}</div>
                      <div class="preview-banner-sub">{{ b.content || '副标题' }}</div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 快捷标签预览 -->
              <div class="preview-quick-tags" v-if="config.quick_tags_enabled && config.quick_tags.length">
                <div v-for="(t, i) in config.quick_tags.slice(0, 5)" :key="i" class="preview-tag">
                  <span v-if="t.icon">{{ t.icon }}</span>
                  {{ t.label || `标签${i+1}` }}
                </div>
              </div>
              <div class="preview-input-bar">
                <div class="preview-input">请输入您的问题...</div>
                <div class="preview-send-btn">发送</div>
              </div>
            </div>
          </div>
          <div class="preview-hint">预览效果仅供参考，实际显示以前端渲染为准</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, ChatDotRound, Picture, Plus,
  Delete, Lightning,
} from '@element-plus/icons-vue'
import { channelApi } from '@/api/admin'

const route  = useRoute()
const router = useRouter()

const channelId   = ref(Number(route.params.id))
const channelName = ref('')
const saving      = ref(false)

const BOT_AVATAR_IMG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><circle cx="20" cy="20" r="20" fill="%2367c23a"/><rect x="11" y="14" width="18" height="14" rx="4" fill="white" opacity="0.95"/><circle cx="16" cy="20" r="2.5" fill="%2367c23a"/><circle cx="24" cy="20" r="2.5" fill="%2367c23a"/><rect x="15" y="25" width="10" height="2" rx="1" fill="%2367c23a"/></svg>`

const config = ref({
  hot_questions_enabled: true,
  hot_questions: [],
  banners_enabled: true,
  banners: [],
  quick_tags_enabled: true,
  quick_tags: [],
})

function addItem(type) {
  if (type === 'hot_questions') {
    config.value.hot_questions.push({ id: Date.now(), text: '' })
  } else if (type === 'banners') {
    config.value.banners.push({ id: Date.now(), image_url: '', title: '', content: '', link_url: '' })
  } else if (type === 'quick_tags') {
    config.value.quick_tags.push({ id: Date.now(), icon: '', label: '', content: '' })
  }
}

function removeItem(type, index) {
  config.value[type].splice(index, 1)
}

async function handleSave() {
  saving.value = true
  try {
    await channelApi.saveConfig(channelId.value, config.value)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function loadConfig() {
  try {
    const res = await channelApi.getConfig(channelId.value)
    if (res.data) {
      Object.assign(config.value, res.data)
    }
    channelName.value = res.data?.channel_name || `渠道 ${channelId.value}`
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载配置失败')
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped lang="scss">
.channel-config {
  min-height: 100%;
  background: #f5f7fa;
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  background: #fff;
  padding: 16px 20px;
  border-radius: 12px;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.config-card {
  background: #fff;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.config-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #f5f7fa;
  background: #fafafa;
}

.config-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  .el-icon { color: #5b8af5; }
}

.config-card-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-card-body {
  padding: 16px 18px;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
  &:last-child { border-bottom: none; }
}

.item-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #5b8af5;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f7fa;
  &:last-child { border-bottom: none; }
}

.banner-preview { flex-shrink: 0; }

.banner-img {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
}

.banner-img-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px dashed #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.banner-fields {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
  &:last-child { border-bottom: none; }
}

// 预览
.preview-wrap {
  position: sticky;
  top: 20px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-align: center;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.phone-frame {
  width: 280px;
  margin: 0 auto;
  background: #1a1a2e;
  border-radius: 36px;
  padding: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.phone-screen {
  background: #f5f7fa;
  border-radius: 28px;
  overflow: hidden;
  height: 520px;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #5b8af5, #7c3aed);
}

.preview-logo {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.preview-name {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.preview-status {
  font-size: 10px;
  color: rgba(255,255,255,0.8);
}

.preview-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.preview-welcome {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 10px;
}

.preview-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
}

.preview-bubble {
  background: #fff;
  border-radius: 2px 8px 8px 8px;
  padding: 6px 8px;
  font-size: 11px;
  color: #303133;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.preview-section {
  background: #fff;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.preview-section-title {
  font-size: 11px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 6px;
}

.preview-question-item {
  font-size: 11px;
  color: #5b8af5;
  padding: 5px 0;
  border-bottom: 1px solid #f5f7fa;
  &:last-child { border-bottom: none; padding-bottom: 0; }
}

.preview-banner-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.preview-banner-img {
  width: 50px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  flex-shrink: 0;
}

.preview-banner-title {
  font-size: 11px;
  font-weight: 600;
  color: #303133;
}

.preview-banner-sub {
  font-size: 10px;
  color: #909399;
}

.preview-quick-tags {
  display: flex;
  gap: 4px;
  padding: 6px 10px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  overflow-x: auto;
  flex-shrink: 0;
  &::-webkit-scrollbar { display: none; }
}

.preview-tag {
  font-size: 10px;
  color: #5b8af5;
  background: rgba(91,138,245,0.1);
  border: 1px solid rgba(91,138,245,0.2);
  border-radius: 10px;
  padding: 3px 8px;
  white-space: nowrap;
  flex-shrink: 0;
}

.preview-input-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.preview-input {
  flex: 1;
  height: 28px;
  background: #f5f7fa;
  border-radius: 14px;
  font-size: 10px;
  color: #c0c4cc;
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.preview-send-btn {
  height: 28px;
  padding: 0 10px;
  background: #5b8af5;
  color: #fff;
  border-radius: 14px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-hint {
  text-align: center;
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 12px;
}
</style>
