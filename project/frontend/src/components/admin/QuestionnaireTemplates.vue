<template>
  <div class="questionnaire-templates">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>创建问卷模板
      </el-button>
    </div>

    <el-table :data="store.templates" v-loading="store.isLoading" style="width: 100%">
      <el-table-column label="问卷编码" prop="code" width="120" />
      <el-table-column label="问卷名称" prop="name" min-width="150" />
      <el-table-column label="题目数量" prop="question_count" width="100" align="center" />
      <el-table-column label="版本" prop="version" width="80" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
          <el-button 
            link 
            :type="row.is_active ? 'danger' : 'success'" 
            @click="toggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="问卷详情" width="800px" destroy-on-close>
      <div v-if="selectedTemplate" class="template-detail">
        <h3>{{ selectedTemplate.name }}</h3>
        <p class="description">{{ selectedTemplate.description }}</p>
        <div class="questions-list">
          <h4>题目列表 ({{ selectedTemplate.questions?.length || 0 }}题)</h4>
          <div v-for="(q, idx) in selectedTemplate.questions" :key="idx" class="question-item">
            <div class="question-text">{{ idx + 1 }}. {{ q.text || q.id }}</div>
            <div class="options">
              <span v-for="(opt, oidx) in q.options" :key="oidx" class="option">
                {{ opt.label || opt.id }}({{ opt.score }}分)
              </span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 创建问卷模板弹窗 -->
    <el-dialog v-model="createDialogVisible" title="创建问卷模板" width="900px" destroy-on-close>
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="问卷编码" prop="code">
          <el-input v-model="createForm.code" placeholder="请输入问卷编码，如: GAD-7" />
        </el-form-item>
        <el-form-item label="问卷名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入问卷名称" />
        </el-form-item>
        <el-form-item label="问卷描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入问卷描述" />
        </el-form-item>

        <!-- 题目编辑区域 -->
        <div class="questions-editor">
          <div class="questions-header">
            <h4>题目设置</h4>
            <el-button type="primary" size="small" @click="addQuestion">
              <el-icon><Plus /></el-icon>添加题目
            </el-button>
          </div>

          <div v-for="(question, qIdx) in createForm.questions" :key="qIdx" class="question-edit-item">
            <div class="question-header">
              <span class="question-number">题目 {{ qIdx + 1 }}</span>
              <el-button link type="danger" size="small" @click="removeQuestion(qIdx)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </div>
            <el-form-item :label="'题目文本'" :prop="'questions.' + qIdx + '.text'" :rules="{ required: true, message: '请输入题目文本', trigger: 'blur' }">
              <el-input v-model="question.text" placeholder="请输入题目文本" />
            </el-form-item>
            <el-form-item :label="'题目ID'" :prop="'questions.' + qIdx + '.id'" :rules="{ required: true, message: '请输入题目ID', trigger: 'blur' }">
              <el-input v-model="question.id" placeholder="如: q1, question_1" />
            </el-form-item>

            <!-- 选项编辑 -->
            <div class="options-editor">
              <div class="options-header">
                <span>选项设置</span>
                <el-button link type="primary" size="small" @click="addOption(qIdx)">
                  <el-icon><Plus /></el-icon>添加选项
                </el-button>
              </div>
              <div v-for="(option, oIdx) in question.options" :key="oIdx" class="option-edit-row">
                <el-input v-model="option.id" placeholder="选项值" size="small" style="width: 120px" />
                <el-input v-model="option.label" placeholder="选项文本" size="small" style="width: 200px; margin-left: 8px;" />
                <el-input-number v-model="option.score" :min="0" :max="100" size="small" style="margin-left: 8px;" placeholder="分数" />
                <el-button link type="danger" size="small" style="margin-left: 8px;" @click="removeOption(qIdx, oIdx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="isCreating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const store = useAdminQuestionnaireStore()
const detailDialogVisible = ref(false)
const selectedTemplate = ref(null)

// 创建弹窗相关
const createDialogVisible = ref(false)
const createFormRef = ref(null)
const isCreating = ref(false)

const createForm = reactive({
  code: '',
  name: '',
  description: '',
  questions: []
})

const createRules = {
  code: [{ required: true, message: '请输入问卷编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入问卷名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入问卷描述', trigger: 'blur' }]
}

const formatDate = (date) => {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

const viewDetail = async (row) => {
  const detail = await store.getTemplateDetail(row.code)
  selectedTemplate.value = detail
  detailDialogVisible.value = true
}

const toggleStatus = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}问卷"${row.name}"吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await store.updateTemplateStatus(row.code, !row.is_active)
    ElMessage.success(`问卷已${row.is_active ? '禁用' : '启用'}`)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}

// 创建问卷相关方法
const openCreateDialog = () => {
  createForm.code = ''
  createForm.name = ''
  createForm.description = ''
  createForm.questions = []
  createDialogVisible.value = true
}

const addQuestion = () => {
  createForm.questions.push({
    id: `q${createForm.questions.length + 1}`,
    text: '',
    options: [
      { id: '0', label: '没有', score: 0 },
      { id: '1', label: '轻度', score: 1 },
      { id: '2', label: '中度', score: 2 },
      { id: '3', label: '重度', score: 3 }
    ]
  })
}

const removeQuestion = (index) => {
  createForm.questions.splice(index, 1)
}

const addOption = (qIdx) => {
  createForm.questions[qIdx].options.push({
    id: String(createForm.questions[qIdx].options.length),
    label: '',
    score: 0
  })
}

const removeOption = (qIdx, oIdx) => {
  createForm.questions[qIdx].options.splice(oIdx, 1)
}

const submitCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    if (createForm.questions.length === 0) {
      ElMessage.warning('请至少添加一道题目')
      return
    }

    // 验证每道题至少有一个选项
    for (let i = 0; i < createForm.questions.length; i++) {
      if (!createForm.questions[i].options || createForm.questions[i].options.length === 0) {
        ElMessage.warning(`题目 ${i + 1} 至少需要有一个选项`)
        return
      }
    }

    isCreating.value = true
    try {
      await store.createTemplate({
        code: createForm.code,
        name: createForm.name,
        description: createForm.description,
        questions: createForm.questions
      })
      ElMessage.success('问卷模板创建成功')
      createDialogVisible.value = false
      store.fetchTemplates()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '创建失败')
    } finally {
      isCreating.value = false
    }
  })
}
</script>

<style scoped>
.questionnaire-templates { padding: 20px 0; }
.toolbar { margin-bottom: 20px; }
.template-detail h3 { margin: 0 0 12px 0; }
.description { color: #606266; margin-bottom: 20px; }
.questions-list h4 { margin: 0 0 16px 0; }
.question-item { 
  padding: 12px; 
  background: #f5f7fa; 
  border-radius: 8px; 
  margin-bottom: 12px; 
}
.question-text { font-weight: 500; margin-bottom: 8px; }
.options { display: flex; gap: 16px; flex-wrap: wrap; }
.option { font-size: 14px; color: #606266; }

/* 创建弹窗样式 */
.questions-editor { margin-top: 20px; border-top: 1px solid #e4e7ed; padding-top: 20px; }
.questions-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.questions-header h4 { margin: 0; }
.question-edit-item { 
  background: #f5f7fa; 
  padding: 16px; 
  border-radius: 8px; 
  margin-bottom: 16px; 
}
.question-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 12px; 
}
.question-number { font-weight: 500; color: #409eff; }
.options-editor { 
  background: #fff; 
  padding: 12px; 
  border-radius: 4px; 
  margin-top: 8px; 
}
.options-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 12px; 
  font-size: 14px; 
  color: #606266; 
}
.option-edit-row { 
  display: flex; 
  align-items: center; 
  margin-bottom: 8px; 
}
</style>
