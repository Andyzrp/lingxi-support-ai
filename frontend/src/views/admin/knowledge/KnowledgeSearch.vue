<template>
  <div class="knowledge-search">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
        <el-divider direction="vertical" />
        <div>
          <h2 class="page-title">检索效果测试</h2>
          <span class="page-sub">{{ kbName || '知识库' }}</span>
        </div>
      </div>
      <el-button :icon="List" @click="goItems">查看条目列表</el-button>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：检索输入区 + 结果 -->
      <el-col :span="16">

        <!-- 检索输入框 -->
        <div class="search-card">
          <div class="search-input-wrap">
            <el-input
              v-model="query"
              placeholder="请输入测试问题，如：我要退款怎么操作？"
              size="large"
              clearable
              :prefix-icon="Search"
              @keyup.enter="handleSearch"
            />
            <el-button
              type="primary"
              size="large"
              :loading="searching"
              :icon="Search"
              @click="handleSearch"
            >
              {{ searching ? '检索中...' : '开始检索' }}
            </el-button>
          </div>

          <!-- 快速测试标签 -->
          <div class="quick-tags">
            <span class="quick-label">快速测试：</span>
            <el-tag
              v-for="tag in quickTags"
              :key="tag"
              class="quick-tag"
              type="info"
              size="small"
              effect="plain"
              @click="useQuickTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <!-- 检索结果 -->
        <div class="results-area" v-loading="searching">

          <!-- 结果统计头 -->
          <div class="results-header" v-if="hasSearched">
            <div class="results-meta">
              <template v-if="results.length">
                <span class="results-count">
                  找到 <strong>{{ results.length }}</strong> 条相关知识
                </span>
                <el-divider direction="vertical" />
                <span class="results-time">
                  耗时 <strong>{{ elapsedMs }}</strong> ms
                </span>
                <el-divider direction="vertical" />
                <span class="results-query">
                  查询：<em>「{{ lastQuery }}」</em>
                </span>
              </template>
              <template v-else>
                <el-icon class="no-result-icon"><WarningFilled /></el-icon>
                <span>未找到匹配结果，建议降低相似度阈值或补充知识条目</span>
              </template>
            </div>

            <!-- 视图切换 -->
            <el-radio-group v-model="viewMode" size="small" v-if="results.length">
              <el-radio-button value="card">卡片视图</el-radio-button>
              <el-radio-button value="table">表格视图</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 卡片视图 -->
          <div v-if="hasSearched && results.length && viewMode === 'card'" class="results-cards">
            <div
              v-for="(item, index) in results"
              :key="item.id"
              class="result-card"
              :class="getScoreClass(item.score)"
            >
              <!-- 排名 + 分数 -->
              <div class="result-rank-wrap">
                <div class="result-rank">{{ index + 1 }}</div>
                <div class="result-score-wrap">
                  <el-progress
                    :percentage="Math.round(item.score * 100)"
                    :color="getScoreColor(item.score)"
                    :stroke-width="8"
                    :show-text="false"
                    style="width: 80px"
                  />
                  <span class="result-score" :style="{ color: getScoreColor(item.score) }">
                    {{ item.score.toFixed(4) }}
                  </span>
                </div>
              </div>

              <!-- 内容 -->
              <div class="result-content">
                <div class="result-header">
                  <span class="result-title">{{ item.title }}</span>
                  <div class="result-badges">
                    <el-tag size="small" :type="getSourceType(item.source)">
                      {{ getSourceLabel(item.source) }}
                    </el-tag>
                    <el-tag v-if="item.category" size="small" type="info">
                      {{ item.category }}
                    </el-tag>
                    <el-tag
                      :type="item.score >= searchParams.threshold ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ item.score >= searchParams.threshold ? '✓ 达到阈值' : '✗ 未达阈值' }}
                    </el-tag>
                  </div>
                </div>

                <div class="result-answer">{{ item.content }}</div>

                <!-- 相似问法 -->
                <div class="result-similar" v-if="item.similar_questions?.length">
                  <span class="similar-label">相似问法：</span>
                  <span
                    v-for="q in item.similar_questions.slice(0, 3)"
                    :key="q"
                    class="similar-q"
                  >
                    {{ q }}
                  </span>
                </div>
              </div>

              <!-- 操作 -->
              <div class="result-actions">
                <el-button
                  text
                  type="primary"
                  size="small"
                  :icon="Edit"
                  @click="goEditItem(item)"
                >
                  编辑
                </el-button>
              </div>
            </div>
          </div>

          <!-- 表格视图 -->
          <div v-if="hasSearched && results.length && viewMode === 'table'" class="results-table">
            <el-table :data="results" border stripe>
              <el-table-column label="排名" type="index" width="60" align="center" />
              <el-table-column label="相似度" width="140" align="center">
                <template #default="{ row }">
                  <div class="score-cell">
                    <span class="score-num" :style="{ color: getScoreColor(row.score) }">
                      {{ row.score.toFixed(4) }}
                    </span>
                    <el-tag
                      size="small"
                      :type="row.score >= searchParams.threshold ? 'success' : 'warning'"
                    >
                      {{ row.score >= searchParams.threshold ? '达标' : '未达' }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="知识标题" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="table-title">{{ row.title }}</span>
                </template>
              </el-table-column>
              <el-table-column label="分类" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.category" size="small" type="info">{{ row.category }}</el-tag>
                  <span v-else class="text-gray">—</span>
                </template>
              </el-table-column>
              <el-table-column label="来源" width="100" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="getSourceType(row.source)">
                    {{ getSourceLabel(row.source) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="答案预览" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="text-gray answer-preview">{{ row.content }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="goEditItem(row)">
                    编辑
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 未搜索初始状态 -->
          <div v-if="!hasSearched" class="empty-state">
            <el-icon :size="64" class="empty-icon"><Search /></el-icon>
            <div class="empty-title">输入问题开始检索测试</div>
            <div class="empty-desc">
              测试知识库的检索效果，验证相似度阈值是否合理
            </div>
          </div>

          <!-- 无结果状态 -->
          <el-empty
            v-if="hasSearched && !searching && !results.length"
            description="未找到匹配的知识条目"
            :image-size="80"
          >
            <el-button type="primary" @click="lowerThreshold">
              降低阈值重试（当前 {{ searchParams.threshold }}）
            </el-button>
          </el-empty>
        </div>
      </el-col>

      <!-- 右侧：参数配置 + 历史记录 -->
      <el-col :span="8">

        <!-- 检索参数配置 -->
        <div class="param-card">
          <div class="param-title">
            <el-icon><Setting /></el-icon>
            检索参数配置
          </div>

          <div class="param-item">
            <div class="param-label">
              返回条数（top_k）
              <el-tooltip content="最多返回多少条匹配结果" placement="top">
                <el-icon class="param-tip"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
            <el-slider
              v-model="searchParams.top_k"
              :min="1"
              :max="20"
              :step="1"
              show-input
              size="small"
              :input-size="'small'"
            />
          </div>

          <div class="param-item">
            <div class="param-label">
              相似度阈值（threshold）
              <el-tooltip content="只返回相似度高于此值的结果，越高越严格" placement="top">
                <el-icon class="param-tip"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
            <el-slider
              v-model="searchParams.threshold"
              :min="0.5"
              :max="1.0"
              :step="0.01"
              show-input
              size="small"
              :input-size="'small'"
            />
            <div class="threshold-tips">
              <span :class="getThresholdLabel(searchParams.threshold).class">
                {{ getThresholdLabel(searchParams.threshold).text }}
              </span>
            </div>
          </div>

          <!-- 阈值参考线 -->
          <div class="threshold-ref">
            <div class="threshold-ref-title">阈值参考：</div>
            <div class="threshold-ref-items">
              <div class="threshold-ref-item">
                <span class="ref-dot dot-strict"></span>
                <span>≥ 0.90 严格</span>
              </div>
              <div class="threshold-ref-item">
                <span class="ref-dot dot-normal"></span>
                <span>0.80 ~ 0.90 推荐</span>
              </div>
              <div class="threshold-ref-item">
                <span class="ref-dot dot-loose"></span>
                <span>≤ 0.75 宽松</span>
              </div>
            </div>
          </div>

          <el-button
            type="primary"
            plain
            style="width: 100%; margin-top: 8px"
            @click="handleSearch"
            :disabled="!query"
          >
            用当前参数重新检索
          </el-button>

          <el-button
            style="width: 100%; margin-top: 8px"
            @click="resetParams"
          >
            重置默认参数
          </el-button>
        </div>

        <!-- 检索历史 -->
        <div class="history-card">
          <div class="history-title">
            <el-icon><Clock /></el-icon>
            检索历史
            <el-button
              v-if="searchHistory.length"
              text
              size="small"
              type="danger"
              style="margin-left: auto"
              @click="clearHistory"
            >
              清空
            </el-button>
          </div>

          <div v-if="searchHistory.length" class="history-list">
            <div
              v-for="(record, index) in searchHistory"
              :key="index"
              class="history-item"
              @click="useHistory(record)"
            >
              <div class="history-item-left">
                <el-icon class="history-q-icon"><ChatLineRound /></el-icon>
                <span class="history-query">{{ record.query }}</span>
              </div>
              <div class="history-item-right">
                <span class="history-count">{{ record.count }} 条</span>
                <span class="history-ms">{{ record.ms }} ms</span>
              </div>
            </div>
          </div>

          <el-empty
            v-else
            description="暂无检索历史"
            :image-size="50"
          />
        </div>

        <!-- 使用说明 -->
        <div class="tips-card">
          <div class="tips-title">
            <el-icon><InfoFilled /></el-icon>
            检索说明
          </div>
          <ul class="tips-list">
            <li>
              检索采用 <strong>BM25（0.3）+ Embedding（0.7）</strong>
              混合检索策略 [1]
            </li>
            <li>相似度分数越接近 1.0，表示匹配度越高</li>
            <li>
              Bot 默认阈值为 <strong>0.85</strong>，低于此值不会触发 FAQ 拦截
            </li>
            <li>绿色表示达到阈值，会被 Bot 直接回复；黄色表示未达到阈值</li>
            <li>若多数问题未达阈值，建议补充相似问法或降低阈值</li>
          </ul>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Search,
  List,
  Edit,
  Setting,
  QuestionFilled,
  Clock,
  ChatLineRound,
  InfoFilled,
  WarningFilled,
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/admin'

const route  = useRoute()
const router = useRouter()

const kbId   = computed(() => Number(route.params.id))
const kbName = ref('')

// ==================== 检索参数 ====================
const DEFAULT_PARAMS = { top_k: 5, threshold: 0.85 }

const searchParams = ref({ ...DEFAULT_PARAMS })

function resetParams() {
  searchParams.value = { ...DEFAULT_PARAMS }
  ElMessage.info('已重置为默认参数')
}

function lowerThreshold() {
  const newVal = Math.max(0.5, Number((searchParams.value.threshold - 0.05).toFixed(2)))
  searchParams.value.threshold = newVal
  handleSearch()
}

// 阈值状态标签
function getThresholdLabel(val) {
  if (val >= 0.90) return { text: '严格模式：精确匹配，召回率低', class: 'tip-strict' }
  if (val >= 0.80) return { text: '推荐模式：平衡精确与召回', class: 'tip-normal' }
  return { text: '宽松模式：召回率高，可能有噪声', class: 'tip-loose' }
}

// ==================== 快速测试标签 ====================
const quickTags = [
  '我要退款怎么操作',
  '物流还没到怎么办',
  '订单能取消吗',
  '商品有质量问题',
  '发票怎么开',
  '如何修改收货地址',
]

function useQuickTag(tag) {
  query.value = tag
  handleSearch()
}

// ==================== 检索 ====================
const query     = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const results   = ref([])
const elapsedMs = ref(0)
const lastQuery = ref('')
const viewMode  = ref('card')

async function handleSearch() {
  const q = query.value.trim()
  if (!q) {
    ElMessage.warning('请输入检索问题')
    return
  }

  searching.value = true
  hasSearched.value = true
  results.value = []

  try {
    const res = await knowledgeApi.search(kbId.value, {
      query:     q,
      top_k:     searchParams.value.top_k,
      threshold: searchParams.value.threshold,
    })

    results.value = res.data?.results || []
    elapsedMs.value = res.data?.elapsed_ms || 0
    lastQuery.value = q

    // 保存到历史
    saveHistory({
      query: q,
      count: results.value.length,
      ms:    elapsedMs.value,
    })

    if (!results.value.length) {
      ElMessage.warning('未找到匹配结果，可尝试调低相似度阈值')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '检索失败，请稍后重试')
  } finally {
    searching.value = false
  }
}

// ==================== 分数样式 ====================
function getScoreColor(score) {
  if (score >= 0.90) return '#67c23a'
  if (score >= 0.85) return '#5b8af5'
  if (score >= 0.75) return '#e6a23c'
  return '#f56c6c'
}

function getScoreClass(score) {
  if (score >= 0.90) return 'score-excellent'
  if (score >= 0.85) return 'score-good'
  if (score >= 0.75) return 'score-fair'
  return 'score-poor'
}

// ==================== 来源标签 ====================
function getSourceLabel(source) {
  const map = {
    embedding: 'Embedding',
    bm25:      'BM25',
    hybrid:    '混合',
  }
  return map[source] || source || '未知'
}

function getSourceType(source) {
  const map = {
    embedding: 'primary',
    bm25:      'success',
    hybrid:    'warning',
  }
  return map[source] || 'info'
}

// ==================== 跳转 ====================
function goItems() {
  router.push(`/admin/knowledge/${kbId.value}/items`)
}

function goEditItem(item) {
  // 跳转到条目列表并带上编辑标记（实际在列表页处理编辑弹窗）
  router.push({
    path:  `/admin/knowledge/${kbId.value}/items`,
    query: { edit: item.id },
  })
}

// ==================== 检索历史（本地存储）====================
const searchHistory = ref([])
const HISTORY_KEY   = computed(() => `search_history_kb_${kbId.value}`)

function saveHistory(record) {
  const list = JSON.parse(localStorage.getItem(HISTORY_KEY.value) || '[]')
  // 去重：相同问题则提前
  const filtered = list.filter(r => r.query !== record.query)
  filtered.unshift(record)
  const trimmed = filtered.slice(0, 20)
  localStorage.setItem(HISTORY_KEY.value, JSON.stringify(trimmed))
  searchHistory.value = trimmed
}

function loadHistory() {
  const list = JSON.parse(localStorage.getItem(HISTORY_KEY.value) || '[]')
  searchHistory.value = list
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY.value)
  searchHistory.value = []
  ElMessage.success('历史记录已清空')
}

function useHistory(record) {
  query.value = record.query
  handleSearch()
}

// ==================== 获取知识库名称 ====================
async function fetchKbName() {
  try {
    const res = await knowledgeApi.getBases()
    const kb  = (res.data || []).find(k => k.id === kbId.value)
    kbName.value = kb?.name || ''
  } catch {
    // 不影响主功能
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchKbName()
  loadHistory()
})
</script>
<style scoped lang="scss">
.knowledge-search {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 2px;
}

.page-sub {
  font-size: 12px;
  color: #909399;
}

// 检索输入卡片
.search-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
  margin-bottom: 16px;
}

.search-input-wrap {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;

  .el-input {
    flex: 1;
  }

  .el-button {
    flex-shrink: 0;
    min-width: 120px;
  }
}

// 快速测试标签
.quick-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-label {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    color: #5b8af5;
    border-color: #5b8af5;
    background: rgba(91, 138, 245, 0.06);
  }
}

// 结果区域
.results-area {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
  min-height: 300px;
}

// 结果头部
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f5f7fa;
  flex-wrap: wrap;
  gap: 10px;
}

.results-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  flex-wrap: wrap;

  strong { color: #303133; font-weight: 700; }
  em     { font-style: normal; color: #5b8af5; }
}

.no-result-icon {
  color: #e6a23c;
  font-size: 16px;
}

// 结果卡片列表
.results-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s, border-color 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  &.score-excellent { border-left: 4px solid #67c23a; }
  &.score-good      { border-left: 4px solid #5b8af5; }
  &.score-fair      { border-left: 4px solid #e6a23c; }
  &.score-poor      { border-left: 4px solid #f56c6c; }
}

// 排名 + 分数
.result-rank-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.result-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f5f7fa;
  color: #909399;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;

  .result-card:nth-child(1) & {
    background: #fff7e6;
    color: #fa8c16;
  }
  .result-card:nth-child(2) & {
    background: #f0f0f0;
    color: #595959;
  }
  .result-card:nth-child(3) & {
    background: #fff2e8;
    color: #d46b08;
  }
}

.result-score-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.result-score {
  font-size: 12px;
  font-weight: 700;
}

// 内容区
.result-content {
  flex: 1;
  min-width: 0;
}

.result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.result-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.result-answer {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.result-similar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
}

.similar-label {
  color: #909399;
  flex-shrink: 0;
}

.similar-q {
  color: #5b8af5;
  background: rgba(91, 138, 245, 0.08);
  padding: 2px 8px;
  border-radius: 10px;
}

// 操作
.result-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
}

// 表格视图
.results-table {
  margin-top: 4px;
}

.score-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.score-num {
  font-size: 15px;
  font-weight: 700;
}

.table-title {
  font-weight: 500;
  color: #303133;
}

.answer-preview {
  font-size: 12px;
}

.text-gray {
  color: #c0c4cc;
}

// 初始状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 14px;
}

.empty-icon {
  color: #dcdfe6;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #909399;
}

.empty-desc {
  font-size: 13px;
  color: #c0c4cc;
  text-align: center;
}

// 参数配置卡片
.param-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 18px 20px;
  margin-bottom: 16px;
}

.param-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 18px;

  .el-icon {
    color: #909399;
  }
}

.param-item {
  margin-bottom: 20px;

  &:last-of-type {
    margin-bottom: 0;
  }
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 10px;
}

.param-tip {
  color: #c0c4cc;
  font-size: 14px;
  cursor: help;
  transition: color 0.2s;

  &:hover {
    color: #5b8af5;
  }
}

// 阈值提示文字
.threshold-tips {
  margin-top: 6px;
  font-size: 12px;

  .tip-strict { color: #f56c6c; }
  .tip-normal { color: #67c23a; }
  .tip-loose  { color: #e6a23c; }
}

// 阈值参考
.threshold-ref {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 12px;
  margin-top: 12px;
  margin-bottom: 4px;
}

.threshold-ref-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}

.threshold-ref-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.threshold-ref-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #606266;
}

.ref-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.dot-strict { background: #f56c6c; }
  &.dot-normal { background: #67c23a; }
  &.dot-loose  { background: #e6a23c; }
}

// 检索历史卡片
.history-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 18px 20px;
  margin-bottom: 16px;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 14px;

  .el-icon {
    color: #909399;
  }
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  gap: 10px;

  &:hover {
    background: #f0f5ff;

    .history-query {
      color: #5b8af5;
    }
  }
}

.history-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.history-q-icon {
  color: #c0c4cc;
  font-size: 14px;
  flex-shrink: 0;
}

.history-query {
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s;
}

.history-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.history-count {
  font-size: 11px;
  color: #5b8af5;
  background: rgba(91, 138, 245, 0.08);
  padding: 1px 6px;
  border-radius: 10px;
  white-space: nowrap;
}

.history-ms {
  font-size: 11px;
  color: #c0c4cc;
  white-space: nowrap;
}

// 说明卡片
.tips-card {
  background: #f0f9eb;
  border: 1px solid #b3e19d;
  border-radius: 12px;
  padding: 18px 20px;
}

.tips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #2d6a4f;
  margin-bottom: 12px;

  .el-icon {
    color: #52c41a;
  }
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;

  li {
    font-size: 12px;
    color: #40916c;
    line-height: 1.6;

    strong {
      color: #1b4332;
    }
  }
}
</style>