<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">工作台</h2>
      <div class="header-actions">
        <!-- 日期范围选择 -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          value-format="YYYY-MM-DD"
          size="default"
          @change="handleDateChange"
        />
        <el-button :icon="Refresh" @click="fetchAll">刷新</el-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6" v-for="card in metricCards" :key="card.key">
        <div class="metric-card" :class="`metric-card--${card.color}`" v-loading="loadingMetrics">
          <div class="metric-icon">
            <el-icon :size="28"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-body">
            <div class="metric-value">{{ card.value }}</div>
            <div class="metric-label">{{ card.label }}</div>
            <div class="metric-sub" v-if="card.sub">
              <el-icon :size="12">
                <CaretTop v-if="card.subPositive" />
                <CaretBottom v-else />
              </el-icon>
              <span :class="card.subPositive ? 'text-up' : 'text-down'">{{ card.sub }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 第一行 -->
    <el-row :gutter="16" class="chart-row">
      <!-- 会话量趋势 -->
      <el-col :span="16">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-header">
            <span class="chart-title">会话量趋势</span>
            <el-radio-group v-model="sessionChartType" size="small">
              <el-radio-button value="stack">堆叠</el-radio-button>
              <el-radio-button value="line">折线</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="sessionChartRef" class="chart-body"></div>
        </div>
      </el-col>

      <!-- 意图分布 -->
      <el-col :span="8">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-header">
            <span class="chart-title">意图分布</span>
          </div>
          <div ref="intentChartRef" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 第二行 -->
    <el-row :gutter="16" class="chart-row">
      <!-- 解决率趋势 -->
      <el-col :span="12">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-header">
            <span class="chart-title">解决率趋势</span>
          </div>
          <div ref="resolveChartRef" class="chart-body"></div>
        </div>
      </el-col>

      <!-- 满意度 + Top 未解决 -->
      <el-col :span="12">
        <div class="chart-card" v-loading="loadingCharts">
          <div class="chart-header">
            <span class="chart-title">Top 未解决问题</span>
          </div>
          <div class="unanswered-list">
            <div
              v-for="(item, index) in unansweredList"
              :key="index"
              class="unanswered-item"
            >
              <span class="unanswered-rank" :class="`rank-${index + 1}`">
                {{ index + 1 }}
              </span>
              <span class="unanswered-question">{{ item.question }}</span>
              <span class="unanswered-count">{{ item.count }} 次</span>
              <el-progress
                :percentage="Math.round((item.count / unansweredList[0]?.count) * 100)"
                :show-text="false"
                :stroke-width="4"
                class="unanswered-bar"
              />
            </div>
            <el-empty v-if="!unansweredList.length" description="暂无数据" :image-size="60" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  CaretTop,
  CaretBottom,
  ChatDotRound,
  Check,
  Switch,
  Timer,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { reportsApi } from '@/api/admin'
import dayjs from 'dayjs'

// ==================== 日期范围 ====================
const dateRange = ref([
  dayjs().subtract(13, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD'),
])

const dateShortcuts = [
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
]

const dateParams = computed(() => ({
  start_date: dateRange.value?.[0] || '',
  end_date:   dateRange.value?.[1] || '',
}))

// ==================== 核心指标 ====================
const loadingMetrics = ref(false)
const metrics = ref({})

const metricCards = computed(() => [
  {
    key:         'total_sessions',
    label:       '总会话量',
    value:       metrics.value.total_sessions ?? '--',
    icon:        'ChatDotRound',
    color:       'blue',
    sub:         metrics.value.compared_yesterday != null
                   ? `较昨日 ${metrics.value.compared_yesterday > 0 ? '+' : ''}${metrics.value.compared_yesterday}`
                   : null,
    subPositive: (metrics.value.compared_yesterday ?? 0) >= 0,
  },
  {
    key:   'ai_resolve_rate',
    label: 'AI 解决率',
    value: metrics.value.ai_resolve_rate != null
             ? `${(metrics.value.ai_resolve_rate * 100).toFixed(1)}%`
             : '--',
    icon:  'Check',
    color: 'green',
  },
  {
    key:   'transfer_rate',
    label: '转人工率',
    value: metrics.value.transfer_rate != null
             ? `${(metrics.value.transfer_rate * 100).toFixed(1)}%`
             : '--',
    icon:  'Switch',
    color: 'orange',
  },
  {
    key:   'avg_response_ms',
    label: '平均响应时长',
    value: metrics.value.avg_response_ms != null
             ? `${metrics.value.avg_response_ms} ms`
             : '--',
    icon:  'Timer',
    color: 'purple',
  },
])

async function fetchMetrics() {
  loadingMetrics.value = true
  try {
    const res = await reportsApi.getDashboard(dateParams.value)
    metrics.value = res.data || {}
  } catch {
    ElMessage.error('获取核心指标失败')
  } finally {
    loadingMetrics.value = false
  }
}

// ==================== 图表数据 ====================
const loadingCharts = ref(false)
const sessionChartType = ref('stack')
const unansweredList = ref([])

// ECharts 实例
const sessionChartRef = ref(null)
const intentChartRef  = ref(null)
const resolveChartRef = ref(null)
let sessionChart = null
let intentChart  = null
let resolveChart = null

// 初始化图表实例
function initCharts() {
  if (sessionChartRef.value) {
    sessionChart = echarts.init(sessionChartRef.value)
  }
  if (intentChartRef.value) {
    intentChart = echarts.init(intentChartRef.value)
  }
  if (resolveChartRef.value) {
    resolveChart = echarts.init(resolveChartRef.value)
  }

  // 响应式
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  sessionChart?.resize()
  intentChart?.resize()
  resolveChart?.resize()
}

// 会话量趋势图
function renderSessionChart(data) {
  if (!sessionChart || !data) return
  const isStack = sessionChartType.value === 'stack'

  sessionChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['Bot会话', 'Agent会话', '人工会话'],
      bottom: 0,
      textStyle: { color: '#606266' },
    },
    grid: { top: 16, right: 16, bottom: 40, left: 48 },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLine: { lineStyle: { color: '#e4e7ed' } },
      axisLabel: { color: '#909399', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#909399' },
    },
    series: [
      {
        name: 'Bot会话',
        type: 'bar',
        stack: isStack ? 'total' : undefined,
        data: data.bot_sessions,
        itemStyle: { color: '#5b8af5', borderRadius: isStack ? 0 : [3, 3, 0, 0] },
      },
      {
        name: 'Agent会话',
        type: 'bar',
        stack: isStack ? 'total' : undefined,
        data: data.agent_sessions,
        itemStyle: { color: '#67c23a', borderRadius: isStack ? 0 : [3, 3, 0, 0] },
      },
      {
        name: '人工会话',
        type: 'bar',
        stack: isStack ? 'total' : undefined,
        data: data.human_sessions,
        itemStyle: { color: '#e6a23c', borderRadius: isStack ? [3, 3, 0, 0] : [3, 3, 0, 0] },
      },
    ],
  }, true)
}

// 解决率趋势图
function renderResolveChart(data) {
  if (!resolveChart || !data) return

  resolveChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) =>
        params[0].name + '<br/>' +
        params.map(p => `${p.marker}${p.seriesName}: ${(p.value * 100).toFixed(1)}%`).join('<br/>'),
    },
    legend: {
      data: ['Bot解决率', 'Agent解决率', '综合解决率'],
      bottom: 0,
      textStyle: { color: '#606266' },
    },
    grid: { top: 16, right: 16, bottom: 40, left: 52 },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: { color: '#909399', fontSize: 11 },
      axisLine: { lineStyle: { color: '#e4e7ed' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: {
        color: '#909399',
        formatter: (v) => `${(v * 100).toFixed(0)}%`,
      },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
    },
    series: [
      {
        name: 'Bot解决率',
        type: 'line',
        data: data.bot_resolve_rate,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#5b8af5', width: 2 },
        itemStyle: { color: '#5b8af5' },
        areaStyle: { color: 'rgba(91,138,245,0.08)' },
      },
      {
        name: 'Agent解决率',
        type: 'line',
        data: data.agent_resolve_rate,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#67c23a', width: 2 },
        itemStyle: { color: '#67c23a' },
        areaStyle: { color: 'rgba(103,194,58,0.08)' },
      },
      {
        name: '综合解决率',
        type: 'line',
        data: data.overall_resolve_rate,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#e6a23c', width: 2, type: 'dashed' },
        itemStyle: { color: '#e6a23c' },
      },
    ],
  }, true)
}

// 意图分布饼图
function renderIntentChart(data) {
  if (!intentChart || !data?.length) return

  const INTENT_MAP = {
    order_query:     '订单查询',
    logistics_query: '物流查询',
    refund_request:  '退款申请',
    product_query:   '商品咨询',
    complaint:       '投诉',
    greeting:        '打招呼',
    other:           '其他',
  }

  const pieData = data.map(item => ({
    name:  INTENT_MAP[item.intent] || item.intent,
    value: item.count,
  }))

  intentChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'center',
      textStyle: { color: '#606266', fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['38%', '50%'],
        data: pieData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,0.2)',
          },
        },
        color: [
          '#5b8af5', '#67c23a', '#e6a23c',
          '#f56c6c', '#909399', '#9b59b6', '#1abc9c',
        ],
      },
    ],
  }, true)
}

// 拉取所有图表数据
let sessionData = null
async function fetchCharts() {
  loadingCharts.value = true
  try {
    const [sessionsRes, resolveRes, intentRes, unansweredRes] = await Promise.all([
      reportsApi.getSessions(dateParams.value),
      reportsApi.getResolveRate(dateParams.value),
      reportsApi.getIntentDistribution(dateParams.value),
      reportsApi.getTopUnanswered({ ...dateParams.value, limit: 8 }),
    ])
    sessionData = sessionsRes.data
    await nextTick()
    renderSessionChart(sessionsRes.data)
    renderResolveChart(resolveRes.data)
    renderIntentChart(intentRes.data)
    unansweredList.value = unansweredRes.data || []
  } catch {
    ElMessage.error('获取图表数据失败')
  } finally {
    loadingCharts.value = false
  }
}

// 切换堆叠/折线时重渲染
watch(sessionChartType, () => {
  renderSessionChart(sessionData)
})

// 日期变化
function handleDateChange() {
  fetchAll()
}

// 全量刷新
function fetchAll() {
  fetchMetrics()
  fetchCharts()
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await nextTick()
  initCharts()
  fetchAll()
})
</script>
<style scoped lang="scss">
.dashboard {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

// 指标卡片
.metric-row {
  margin-bottom: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border-left: 4px solid transparent;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  &--blue {
    border-left-color: #5b8af5;
    .metric-icon { background: rgba(91, 138, 245, 0.1); color: #5b8af5; }
  }
  &--green {
    border-left-color: #67c23a;
    .metric-icon { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
  }
  &--orange {
    border-left-color: #e6a23c;
    .metric-icon { background: rgba(230, 162, 60, 0.1); color: #e6a23c; }
  }
  &--purple {
    border-left-color: #9b59b6;
    .metric-icon { background: rgba(155, 89, 182, 0.1); color: #9b59b6; }
  }
}

.metric-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
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
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.metric-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.metric-sub {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 4px;
  font-size: 12px;

  .text-up   { color: #67c23a; }
  .text-down { color: #f56c6c; }
}

// 图表卡片
.chart-row {
  margin-bottom: 16px;
}

.chart-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 16px 20px 20px;
  height: 320px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.chart-body {
  flex: 1;
  min-height: 0;
}

// Top 未解决问题列表
.unanswered-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.unanswered-item {
  display: grid;
  grid-template-columns: 24px 1fr 52px;
  grid-template-rows: auto 4px;
  align-items: center;
  column-gap: 10px;
  row-gap: 4px;
}

.unanswered-rank {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f0f2f5;
  color: #909399;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;

  &.rank-1 { background: #fff2e8; color: #fa8c16; }
  &.rank-2 { background: #f9f0ff; color: #722ed1; }
  &.rank-3 { background: #e6f7ff; color: #1890ff; }
}

.unanswered-question {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unanswered-count {
  font-size: 12px;
  color: #909399;
  text-align: right;
  white-space: nowrap;
}

.unanswered-bar {
  grid-column: 2 / 4;
}
</style>