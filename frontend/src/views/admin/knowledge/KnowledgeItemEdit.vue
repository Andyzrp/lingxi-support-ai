<template>
  <el-drawer
    v-model="visible"
    :title="isEdit ? '编辑知识条目' : '新增知识条目'"
    size="800px"
    direction="rtl"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div class="edit-wrap">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <!-- 基础设置 -->
        <div class="section-block">
          <div class="section-title">基础设置</div>

          <el-form-item label="所属类目" prop="category">
            <el-select
              v-model="form.category"
              placeholder="请选择类目"
              allow-create
              filterable
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="c in categoryList"
                :key="c"
                :label="c"
                :value="c"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="标签">
            <el-select
              v-model="form.tags"
              multiple
              filterable
              allow-create
              placeholder="输入标签后回车确认"
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="t in commonTags"
                :key="t"
                :label="t"
                :value="t"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 问法设置 -->
        <div class="section-block">
          <div class="section-title">问法设置</div>

          <el-form-item label="标准问题（知识标题）" prop="title" required>
            <el-input
              v-model="form.title"
              placeholder="请输入标准问题，建议50字以内"
              maxlength="120"
              show-word-limit
              clearable
            />
            <div class="field-hint">建议问题50字以内，超长会影响机器人推荐的准确性</div>
          </el-form-item>

          <el-form-item label="相似问法">
            <div class="similar-list">
              <div
                v-for="(q, index) in form.similar_questions"
                :key="index"
                class="similar-item"
              >
                <el-input
                  v-model="form.similar_questions[index]"
                  :placeholder="`相似问法 ${index + 1}`"
                  maxlength="200"
                  show-word-limit
                  clearable
                />
                <el-button
                  text
                  type="danger"
                  :icon="Delete"
                  @click="removeSimilar(index)"
                />
              </div>

              <el-button
                class="add-btn"
                :icon="Plus"
                @click="addSimilar"
                :disabled="form.similar_questions.length >= 20"
              >
                添加相似问法
              </el-button>
            </div>
          </el-form-item>
        </div>

        <!-- 回答设置 -->
        <div class="section-block">
          <div class="section-title">回答设置</div>

          <el-form-item label="答案类型" required>
            <el-radio-group v-model="form.answer_type">
              <el-radio value="text">纯文本</el-radio>
              <el-radio value="html">富文本（HTML）</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 纯文本编辑器 -->
          <el-form-item
            v-show="form.answer_type === 'text'"
            label="答案内容"
            prop="answer_content"
            required
          >
            <el-input
              v-model="form.answer_content"
              type="textarea"
              :rows="8"
              placeholder="请输入答案内容"
              maxlength="5000"
              show-word-limit
            />
          </el-form-item>

          <!-- 富文本编辑器 -->
          <el-form-item
            v-show="form.answer_type === 'html'"
            label="答案内容"
            prop="answer_content"
            required
          >
            <div class="rich-editor-wrap">
              <div class="rich-toolbar">
                <el-button-group size="small">
                  <el-button @click="execCmd('bold')" title="加粗"><b>B</b></el-button>
                  <el-button @click="execCmd('italic')" title="斜体"><i>I</i></el-button>
                  <el-button @click="execCmd('underline')" title="下划线"><u>U</u></el-button>
                </el-button-group>
                <el-divider direction="vertical" />
                <el-button-group size="small">
                  <el-button @click="execCmd('insertUnorderedList')" title="无序列表">• 列表</el-button>
                  <el-button @click="execCmd('insertOrderedList')" title="有序列表">1. 列表</el-button>
                </el-button-group>
                <el-divider direction="vertical" />
                <el-select v-model="fontSize" size="small" style="width: 80px" @change="execCmd('fontSize', fontSize)">
                  <el-option label="小" value="2" />
                  <el-option label="中" value="3" />
                  <el-option label="大" value="5" />
                  <el-option label="特大" value="7" />
                </el-select>
                <el-button size="small" @click="insertLink" title="插入链接">
                  <LinkIcon />
                </el-button>
                <el-button size="small" @click="execCmd('removeFormat')" title="清除格式">
                  清除
                </el-button>
              </div>
              <div
                ref="editorRef"
                class="rich-editor"
                contenteditable="true"
                @input="handleEditorInput"
                @paste="handlePaste"
                placeholder="请输入富文本答案内容，支持加粗、列表、链接等格式..."
              />
            </div>
            <div class="field-hint">支持富文本格式，粘贴内容时会自动清除外部样式</div>
          </el-form-item>
        </div>

        <!-- 状态 -->
        <div class="section-block">
          <el-form-item label="状态">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
              active-text="启用"
              inactive-text="停用"
            />
          </el-form-item>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '立即创建' }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus, Link as LinkIcon } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/admin'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, default: null },
  kbId: { type: Number, required: true },
  categoryList: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const isEdit = computed(() => !!props.item?.id)

const formRef = ref(null)
const editorRef = ref(null)
const submitting = ref(false)
const fontSize = ref('3')

const commonTags = ['退款', '物流', '订单', '换货', '发票', '积分', '优惠券', '售后', '保修', '配送']

const form = reactive({
  title: '',
  category: '',
  tags: [],
  answer_type: 'text',
  answer_content: '',
  similar_questions: [],
  status: 1,
})

// 保存的原始HTML内容（弹窗打开时初始化）
let savedHtmlContent = ''

// 当弹窗打开时，强制重置并填充表单数据
watch(visible, (newVal) => {
  if (newVal && props.item) {
    form.title = props.item.title || ''
    form.category = props.item.category || ''

    const tagsVal = props.item.tags
    if (typeof tagsVal === 'string' && tagsVal) {
      form.tags = tagsVal.split(',').map(t => t.trim()).filter(t => t)
    } else if (Array.isArray(tagsVal)) {
      form.tags = [...tagsVal]
    } else if (tagsVal && typeof tagsVal === 'object' && Array.isArray(tagsVal.tags)) {
      form.tags = [...tagsVal.tags]
    } else {
      form.tags = []
    }

    form.answer_type = (props.item.answer_type === 1 || props.item.answer_type === 'html') ? 'html' : 'text'
    form.answer_content = props.item.answer || ''

    const sqVal = props.item.similar_questions
    if (Array.isArray(sqVal)) {
      form.similar_questions = sqVal.map(q => typeof q === 'string' ? q : (q.question || '')).filter(q => q.trim())
    } else {
      form.similar_questions = []
    }

    form.status = props.item.status ?? 1

    // 打开时保存原始HTML内容
    if (form.answer_type === 'html') {
      savedHtmlContent = props.item.answer || ''
    } else {
      savedHtmlContent = ''
    }

    nextTick(() => {
      if (form.answer_type === 'html' && editorRef.value) {
        editorRef.value.innerHTML = savedHtmlContent || ''
      } else if (editorRef.value) {
        editorRef.value.innerHTML = ''
      }
    })
  } else if (!newVal) {
    // 弹窗关闭时重置表单
    form.title = ''
    form.category = ''
    form.tags = []
    form.answer_type = 'text'
    form.answer_content = ''
    form.similar_questions = []
    form.status = 1
    if (editorRef.value) editorRef.value.innerHTML = ''
  }
}, { immediate: true })

watch(
  () => props.item,
  (val) => {
    if (!val) return

    form.title = val.title || ''
    form.category = val.category || ''

    const tagsVal = val.tags
    if (typeof tagsVal === 'string' && tagsVal) {
      form.tags = tagsVal.split(',').map(t => t.trim()).filter(t => t)
    } else if (Array.isArray(tagsVal)) {
      form.tags = [...tagsVal]
    } else if (tagsVal && typeof tagsVal === 'object' && Array.isArray(tagsVal.tags)) {
      form.tags = [...tagsVal.tags]
    } else {
      form.tags = []
    }

    form.answer_type = (val.answer_type === 1 || val.answer_type === 'html') ? 'html' : 'text'
    form.answer_content = val.answer || ''

    const sqVal = val.similar_questions
    if (Array.isArray(sqVal)) {
      form.similar_questions = sqVal.map(q => typeof q === 'string' ? q : (q.question || '')).filter(q => q.trim())
    } else {
      form.similar_questions = []
    }

    form.status = val.status ?? 1

    nextTick(() => {
      if (form.answer_type === 'html' && editorRef.value) {
        editorRef.value.innerHTML = form.answer_content || ''
      } else if (editorRef.value) {
        editorRef.value.innerHTML = ''
      }
    })
  },
  { immediate: true, deep: true }
)

// 监听答案类型切换
watch(() => form.answer_type, (newType, oldType) => {
  if (!editorRef.value) return

  if (newType === 'text' && oldType === 'html') {
    // HTML转纯文本：保存HTML内容，提取纯文本
    savedHtmlContent = editorRef.value.innerHTML || form.answer_content
    const temp = document.createElement('div')
    temp.innerHTML = savedHtmlContent
    form.answer_content = temp.textContent || temp.innerText || savedHtmlContent
  } else if (newType === 'html' && oldType === 'text') {
    // 纯文本转HTML：恢复HTML内容
    if (savedHtmlContent) {
      editorRef.value.innerHTML = savedHtmlContent
      form.answer_content = savedHtmlContent
    } else {
      const text = form.answer_content.trim()
      if (text && !text.startsWith('<')) {
        const html = `<p>${text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')}</p>`
        editorRef.value.innerHTML = html
        form.answer_content = html
      } else if (text) {
        editorRef.value.innerHTML = text
        form.answer_content = text
      }
    }
  }
})

const rules = {
  title: [
    { required: true, message: '请输入标准问题', trigger: 'blur' },
    { max: 120, message: '不超过120个字符', trigger: 'blur' },
  ],
  answer_content: [
    { required: true, message: '请输入答案内容', trigger: 'blur' },
  ],
}

function addSimilar() {
  form.similar_questions.push('')
}

function removeSimilar(index) {
  form.similar_questions.splice(index, 1)
}

function execCmd(cmd, value) {
  document.execCommand(cmd, false, value)
  editorRef.value?.focus()
}

function insertLink() {
  const url = prompt('请输入链接地址：')
  if (url) {
    document.execCommand('createLink', false, url)
    editorRef.value?.focus()
  }
}

function handleEditorInput() {
  form.answer_content = editorRef.value?.innerHTML || ''
}

function handlePaste(e) {
  e.preventDefault()
  const text = e.clipboardData.getData('text/html') || e.clipboardData.getData('text/plain')
  document.execCommand('insertHTML', false, text)
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  submitting.value = true

  const payload = {
    title: form.title.trim(),
    category: form.category || null,
    tags: form.tags.join(','),
    answer: form.answer_type === 'html'
      ? (editorRef.value?.innerHTML || form.answer_content)
      : form.answer_content.trim(),
    answer_type: form.answer_type === 'html' ? 1 : 0,
    similar_questions: form.similar_questions.filter(q => q.trim()),
    status: form.status,
  }

  try {
    if (isEdit.value) {
      await knowledgeApi.updateItem(props.item.id, payload)
      ElMessage.success('修改成功')
    } else {
      await knowledgeApi.createItem(props.kbId, payload)
      ElMessage.success('创建成功')
    }
    emit('saved')
    visible.value = false
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

function handleClosed() {
  form.title = ''
  form.category = ''
  form.tags = []
  form.answer_type = 'text'
  form.answer_content = ''
  form.similar_questions = []
  form.status = 1
  fontSize.value = '3'
  if (editorRef.value) editorRef.value.innerHTML = ''
}
</script>

<style scoped lang="scss">
.edit-wrap {
  padding: 0 20px 20px;
}

.section-block {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.similar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-btn {
  border: 1px dashed #d9d9d9;
  color: #5b8af5;
  background: transparent;

  &:hover {
    border-color: #5b8af5;
  }

  &:disabled {
    color: #c0c4cc;
    border-color: #e4e7ed;
  }
}

.rich-editor-wrap {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.rich-toolbar {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
  gap: 4px;
}

.rich-editor {
  min-height: 220px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  outline: none;

  &:empty::before {
    content: attr(placeholder);
    color: #c0c4cc;
  }

  :deep(a) {
    color: #5b8af5;
    text-decoration: underline;
  }

  :deep(ul), :deep(ol) {
    padding-left: 24px;
    margin: 4px 0;
  }

  :deep(p) {
    margin: 6px 0;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
