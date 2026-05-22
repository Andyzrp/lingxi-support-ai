<template>
  <div class="settings">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h2 class="page-title">系统设置</h2>
        <span class="page-sub">灵犀智能客服系统配置</span>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：设置菜单 -->
      <el-col :span="5">
        <div class="settings-nav">
          <div
            v-for="nav in navList"
            :key="nav.key"
            class="nav-item"
            :class="{ active: activeNav === nav.key }"
            @click="activeNav = nav.key"
          >
            <el-icon><component :is="nav.icon" /></el-icon>
            <span>{{ nav.label }}</span>
          </div>
        </div>
      </el-col>

      <!-- 右侧：设置内容 -->
      <el-col :span="19">

        <!-- 基础信息设置 -->
        <div v-show="activeNav === 'basic'" class="settings-section">
          <div class="section-header">
            <div class="section-title">基础信息</div>
            <div class="section-desc">系统名称、Logo 等基础配置</div>
          </div>

          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicRules"
            label-width="120px"
            class="settings-form"
          >
            <el-form-item label="系统名称" prop="system_name">
              <el-input
                v-model="basicForm.system_name"
                placeholder="灵犀智能客服"
                maxlength="30"
                show-word-limit
                clearable
                style="width: 320px"
              />
            </el-form-item>

            <el-form-item label="系统副标题" prop="system_subtitle">
              <el-input
                v-model="basicForm.system_subtitle"
                placeholder="后台管理平台"
                maxlength="50"
                show-word-limit
                clearable
                style="width: 320px"
              />
            </el-form-item>

            <el-form-item label="版权信息" prop="copyright">
              <el-input
                v-model="basicForm.copyright"
                placeholder="灵犀智能客服系统 © 2026"
                maxlength="100"
                clearable
                style="width: 400px"
              />
            </el-form-item>

            <el-form-item label="系统语言">
              <el-select v-model="basicForm.language" style="width: 200px">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="繁體中文" value="zh-TW" />
                <el-option label="English"  value="en-US" />
              </el-select>
            </el-form-item>

            <el-form-item label="时区">
              <el-select v-model="basicForm.timezone" style="width: 200px">
                <el-option label="UTC+8 北京时间" value="Asia/Shanghai" />
                <el-option label="UTC+0 格林威治"  value="UTC" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="savingBasic"
                @click="saveBasicForm"
              >
                保存基础配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 对话参数设置 -->
        <div v-show="activeNav === 'chat'" class="settings-section">
          <div class="section-header">
            <div class="section-title">对话参数</div>
            <div class="section-desc">会话超时、转人工等核心参数配置</div>
          </div>

          <el-form
            ref="chatFormRef"
            :model="chatForm"
            label-width="160px"
            class="settings-form"
          >
            <el-form-item label="会话超时时间">
              <el-input-number
                v-model="chatForm.session_timeout"
                :min="1"
                :max="60"
                :step="1"
                style="width: 140px"
              />
              <span class="form-unit">分钟</span>
              <div class="form-hint">
                用户超过此时间未发消息，会话自动关闭
              </div>
            </el-form-item>

            <el-form-item label="最大消息长度">
              <el-input-number
                v-model="chatForm.max_message_length"
                :min="50"
                :max="2000"
                :step="50"
                style="width: 140px"
              />
              <span class="form-unit">字符</span>
            </el-form-item>

            <el-form-item label="自动转人工阈值">
              <el-input-number
                v-model="chatForm.auto_transfer_threshold"
                :min="1"
                :max="10"
                :step="1"
                style="width: 140px"
              />
              <span class="form-unit">次</span>
              <div class="form-hint">
                AI 连续答不上此次数后，自动转接人工
              </div>
            </el-form-item>

            <el-form-item label="心跳间隔">
              <el-input-number
                v-model="chatForm.heartbeat_interval"
                :min="10"
                :max="120"
                :step="5"
                style="width: 140px"
              />
              <span class="form-unit">秒</span>
            </el-form-item>

            <el-form-item label="欢迎语">
              <el-input
                v-model="chatForm.welcome_message"
                type="textarea"
                :rows="3"
                placeholder="您好！我是灵犀智能客服，请问有什么可以帮助您？"
                maxlength="200"
                show-word-limit
                style="width: 480px"
              />
            </el-form-item>

            <el-form-item label="评价推送延迟">
              <el-input-number
                v-model="chatForm.evaluate_delay"
                :min="0"
                :max="300"
                :step="10"
                style="width: 140px"
              />
              <span class="form-unit">秒</span>
              <div class="form-hint">
                会话结束后多少秒推送评价卡片（0 表示立即推送）
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="savingChat"
                @click="saveChatForm"
              >
                保存对话配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 管理员账号管理 -->
        <div v-show="activeNav === 'admins'" class="settings-section">
          <div class="section-header">
            <div class="section-title">管理员账号</div>
            <div class="section-desc">管理后台账号权限</div>
          </div>

          <!-- 管理员列表 -->
          <div class="admins-toolbar">
            <el-button
              type="primary"
              :icon="Plus"
              @click="openAdminDialog()"
            >
              新增管理员
            </el-button>
          </div>

          <el-table
            :data="adminList"
            border
            stripe
            v-loading="loadingAdmins"
            style="width: 100%"
          >
            <el-table-column label="用户名" prop="username" min-width="120" />
            <el-table-column label="昵称" prop="nickname" min-width="120" />
            <el-table-column label="角色" width="130" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="getRoleType(row.role)"
                  size="small"
                  round
                >
                  {{ getRoleLabel(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.status"
                  :active-value="1"
                  :inactive-value="0"
                  size="small"
                  :disabled="row.role === 'super_admin'"
                  @change="handleAdminStatusChange(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="160" align="center">
              <template #default="{ row }">
                <span class="text-time">{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  :icon="Edit"
                  @click="openAdminDialog(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  :icon="Delete"
                  :disabled="row.role === 'super_admin'"
                  @click="handleDeleteAdmin(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 新增/编辑管理员弹窗 -->
          <el-dialog
            v-model="adminDialogVisible"
            :title="editAdmin ? '编辑管理员' : '新增管理员'"
            width="480px"
            :close-on-click-modal="false"
            @closed="resetAdminForm"
          >
            <el-form
              ref="adminFormRef"
              :model="adminForm"
              :rules="adminRules"
              label-width="90px"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="adminForm.username"
                  placeholder="请输入用户名"
                  :disabled="!!editAdmin"
                  clearable
                />
              </el-form-item>

              <el-form-item label="昵称" prop="nickname">
                <el-input
                  v-model="adminForm.nickname"
                  placeholder="请输入昵称"
                  clearable
                />
              </el-form-item>

              <el-form-item
                label="密码"
                prop="password"
                :rules="editAdmin ? [] : adminRules.password"
              >
                <el-input
                  v-model="adminForm.password"
                  type="password"
                  :placeholder="editAdmin ? '留空则不修改密码' : '请输入密码'"
                  show-password
                  clearable
                />
              </el-form-item>

              <el-form-item label="角色" prop="role">
                <el-select
                  v-model="adminForm.role"
                  style="width: 100%"
                  :disabled="editAdmin?.role === 'super_admin'"
                >
                  <el-option label="超级管理员" value="super_admin" />
                  <el-option label="管理员"     value="admin" />
                  <el-option label="运营人员"   value="operator" />
                  <el-option label="只读用户"   value="viewer" />
                </el-select>
              </el-form-item>
            </el-form>

            <template #footer>
              <el-button @click="adminDialogVisible = false">取消</el-button>
              <el-button
                type="primary"
                :loading="savingAdmin"
                @click="handleSaveAdmin"
              >
                {{ editAdmin ? '保存修改' : '立即创建' }}
              </el-button>
            </template>
          </el-dialog>
        </div>

        <!-- 修改密码 -->
        <div v-show="activeNav === 'password'" class="settings-section">
          <div class="section-header">
            <div class="section-title">修改密码</div>
            <div class="section-desc">修改当前管理员登录密码</div>
          </div>

          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="120px"
            class="settings-form"
            style="max-width: 460px"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input
                v-model="pwdForm.old_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="pwdForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="pwdForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="savingPwd"
                @click="handleChangePwd"
              >
                修改密码
              </el-button>
              <el-button @click="resetPwdForm">重置</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 系统信息 -->
        <div v-show="activeNav === 'about'" class="settings-section">
          <div class="section-header">
            <div class="section-title">系统信息</div>
            <div class="section-desc">当前系统版本与技术栈信息</div>
          </div>

          <div class="about-content">
            <!-- Logo + 系统名称 -->
            <div class="about-hero">
              <img
                src="/brand/lingxi-admin-logo-dark.svg"
                alt="灵犀客服"
                class="about-logo"
              />
              <div class="about-name">灵犀智能客服系统</div>
              <div class="about-version">
                <el-tag type="primary" effect="dark">v1.0.0</el-tag>
              </div>
              <div class="about-desc">
                基于 Bot + Agent 双层拦截架构的电商智能客服系统，
                私有化部署，AI 解决率目标 ≥ 68%。
              </div>
            </div>

            <!-- 技术栈 -->
            <el-divider content-position="left">技术栈</el-divider>
            <el-row :gutter="12" class="tech-grid">
              <el-col
                :span="8"
                v-for="tech in techStack"
                :key="tech.name"
              >
                <div class="tech-item">
                  <div class="tech-name">{{ tech.name }}</div>
                  <div class="tech-value">{{ tech.value }}</div>
                </div>
              </el-col>
            </el-row>

            <!-- 中间件状态 -->
            <el-divider content-position="left">中间件连接状态</el-divider>
            <div class="middleware-list">
              <div
                v-for="mw in middlewareStatus"
                :key="mw.name"
                class="middleware-item"
              >
                <div class="mw-left">
                  <span
                    class="mw-dot"
                    :class="mw.connected ? 'dot-online' : 'dot-offline'"
                  ></span>
                  <span class="mw-name">{{ mw.name }}</span>
                </div>
                <div class="mw-right">
                  <span class="mw-addr">{{ mw.addr }}</span>
                  <el-tag
                    :type="mw.connected ? 'success' : 'danger'"
                    size="small"
                    round
                  >
                    {{ mw.connected ? '已连接' : '未连接' }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 版权 -->
            <div class="about-footer">
              <span>灵犀智能客服系统 © 2026 · 私有化部署版</span>
            </div>
          </div>
        </div>

      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  ChatDotRound,
  UserFilled,
  Lock,
  InfoFilled,
  Plus,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { adminAuthApi } from '@/api/admin'
import { useAdminStore } from '@/stores/admin'
import dayjs from 'dayjs'

const adminStore = useAdminStore()

// ==================== 左侧导航 ====================
const activeNav = ref('basic')

const navList = [
  { key: 'basic',    label: '基础信息', icon: 'Setting'      },
  { key: 'chat',     label: '对话参数', icon: 'ChatDotRound' },
  { key: 'admins',   label: '管理员账号', icon: 'UserFilled' },
  { key: 'password', label: '修改密码', icon: 'Lock'         },
  { key: 'about',    label: '系统信息', icon: 'InfoFilled'   },
]

// ==================== 基础信息配置 ====================
const basicFormRef = ref(null)
const savingBasic  = ref(false)

const basicForm = ref({
  system_name:     '灵犀智能客服',
  system_subtitle: '后台管理平台',
  copyright:       '灵犀智能客服系统 © 2026',
  language:        'zh-CN',
  timezone:        'Asia/Shanghai',
})

const basicRules = {
  system_name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' },
  ],
}

async function saveBasicForm() {
  await basicFormRef.value?.validate(async (valid) => {
    if (!valid) return
    savingBasic.value = true
    try {
      // 存储到 localStorage（后端暂无系统配置接口 [3]）
      localStorage.setItem('lingxi_basic_config', JSON.stringify(basicForm.value))
      ElMessage.success('基础配置已保存')
    } finally {
      savingBasic.value = false
    }
  })
}

function loadBasicForm() {
  const saved = localStorage.getItem('lingxi_basic_config')
  if (saved) {
    try {
      Object.assign(basicForm.value, JSON.parse(saved))
    } catch {
      // 忽略解析错误
    }
  }
}

// ==================== 对话参数配置 ====================
const chatFormRef = ref(null)
const savingChat  = ref(false)

const chatForm = ref({
  session_timeout:         5,
  max_message_length:      500,
  auto_transfer_threshold: 3,
  heartbeat_interval:      30,
  welcome_message:         '您好！我是灵犀智能客服，请问有什么可以帮助您？',
  evaluate_delay:          30,
})

async function saveChatForm() {
  savingChat.value = true
  try {
    localStorage.setItem('lingxi_chat_config', JSON.stringify(chatForm.value))
    ElMessage.success('对话配置已保存')
  } finally {
    savingChat.value = false
  }
}

function loadChatForm() {
  const saved = localStorage.getItem('lingxi_chat_config')
  if (saved) {
    try {
      Object.assign(chatForm.value, JSON.parse(saved))
    } catch {
      // 忽略解析错误
    }
  }
}

// ==================== 管理员账号管理 ====================
const loadingAdmins     = ref(false)
const adminList         = ref([])
const adminDialogVisible = ref(false)
const savingAdmin       = ref(false)
const editAdmin         = ref(null)
const adminFormRef      = ref(null)

const adminForm = ref({
  username: '',
  nickname: '',
  password: '',
  role:     'operator',
})

const adminRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 30, message: '用户名长度 2-30 个字符', trigger: 'blur' },
  ],
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于 6 位', trigger: 'blur' },
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' },
  ],
}

async function fetchAdmins() {
  loadingAdmins.value = true
  try {
    const res = await adminAuthApi.getAdmins()
    adminList.value = res.data || []
  } catch {
    ElMessage.error('获取管理员列表失败')
  } finally {
    loadingAdmins.value = false
  }
}

function openAdminDialog(admin = null) {
  editAdmin.value = admin
  if (admin) {
    adminForm.value.username = admin.username
    adminForm.value.nickname = admin.nickname
    adminForm.value.password = ''
    adminForm.value.role     = admin.role
  }
  adminDialogVisible.value = true
}

function resetAdminForm() {
  adminForm.value = { username: '', nickname: '', password: '', role: 'operator' }
  adminFormRef.value?.clearValidate()
  editAdmin.value = null
}

async function handleSaveAdmin() {
  await adminFormRef.value?.validate(async (valid) => {
    if (!valid) return
    savingAdmin.value = true
    try {
      if (editAdmin.value) {
        const payload = {
          nickname: adminForm.value.nickname,
          role:     adminForm.value.role,
        }
        if (adminForm.value.password) {
          payload.password = adminForm.value.password
        }
        await adminAuthApi.updateAdmin(editAdmin.value.id, payload)
        ElMessage.success('修改成功')
      } else {
        await adminAuthApi.createAdmin(adminForm.value)
        ElMessage.success('创建成功')
      }
      adminDialogVisible.value = false
      fetchAdmins()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    } finally {
      savingAdmin.value = false
    }
  })
}

async function handleAdminStatusChange(row) {
  try {
    await adminAuthApi.updateAdmin(row.id, { status: row.status })
    ElMessage.success(row.status === 1 ? '已启用' : '已停用')
  } catch {
    row.status = row.status === 1 ? 0 : 1
    ElMessage.error('状态更新失败')
  }
}

async function handleDeleteAdmin(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除管理员「${row.nickname || row.username}」？`,
      '删除确认',
      {
        type:               'warning',
        confirmButtonText:  '确认删除',
        cancelButtonText:   '取消',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await adminAuthApi.deleteAdmin(row.id)
    ElMessage.success('删除成功')
    fetchAdmins()
  } catch {
    // 用户取消不处理
  }
}

// 角色标签
function getRoleLabel(role) {
  const map = {
    super_admin: '超级管理员',
    admin:       '管理员',
    operator:    '运营人员',
    viewer:      '只读用户',
  }
  return map[role] || role
}

function getRoleType(role) {
  const map = {
    super_admin: 'danger',
    admin:       'warning',
    operator:    'primary',
    viewer:      'info',
  }
  return map[role] || 'info'
}

// ==================== 修改密码 ====================
const pwdFormRef = ref(null)
const savingPwd  = ref(false)

const pwdForm = ref({
  old_password:     '',
  new_password:     '',
  confirm_password: '',
})

const pwdRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleChangePwd() {
  await pwdFormRef.value?.validate(async (valid) => {
    if (!valid) return
    savingPwd.value = true
    try {
      await adminAuthApi.changePwd?.({
        old_password: pwdForm.value.old_password,
        new_password: pwdForm.value.new_password,
      })
      ElMessage.success('密码修改成功，请重新登录')
      resetPwdForm()

      // 延迟退出登录
      setTimeout(() => {
        adminStore.logout()
        window.location.href = '/admin/login'
      }, 1500)
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '密码修改失败，请检查当前密码')
    } finally {
      savingPwd.value = false
    }
  })
}

function resetPwdForm() {
  pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
  pwdFormRef.value?.clearValidate()
}

// ==================== 系统信息 ====================
const techStack = [
  { name: '后端框架',   value: 'FastAPI (Python 3.11)' },
  { name: 'Agent 框架', value: 'LangGraph'              },
  { name: '向量数据库', value: 'Qdrant'                  },
  { name: '关系数据库', value: 'PostgreSQL 15'           },
  { name: '缓存',       value: 'Redis 7'                 },
  { name: '前端框架',   value: 'Vue3 + Vite'             },
  { name: 'UI 组件库',  value: 'Element Plus'            },
  { name: '图表库',     value: 'ECharts'                 },
  { name: '状态管理',   value: 'Pinia'                   },
  { name: 'Embedding',  value: 'bge-small-zh-v1.5'       },
  { name: '检索策略',   value: 'BM25(0.3) + Embedding(0.7)' },
  { name: '部署方式',   value: 'Docker 私有化部署'        },
]

const middlewareStatus = ref([
  { name: 'PostgreSQL', addr: '10.99.216.94:5432', connected: true  },
  { name: 'Redis',      addr: '10.99.216.94:6379', connected: true  },
  { name: 'Qdrant',     addr: '10.99.216.94:6333', connected: true  },
  { name: 'Embedding',  addr: '10.99.216.94:8001',   connected: true  },
])

// ==================== 工具函数 ====================
function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadBasicForm()
  loadChatForm()
  fetchAdmins()
})
</script>
<style scoped lang="scss">
.settings {
  min-height: 100%;
}

// 页面标题
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
      margin-bottom: 20px;
}

// 左侧导航
.settings-nav {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;

  .el-icon {
    font-size: 16px;
    color: #909399;
    flex-shrink: 0;
  }

  &:hover {
    background: #f5f7fa;
    color: #303133;

    .el-icon {
      color: #5b8af5;
    }
  }

  &.active {
    background: rgba(91, 138, 245, 0.1);
    color: #5b8af5;
    font-weight: 600;

    .el-icon {
      color: #5b8af5;
    }
  }
}

// 设置内容区
.settings-section {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 24px 28px;
  min-height: 500px;
}

// 区块标题
.section-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f5f7fa;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: #909399;
}

// 设置表单
.settings-form {
  max-width: 560px;
}

.form-unit {
  font-size: 13px;
  color: #909399;
  margin-left: 10px;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 5px;
}

// 管理员列表工具栏
.admins-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-bottom: 14px;
}

.text-time {
  font-size: 12px;
  color: #909399;
}

// 关于页面
.about-content {
  max-width: 660px;
}

.about-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 28px 20px;
  background: linear-gradient(
    135deg,
    rgba(91, 138, 245, 0.05),
    rgba(91, 138, 245, 0.02)
  );
  border-radius: 12px;
  margin-bottom: 20px;
  text-align: center;
}

.about-logo {
  width: 72px;
  height: 72px;
  filter: drop-shadow(0 4px 12px rgba(91, 138, 245, 0.3));
}

.about-name {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  letter-spacing: 1px;
}

.about-version {
  display: flex;
  align-items: center;
  gap: 8px;
}

.about-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.7;
  max-width: 480px;
}

// 技术栈网格
.tech-grid {
  margin-bottom: 8px;
}

.tech-item {
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 10px;
  transition: background 0.2s;

  &:hover {
    background: rgba(91, 138, 245, 0.06);
  }
}

.tech-name {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tech-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

// 中间件状态
.middleware-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.middleware-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: #ecf5ff;
  }
}

.mw-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mw-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.dot-online {
    background: #67c23a;
    box-shadow: 0 0 6px rgba(103, 194, 58, 0.5);
    animation: pulse-green 2s infinite;
  }

  &.dot-offline {
    background: #f56c6c;
    box-shadow: 0 0 6px rgba(245, 108, 108, 0.4);
  }
}

@keyframes pulse-green {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

.mw-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.mw-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mw-addr {
  font-size: 12px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

// 关于页面底部版权
.about-footer {
  text-align: center;
  padding: 16px 0;
  font-size: 12px;
  color: #c0c4cc;
  border-top: 1px solid #f5f7fa;
  margin-top: 8px;
}
</style>