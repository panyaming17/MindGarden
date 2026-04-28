<template>
  <div class="scoring-rules">
    <div class="toolbar">
      <div class="template-selector">
        <span>选择问卷：</span>
        <el-select v-model="selectedTemplate" placeholder="请选择问卷" @change="loadRules">
          <el-option v-for="t in store.templates" :key="t.code" :label="t.name" :value="t.code" />
        </el-select>
      </div>
      <el-button type="primary" @click="openCreateDialog" :disabled="!selectedTemplate">
        <el-icon><Plus /></el-icon>创建评分规则
      </el-button>
    </div>

    <div v-if="selectedTemplate && store.scoringRules.length > 0" class="rules-list">
      <div v-for="rule in store.scoringRules" :key="rule.id" class="rule-item">
        <div class="rule-header">
          <el-tag :type="getRuleTypeColor(rule.rule_type)">{{ getRuleTypeText(rule.rule_type) }}</el-tag>
          <span class="rule-priority">优先级: {{ rule.priority }}</span>
        </div>
        <div class="rule-config">
          <pre>{{ JSON.stringify(rule.rule_config, null, 2) }}</pre>
        </div>
        <div class="rule-actions">
          <el-button type="primary" size="small" @click="editRule(rule)">编辑</el-button>
        </div>
      </div>
    </div>

    <el-empty v-else-if="selectedTemplate" description="该问卷暂无评分规则" />
    <el-empty v-else description="请选择问卷查看评分规则" />

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑评分规则" width="600px">
      <el-form v-if="editingRule" :model="editForm" label-width="100px">
        <el-form-item label="修改原因">
          <el-input v-model="editForm.reason" type="textarea" rows="3" placeholder="请说明修改原因" />
        </el-form-item>
        <el-form-item label="规则配置">
          <el-input v-model="editForm.config" type="textarea" rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpdate">提交审核</el-button>
      </template>
    </el-dialog>

    <!-- 创建评分规则弹窗 -->
    <el-dialog v-model="createDialogVisible" title="创建评分规则" width="700px" destroy-on-close>
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="问卷模板" prop="template_code">
          <el-select v-model="createForm.template_code" placeholder="请选择问卷模板" style="width: 100%">
            <el-option v-for="t in store.templates" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则类型" prop="rule_type">
          <el-select v-model="createForm.rule_type" placeholder="请选择规则类型" style="width: 100%">
            <el-option label="等级规则" value="level" />
            <el-option label="建议规则" value="suggestion" />
            <el-option label="区间规则" value="interval" />
            <el-option label="预警规则" value="alert" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="createForm.priority" :min="1" :max="100" style="width: 100%" />
          <span class="form-tip">数字越小优先级越高</span>
        </el-form-item>

        <!-- 等级规则配置 -->
        <template v-if="createForm.rule_type === 'level'">
          <el-form-item label="等级配置">
            <div v-for="(level, idx) in createForm.rule_config.levels" :key="idx" class="config-row">
              <el-input v-model="level.name" placeholder="等级名称" size="small" style="width: 120px" />
              <el-input-number v-model="level.min_score" :min="0" placeholder="最低分" size="small" style="width: 100px; margin-left: 8px;" />
              <el-input-number v-model="level.max_score" :min="0" placeholder="最高分" size="small" style="width: 100px; margin-left: 8px;" />
              <el-button link type="danger" size="small" style="margin-left: 8px;" @click="removeLevel(idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button link type="primary" size="small" @click="addLevel">
              <el-icon><Plus /></el-icon>添加等级
            </el-button>
          </el-form-item>
        </template>

        <!-- 建议规则配置 -->
        <template v-if="createForm.rule_type === 'suggestion'">
          <el-form-item label="建议配置">
            <div v-for="(sugg, idx) in createForm.rule_config.suggestions" :key="idx" class="config-item">
              <div class="config-row">
                <el-input v-model="sugg.level" placeholder="适用等级" size="small" style="width: 120px" />
                <el-button link type="danger" size="small" style="margin-left: 8px;" @click="removeSuggestion(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-input v-model="sugg.text" type="textarea" :rows="2" placeholder="建议内容" size="small" style="margin-top: 8px;" />
            </div>
            <el-button link type="primary" size="small" @click="addSuggestion">
              <el-icon><Plus /></el-icon>添加建议
            </el-button>
          </el-form-item>
        </template>

        <!-- 区间规则配置 -->
        <template v-if="createForm.rule_type === 'interval'">
          <el-form-item label="区间配置">
            <div v-for="(interval, idx) in createForm.rule_config.intervals" :key="idx" class="config-row">
              <el-input-number v-model="interval.min" :min="0" placeholder="最小值" size="small" style="width: 100px" />
              <span style="margin: 0 8px;">-</span>
              <el-input-number v-model="interval.max" :min="0" placeholder="最大值" size="small" style="width: 100px" />
              <el-input v-model="interval.label" placeholder="标签" size="small" style="width: 120px; margin-left: 8px;" />
              <el-button link type="danger" size="small" style="margin-left: 8px;" @click="removeInterval(idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button link type="primary" size="small" @click="addInterval">
              <el-icon><Plus /></el-icon>添加区间
            </el-button>
          </el-form-item>
        </template>

        <!-- 预警规则配置 -->
        <template v-if="createForm.rule_type === 'alert'">
          <el-form-item label="预警阈值">
            <el-input-number v-model="createForm.rule_config.threshold" :min="0" placeholder="触发预警的分数阈值" style="width: 100%" />
          </el-form-item>
          <el-form-item label="预警级别">
            <el-select v-model="createForm.rule_config.alert_level" placeholder="请选择预警级别" style="width: 100%">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </el-form-item>
          <el-form-item label="预警消息">
            <el-input v-model="createForm.rule_config.message" type="textarea" :rows="3" placeholder="请输入预警消息内容" />
          </el-form-item>
        </template>

        <el-form-item label="规则说明">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入规则说明（可选）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="isCreating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const store = useAdminQuestionnaireStore()
const selectedTemplate = ref('')
const editDialogVisible = ref(false)
const editingRule = ref(null)
const editForm = ref({ reason: '', config: '' })

// 创建弹窗相关
const createDialogVisible = ref(false)
const createFormRef = ref(null)
const isCreating = ref(false)

const createForm = reactive({
  template_code: '',
  rule_type: 'level',
  priority: 10,
  rule_config: {},
  description: ''
})

const createRules = {
  template_code: [{ required: true, message: '请选择问卷模板', trigger: 'change' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  priority: [{ required: true, message: '请输入优先级', trigger: 'blur' }]
}

onMounted(() => {
  store.getTemplates()
})

const loadRules = () => {
  if (selectedTemplate.value) {
    store.getScoringRules(selectedTemplate.value)
  }
}

const getRuleTypeColor = (type) => {
  const map = { level: 'primary', suggestion: 'success', interval: 'warning', alert: 'danger' }
  return map[type] || 'info'
}

const getRuleTypeText = (type) => {
  const map = { level: '等级规则', suggestion: '建议规则', interval: '区间规则', alert: '预警规则' }
  return map[type] || type
}

const editRule = (rule) => {
  editingRule.value = rule
  editForm.value = {
    reason: '',
    config: JSON.stringify(rule.rule_config, null, 2)
  }
  editDialogVisible.value = true
}

const submitUpdate = async () => {
  try {
    const config = JSON.parse(editForm.value.config)
    await store.requestRuleUpdate(editingRule.value.id, config, editForm.value.reason)
    ElMessage.success('修改申请已提交，等待超级管理员审核')
    editDialogVisible.value = false
  } catch (error) {
    ElMessage.error('提交失败：' + error.message)
  }
}

// 创建评分规则相关方法
const openCreateDialog = () => {
  createForm.template_code = selectedTemplate.value || ''
  createForm.rule_type = 'level'
  createForm.priority = 10
  createForm.description = ''
  createForm.rule_config = { levels: [] }
  createDialogVisible.value = true
}

// 等级规则相关
const addLevel = () => {
  if (!createForm.rule_config.levels) {
    createForm.rule_config.levels = []
  }
  createForm.rule_config.levels.push({
    name: '',
    min_score: 0,
    max_score: 0
  })
}

const removeLevel = (idx) => {
  createForm.rule_config.levels.splice(idx, 1)
}

// 建议规则相关
const addSuggestion = () => {
  if (!createForm.rule_config.suggestions) {
    createForm.rule_config.suggestions = []
  }
  createForm.rule_config.suggestions.push({
    level: '',
    text: ''
  })
}

const removeSuggestion = (idx) => {
  createForm.rule_config.suggestions.splice(idx, 1)
}

// 区间规则相关
const addInterval = () => {
  if (!createForm.rule_config.intervals) {
    createForm.rule_config.intervals = []
  }
  createForm.rule_config.intervals.push({
    min: 0,
    max: 0,
    label: ''
  })
}

const removeInterval = (idx) => {
  createForm.rule_config.intervals.splice(idx, 1)
}

// 监听规则类型变化，初始化对应的配置
const initRuleConfig = (type) => {
  switch (type) {
    case 'level':
      createForm.rule_config = { levels: [] }
      break
    case 'suggestion':
      createForm.rule_config = { suggestions: [] }
      break
    case 'interval':
      createForm.rule_config = { intervals: [] }
      break
    case 'alert':
      createForm.rule_config = { threshold: 0, alert_level: 'medium', message: '' }
      break
    default:
      createForm.rule_config = {}
  }
}

// 监听规则类型变化
import { watch } from 'vue'
watch(() => createForm.rule_type, (newType) => {
  initRuleConfig(newType)
})

const submitCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    // 验证规则配置
    const config = createForm.rule_config
    if (createForm.rule_type === 'level' && (!config.levels || config.levels.length === 0)) {
      ElMessage.warning('请至少添加一个等级')
      return
    }
    if (createForm.rule_type === 'suggestion' && (!config.suggestions || config.suggestions.length === 0)) {
      ElMessage.warning('请至少添加一条建议')
      return
    }
    if (createForm.rule_type === 'interval' && (!config.intervals || config.intervals.length === 0)) {
      ElMessage.warning('请至少添加一个区间')
      return
    }
    if (createForm.rule_type === 'alert' && config.threshold === undefined) {
      ElMessage.warning('请输入预警阈值')
      return
    }

    isCreating.value = true
    try {
      await store.createScoringRule({
        template_code: createForm.template_code,
        rule_type: createForm.rule_type,
        priority: createForm.priority,
        rule_config: createForm.rule_config,
        description: createForm.description
      })
      ElMessage.success('评分规则创建成功')
      createDialogVisible.value = false
      // 刷新当前问卷的规则列表
      if (selectedTemplate.value === createForm.template_code) {
        store.getScoringRules(selectedTemplate.value)
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '创建失败')
    } finally {
      isCreating.value = false
    }
  })
}
</script>

<style scoped>
.scoring-rules { padding: 20px 0; }
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.template-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.rule-item {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.rule-priority {
  font-size: 14px;
  color: #909399;
}
.rule-config pre {
  background: white;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0 0 12px 0;
}
.rule-actions {
  display: flex;
  justify-content: flex-end;
}

/* 创建弹窗样式 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
.config-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.config-item {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}
</style>
