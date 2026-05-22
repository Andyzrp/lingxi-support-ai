<template>
  <div class="reports-dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">数据报表</h2>
        <span class="page-sub">运营数据分析</span>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          value-format="YYYY-MM-DD"
          @change="fetchAll"
        />
        <el-button :icon="Refresh" @click="fetchAll">刷新</el-button>
        <el-button :icon="Download" @click="handleExport">导出报表</el-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <el-row :gutter="14" class="metric-row">
      <el-col :span="4" v-for="card in metricCards" :key="card.key">
        <div
          class="metric-card"
          :class="`metric-card--${card.color}`"
          v-loading="loadingMetrics"
        >
          <div class="metric-icon">
            <el-icon :size="24"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-body">
            <div class="metric-value">{{ card.value }}</div>
            <div class="metric-label">{{ card.label }}</div>
            <div class="metric-trend" v-if="card.trend != null">
              <el-icon :size="11">
                <CaretTop v-if="card.trend >= 0" />
                <CaretBottom v-else />
              </el-icon>
              <span :class="card.trend >= 0 ? 'trend-up' : 'trend-down'">
                {{ card.trend >= 0 ? '+' : '' }}{{ card.trend }}
              </span>
              <span class="trend-label">较昨日</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第一行图表：会话量趋势 + 意图分布 -->
    <el-row :gutter="14" class="chart-row">
      <!-- 会话量趋势 -->
      <el-col :span="16">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">会话量趋势</div>
            <div class="chart-card-actions">
              <el-radio-group v-model="sessionChartMode" size="small" @change="renderSessionChart">
                <el-radio-button value="stack">堆叠</el-radio-button>
                <el-radio-button value="line">折线</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="sessionChartRef" class="chart-body"></div>
        </div>
      </el-col>

      <!-- 意图分布饼图 -->
      <el-col :span="8">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">意图分布</div>
          </div>
          <div ref="intentChartRef" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二行图表：解决率趋势 + 满意度 -->
    <el-row :gutter="14" class="chart-row">
      <!-- 解决率趋势 -->
      <el-col :span="14">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">解决率趋势</div>
            <div class="chart-resolve-legend">
              <span class="legend-item legend-bot">Bot</span>
              <span class="legend-item legend-agent">Agent</span>
              <span class="legend-item legend-overall">综合</span>
            </div>
          </div>
          <div ref="resolveChartRef" class="chart-body"></div>
        </div>
      </el-col>

      <!-- 满意度统计 -->
      <el-col :span="10">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">用户满意度</div>
          </div>

          <!-- 满意度概览 -->
          <div class="satisfaction-overview" v-if="satisfactionData">
            <div class="satisfaction-score">
              <div class="score-num">{{ satisfactionData.avg_score }}</div>
              <el-rate
                :model-value="satisfactionData.avg_score"
                disabled
                :max="5"
                size="large"
              />
              <div class="score-total">
                共 {{ satisfactionData.total_evaluations }} 条评价
              </div>
            </div>

            <!-- 评分分布条形图 -->
            <div class="score-distribution">
              <div
                v-for="star in [5, 4, 3, 2, 1]"
                :key="star"
                class="score-bar-row"
              >
                <span class="star-label">{{ star }}星</span>
                <el-progress
                  :percentage="getScorePercent(star)"
                  :color="getStarColor(star)"
                  :stroke-width="10"
                  :show-text="false"
                  class="score-bar"
                />
                <span class="score-count">
                  {{ satisfactionData.score_distribution?.[star] || 0 }}
                </span>
              </div>
            </div>

            <!-- Top 标签 -->
            <div class="top-tags" v-if="satisfactionData.top_tags?.length">
              <div class="top-tags-title">高频好评标签</div>
              <div class="top-tags-list">
                <el-tag
                  v-for="tag in satisfactionData.top_tags.slice(0, 5)"
                  :key="tag.tag"
                  type="success"
                  size="small"
                  effect="plain"
                >
                  {{ tag.tag }} ({{ tag.count }})
                </el-tag>
              </div>
            </div>
          </div>

          <el-empty
            v-else-if="!loadingCharts"
            description="暂无满意度数据"
            :image-size="60"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：Top 未解决问题 + 回答来源分布 -->
    <el-row :gutter="14" class="chart-row">
      <!-- Top 未解决问题 -->
      <el-col :span="14">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">Top 未解决问题</div>
            <el-tag type="danger" size="small" effect="plain">
              需补充知识库
            </el-tag>
          </div>
          <div class="unanswered-list" v-if="unansweredList.length">
            <div
              v-for="(item, index) in unansweredList"
              :key="index"
              class="unanswered-item"
            >
              <div class="unanswered-rank" :class="`rank-${Math.min(index + 1, 3)}`">
                {{ index + 1 }}
              </div>
              <div class="unanswered-content">
                <div class="unanswered-question">{{ item.question }}</div>
                <el-progress
                  :percentage="Math.round((item.count / unansweredList[0].count) * 100)"
                  :color="getUnansweredColor(index)"
                  :stroke-width="5"
                  :show-text="false"
                />
              </div>
              <div class="unanswered-count">{{ item.count }} 次</div>
              <el-button
                text
                type="primary"
                size="small"
                :icon="Plus"
                @click="goAddKnowledge(item.question)"
              >
                补充
              </el-button>
            </div>
          </div>
          <el-empty
            v-else-if="!loadingCharts"
            description="暂无未解决问题数据"
            :image-size="60"
          />
        </div>
      </el-col>

      <!-- 回答来源分布 -->
      <el-col :span="10">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-card-header">
            <div class="chart-card-title">回答来源分布</div>
          </div>
          <div ref="sourceChartRef" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Download,
  Plus,
  CaretTop,
  CaretBottom,
  ChatDotRound,
  Check,
  Switch,
  Timer,
  Star,
  TrendCharts,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { reportsApi } from '@/api/admin'
import dayjs from 'dayjs'

const router = useRouter()

// ==================== 日期范围 ====================
const dateRange = ref([
  dayjs().subtract(13, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD'),
])

const dateShortcuts = [
  {
    text: '今天',
    value: () => [new Date(), new Date()],
  },
  {
    text: '最近7天',
    value: () => [dayjs().subtract(6, 'day').toDate(), new Date()],
  },
  {
    text: '最近14天',
    value: () => [dayjs().subtract(13, 'day').toDate(), new Date()],
  },
  {
    text: '最近30天',
    value: () => [dayjs().subtract(29, 'day').toDate(), new Date()],
  },
  {
    text: '本月',
    value: () => [dayjs().startOf('month').toDate(), new Date()],
  },
]

const dateParams = computed(() => ({
  start_date: dateRange.value?.[0] || '',
  end_date:   dateRange.value?.[1] || '',
}))

// ==================== 核心指标 ====================
const loadingMetrics = ref(false)
const metricsData    = ref({})

const metricCards = computed(() => [
  {
    key:   'total_sessions',
    label: '总会话量',
    value: metricsData.value.total_sessions ?? '--',
    icon:  'ChatDotRound',
    color: 'blue',
    trend: metricsData.value.compared_yesterday ?? null,
  },
  {
    key:   'today_sessions',
    label: '今日会话',
    value: metricsData.value.today_sessions ?? '--',
    icon:  'TrendCharts',
    color: 'cyan',
    trend: null,
  },
  {
    key:   'ai_resolve_rate',
    label: 'AI 解决率',
    value: metricsData.value.ai_resolve_rate != null
             ? `${(metricsData.value.ai_resolve_rate * 100).toFixed(1)}%`
             : '--',
    icon:  'Check',
    color: 'green',
    trend: null,
  },
  {
    key:   'transfer_rate',
    label: '转人工率',
    value: metricsData.value.transfer_rate != null
             ? `${(metricsData.value.transfer_rate * 100).toFixed(1)}%`
             : '--',
    icon:  'Switch',
    color: 'orange',
    trend: null,
  },
  {
    key:   'avg_response_ms',
    label: '平均响应',
    value: metricsData.value.avg_response_ms != null
             ? `${metricsData.value.avg_response_ms}ms`
             : '--',
    icon:  'Timer',
    color: 'purple',
    trend: null,
  },
  {
    key:   'satisfaction_score',
    label: '满意度',
    value: metricsData.value.satisfaction_score != null
             ? `${metricsData.value.satisfaction_score}分`
             : '--',
    icon:  'Star',
    color: 'yellow',
    trend: null,
  },
])

async function fetchMetrics() {
  loadingMetrics.value = true
  try {
    const res = await reportsApi.getDashboard(dateParams.value)
    metricsData.value = res.data || {}
  } catch {
    ElMessage.error('获取核心指标失败')
  } finally {
    loadingMetrics.value = false
  }
}

// ==================== 图表 ====================
const loadingCharts   = ref(false)
const sessionChartMode = ref('stack')

// ECharts DOM refs
const sessionChartRef = ref(null)
const intentChartRef  = ref(null)
const resolveChartRef = ref(null)
const sourceChartRef  = ref(null)

// ECharts 实例
let sessionChart = null
let intentChart  = null
let resolveChart = null
let sourceChart  = null

// 缓存图表数据（用于切换模式时重渲染）
let cachedSessionData = null

function initCharts() {
  if (sessionChartRef.value) sessionChart = echarts.init(sessionChartRef.value)
  if (intentChartRef.value)  intentChart  = echarts.init(intentChartRef.value)
  if (resolveChartRef.value) resolveChart = echarts.init(resolveChartRef.value)
  if (sourceChartRef.value)  sourceChart  = echarts.init(sourceChartRef.value)
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  sessionChart?.resize()
  intentChart?.resize()
  resolveChart?.resize()
  sourceChart?.resize()
}

// ── 会话量趋势图 ──
function renderSessionChart(data) {
  if (!sessionChart) return
  const d = data || cachedSessionData
  if (!d) return
  cachedSessionData = d

  const isStack = sessionChartMode.value === 'stack'

  sessionChart.clear()
  sessionChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data:      ['Bot 会话', 'Agent 会话', '人工会话'],
      bottom:    0,
      textStyle: { color: '#606266', fontSize: 12 },
    },
    grid: { top: 16, right: 16, bottom: 44, left: 50 },
    xAxis: {
      type:      'category',
      data:      d.dates,
      axisLabel: { color: '#909399', fontSize: 11 },
      axisLine:  { lineStyle: { color: '#e4e7ed' } },
    },
    yAxis: {
      type:       'value',
      splitLine:  { lineStyle: { color: '#f5f7fa' } },
      axisLabel:  { color: '#909399' },
    },
    series: [
      {
        name:  'Bot 会话',
        type:  isStack ? 'bar' : 'line',
        stack: isStack ? 'total' : undefined,
        data:  d.bot_sessions,
        itemStyle: { color: '#5b8af5' },
        smooth: !isStack,
      },
      {
        name:  'Agent 会话',
        type:  isStack ? 'bar' : 'line',
        stack: isStack ? 'total' : undefined,
        data:  d.agent_sessions,
        itemStyle: { color: '#67c23a' },
        smooth: !isStack,
      },
      {
        name:  '人工会话',
        type:  isStack ? 'bar' : 'line',
        stack: isStack ? 'total' : undefined,
        data:  d.human_sessions,
        itemStyle: { color: '#e6a23c' },
        smooth: !isStack,
      },
    ],
  })
  sessionChart.resize()
}

// ── 意图分布饼图 ──
function renderIntentChart(data) {
  if (!intentChart || !data?.length) return

  const INTENT_LABEL = {
    order_query:     '订单查询',
    logistics_query: '物流查询',
    refund_request:  '退款申请',
    product_query:   '商品咨询',
    complaint:       '投诉',
    greeting:        '打招呼',
    other:           '其他',
  }

  intentChart.setOption({
    tooltip: {
      trigger:   'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient:    'vertical',
      right:     6,
      top:       'center',
      textStyle: { color: '#606266', fontSize: 11 },
    },
    series: [
      {
        type:   'pie',
        radius: ['42%', '68%'],
        center: ['36%', '50%'],
        data:   data.map(item => ({
          name:  INTENT_LABEL[item.intent] || item.intent,
          value: item.count,
        })),
        label:     { show: false },
        emphasis:  {
          itemStyle: {
            shadowBlur:   10,
            shadowColor:  'rgba(0,0,0,0.15)',
          },
        },
        color: [
          '#5b8af5', '#67c23a', '#e6a23c',
          '#f56c6c', '#9b59b6', '#1abc9c', '#909399',
        ],
      },
    ],
  }, true)
}

// ── 解决率趋势折线图 ──
function renderResolveChart(data) {
  if (!resolveChart || !data) return

  resolveChart.setOption({
    tooltip: {
      trigger:   'axis',
      formatter: (params) =>
        params[0].name + '<br/>' +
        params.map(p =>
          `${p.marker}${p.seriesName}: ${(p.value * 100).toFixed(1)}%`
        ).join('<br/>'),
    },
    grid: { top: 16, right: 16, bottom: 44, left: 56 },
    xAxis: {
      type:      'category',
      data:      data.dates,
      axisLabel: { color: '#909399', fontSize: 11 },
      axisLine:  { lineStyle: { color: '#e4e7ed' } },
    },
    yAxis: {
      type: 'value',
      min:  0,
      max:  1,
      axisLabel: {
        color:     '#909399',
        formatter: (v) => `${(v * 100).toFixed(0)}%`,
      },
      splitLine: { lineStyle: { color: '#f5f7fa' } },
    },
    legend: {
      bottom:    0,
      textStyle: { color: '#606266', fontSize: 12 },
    },
    series: [
      {
        name:      'Bot 解决率',
        type:      'line',
        data:      data.bot_resolve_rate,
        smooth:    true,
        symbol:    'circle',
        symbolSize: 5,
        lineStyle: { color: '#5b8af5', width: 2 },
        itemStyle: { color: '#5b8af5' },
        areaStyle: { color: 'rgba(91,138,245,0.07)' },
      },
      {
        name:      'Agent 解决率',
        type:      'line',
        data:      data.agent_resolve_rate,
        smooth:    true,
        symbol:    'circle',
        symbolSize: 5,
        lineStyle: { color: '#67c23a', width: 2 },
        itemStyle: { color: '#67c23a' },
        areaStyle: { color: 'rgba(103,194,58,0.07)' },
      },
      {
        name:      '综合解决率',
        type:      'line',
        data:      data.overall_resolve_rate,
        smooth:    true,
        symbol:    'circle',
        symbolSize: 5,
        lineStyle: { color: '#e6a23c', width: 2, type: 'dashed' },
        itemStyle: { color: '#e6a23c' },
      },
    ],
  }, true)
}

// ── 回答来源分布环图 ──
function renderSourceChart(intentData) {
  if (!sourceChart || !intentData?.length) return

  // 从意图数据推算来源分布（或用实际来源数据）
  const sourceData = [
    { name: 'RAG 检索',  value: intentData.find(i => i.intent === 'order_query')?.count || 0 },
    { name: '工具调用',  value: intentData.find(i => i.intent === 'logistics_query')?.count || 0 },
    { name: 'LLM 生成',  value: intentData.find(i => i.intent === 'product_query')?.count || 0 },
    { name: '关键词干预', value: intentData.find(i => i.intent === 'greeting')?.count || 0 },
    { name: '兜底回复',  value: intentData.find(i => i.intent === 'other')?.count || 0 },
  ].filter(d => d.value > 0)

  sourceChart.setOption({
    tooltip: {
      trigger:   'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient:    'vertical',
      right:     6,
      top:       'center',
      textStyle: { color: '#606266', fontSize: 11 },
    },
    series: [
      {
        type:   'pie',
        radius: ['40%', '65%'],
        center: ['36%', '50%'],
        data:   sourceData,
        label:  { show: false },
        color:  ['#5b8af5', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
      },
    ],
  }, true)
}

// ==================== 满意度数据 ====================
const satisfactionData = ref(null)

function getScorePercent(star) {
  if (!satisfactionData.value) return 0
  const total = satisfactionData.value.total_evaluations || 1
  const count = satisfactionData.value.score_distribution?.[star] || 0
  return Math.round((count / total) * 100)
}

function getStarColor(star) {
  const map = { 5: '#67c23a', 4: '#85ce61', 3: '#e6a23c', 2: '#f56c6c', 1: '#f56c6c' }
  return map[star] || '#909399'
}

// ==================== Top 未解决问题 ====================
const unansweredList = ref([])

function getUnansweredColor(index) {
  const colors = ['#f56c6c', '#e6a23c', '#5b8af5', '#67c23a', '#909399']
  return colors[Math.min(index, colors.length - 1)]
}

function goAddKnowledge(question) {
  router.push({
    path:  '/admin/knowledge',
    query: { preset_question: question },
  })
}

// ==================== 全量拉取 ====================
async function fetchCharts() {
  loadingCharts.value = true
  try {
    const [sessionsRes, resolveRes, intentRes, unansweredRes, satisfactionRes] =
      await Promise.all([
        reportsApi.getSessions(dateParams.value),
        reportsApi.getResolveRate(dateParams.value),
        reportsApi.getIntentDistribution(dateParams.value),
        reportsApi.getTopUnanswered({ ...dateParams.value, limit: 10 }),
        reportsApi.getSatisfaction(dateParams.value),
      ])

    await nextTick()
    renderSessionChart(sessionsRes.data)
    renderResolveChart(resolveRes.data)
    renderIntentChart(intentRes.data)
    renderSourceChart(intentRes.data)

    unansweredList.value = unansweredRes.data || []
    satisfactionData.value = satisfactionRes.data || null
  } catch {
    ElMessage.error('获取报表数据失败')
  } finally {
    loadingCharts.value = false
  }
}

function fetchAll() {
  fetchMetrics()
  fetchCharts()
}

// ==================== 导出报表 ====================
function handleExport() {
  ElMessage.info('报表导出功能开发中，敬请期待')
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await nextTick()
  initCharts()
  fetchAll()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  sessionChart?.dispose()
  intentChart?.dispose()
  resolveChart?.dispose()
  sourceChart?.dispose()
})
</script>
<style scoped lang="scss">
.reports-dashboard {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-header-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.page-sub {
  font-size: 13px;
  color: #909399;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

// 指标卡片
.metric-row {
  margin-bottom: 14px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 14px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border-left: 4px solid transparent;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
  }

  &--blue   {
    border-left-color: #5b8af5;
    .metric-icon { background: rgba(91,138,245,0.1); color: #5b8af5; }
  }
  &--cyan   {
    border-left-color: #36cfc9;
    .metric-icon { background: rgba(54,207,201,0.1); color: #36cfc9; }
  }
  &--green  {
    border-left-color: #67c23a;
    .metric-icon { background: rgba(103,194,58,0.1); color: #67c23a; }
  }
  &--orange {
    border-left-color: #e6a23c;
    .metric-icon { background: rgba(230,162,60,0.1); color: #e6a23c; }
  }
  &--purple {
    border-left-color: #9b59b6;
    .metric-icon { background: rgba(155,89,182,0.1); color: #9b59b6; }
  }
  &--yellow {
    border-left-color: #f59e0b;
    .metric-icon { background: rgba(245,158,11,0.1); color: #f59e0b; }
  }
}

.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-body {
  flex: 1;
  min-width: 0;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.metric-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 3px;
  font-size: 11px;

  .trend-up   { color: #67c23a; }
  .trend-down { color: #f56c6c; }
  .trend-label { color: #c0c4cc; }
}

// 图表行
.chart-row {
  margin-bottom: 14px;
}

// 图表卡片
.chart-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 16px 20px 20px;
  height: 340px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
  }
}

.chart-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.chart-card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.chart-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 解决率图例
.chart-resolve-legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-item {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;

  &::before {
    content: '';
    display: inline-block;
    width: 24px;
    height: 3px;
    border-radius: 2px;
  }

  &.legend-bot::before    { background: #5b8af5; }
  &.legend-agent::before  { background: #67c23a; }
  &.legend-overall::before {
    background: #e6a23c;
    border-top: 2px dashed #e6a23c;
    height: 0;
  }
}

// ECharts 图表容器
.chart-body {
  flex: 1;
  min-height: 0;
}

// 满意度概览
.satisfaction-overview {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.satisfaction-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f7fa;
}

.score-num {
  font-size: 36px;
  font-weight: 800;
  color: #f59e0b;
  line-height: 1;
}

.score-total {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

// 评分分布
.score-distribution {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.star-label {
  font-size: 12px;
  color: #909399;
  width: 28px;
  flex-shrink: 0;
  text-align: right;
}

.score-bar {
  flex: 1;
}

.score-count {
  font-size: 12px;
  color: #909399;
  width: 28px;
  flex-shrink: 0;
  text-align: right;
}

// Top 标签
.top-tags {
  padding-top: 10px;
  border-top: 1px solid #f5f7fa;
}

.top-tags-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.top-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

// Top 未解决问题列表
.unanswered-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #e4e7ed;
    border-radius: 2px;
  }
}

.unanswered-item {
  display: grid;
  grid-template-columns: 28px 1fr 52px 56px;
  align-items: center;
  gap: 10px;
}

.unanswered-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #f0f2f5;
  color: #909399;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.rank-1 { background: #fff2e8; color: #fa8c16; }
  &.rank-2 { background: #f9f0ff; color: #722ed1; }
  &.rank-3 { background: #e6f7ff; color: #1890ff; }
}

.unanswered-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.unanswered-question {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.unanswered-count {
  font-size: 12px;
  color: #909399;
  text-align: right;
  white-space: nowrap;
}
</style>