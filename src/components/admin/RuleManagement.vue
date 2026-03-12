<template>
  <div class="rule-management">
    <!-- 搜索和新增按钮 -->
    <div class="rule-filters">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="按规则名称搜索"
          class="search-input"
          @input="handleSearch"
        >
        <select v-model="ruleType" class="type-select" @change="handleSearch">
          <option value="">全部类型</option>
          <option value="cbt">CBT</option>
          <option value="tcm">中医</option>
        </select>
        <button class="add-button" @click="openAddDialog">新增规则</button>
      </div>
    </div>
    
    <!-- 规则列表 -->
    <div class="rule-list">
      <table class="rule-table">
        <thead>
          <tr>
            <th>类型</th>
            <th>名称</th>
            <th>版本</th>
            <th>状态</th>
            <th>更新时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in rules" :key="rule.id">
            <td>{{ getTypeText(rule.type) }}</td>
            <td>{{ rule.name }}</td>
            <td>{{ rule.version }}</td>
            <td>{{ rule.is_active ? '激活' : '禁用' }}</td>
            <td>{{ formatDate(rule.updated_at) }}</td>
            <td class="action-buttons">
              <button class="edit-button" @click="editRule(rule)">编辑</button>
              <button class="delete-button" @click="deleteRule(rule)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 空状态 -->
      <div v-if="rules.length === 0" class="empty-state">
        暂无规则数据
      </div>
    </div>
    
    <!-- 分页 -->
    <div class="pagination">
      <button 
        class="page-button" 
        @click="changePage(page - 1)"
        :disabled="page === 1"
      >
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} 页，共 {{ totalPages }} 页
      </span>
      <button 
        class="page-button" 
        @click="changePage(page + 1)"
        :disabled="page === totalPages"
      >
        下一页
      </button>
    </div>
    
    <!-- 新增/编辑规则对话框 -->
    <div v-if="isDialogVisible" class="dialog-overlay" @click="closeDialog">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h3>{{ isEditing ? '编辑规则' : '新增规则' }}</h3>
          <button class="close-button" @click="closeDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>类型</label>
            <select v-model="ruleForm.type" class="form-select" @change="handleTypeChange">
              <option value="cbt">CBT</option>
              <option value="tcm">中医</option>
            </select>
          </div>
          <div class="form-group">
            <label>名称</label>
            <input 
              type="text" 
              v-model="ruleForm.name" 
              class="form-input"
              placeholder="请输入规则名称"
            >
          </div>
          <div class="form-group">
            <label>版本</label>
            <input 
              type="text" 
              v-model="ruleForm.version" 
              class="form-input"
              placeholder="请输入版本号"
            >
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="ruleForm.is_active" class="form-select">
              <option value="true">激活</option>
              <option value="false">禁用</option>
            </select>
          </div>
          <div class="form-group">
            <label>内容</label>
            <div class="json-editor">
              <textarea 
                v-model="ruleForm.content" 
                class="json-textarea"
                placeholder="请输入JSON格式的规则内容"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cancel-button" @click="closeDialog">取消</button>
          <button class="save-button" @click="saveRule">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth.js'

// 响应式数据
const rules = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const searchQuery = ref('')
const ruleType = ref('')
const isDialogVisible = ref(false)
const isEditing = ref(false)
const currentRule = ref(null)

// 规则表单数据
const ruleForm = ref({
  type: 'cbt',
  name: '',
  version: '',
  is_active: true,
  content: ''
})

// API基础URL
const API_BASE_URL = 'http://localhost:8001'

// 获取auth store
const authStore = useAuthStore()

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(total.value / perPage.value)
})

// 获取类型文本
const getTypeText = (type) => {
  const typeMap = {
    'cbt': 'CBT',
    'tcm': '中医'
  }
  return typeMap[type] || type
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 加载规则列表
const loadRules = async () => {
  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/admin/rules?type=${ruleType.value}&search=${encodeURIComponent(searchQuery.value)}&page=${page.value}&per_page=${perPage.value}`
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('获取规则列表失败')
    }

    const data = await response.json()
    rules.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('Error loading rules:', error)
    ElMessage.error(error.message || '获取规则列表失败')
    // 模拟数据
    rules.value = [
      {
        id: 1,
        type: 'cbt',
        name: '认知重构',
        content: {
          strategy: '认知重构',
          description: '识别并挑战负面思维模式，用更合理的思维替代',
          examples: [
            '识别自动思维："我永远做不好任何事情"',
            '寻找证据："我之前成功完成了项目A和任务B"',
            '替换为合理思维："我虽然遇到了困难，但我有能力克服它"'
          ]
        },
        version: '1.0',
        is_active: true,
        created_at: '2026-03-05T00:00:00',
        updated_at: '2026-03-05T00:00:00'
      },
      {
        id: 6,
        type: 'tcm',
        name: '肝气郁结',
        content: {
          "dominant_emotion": "思",
          "keywords": ["思考", "思虑", "沉思", "冥想", "琢磨"],
          "affected_zang": "脾",
          "common_patterns": ["脾虚", "心脾两虚", "脾胃不和"],
          "inhibiting_emotion": "怒",  
          "behavioral_adjustment": ["听角音（属木）音乐", "轻度运动", "户外活动"],
          "other_suggestions": ["饮食规律", "避免过度思虑"]
        },
        version: '1.0',
        is_active: true,
        created_at: '2026-03-05T00:00:00',
        updated_at: '2026-03-05T00:00:00'
      }
    ]
    total.value = 2
  }
}

// 处理搜索
const handleSearch = () => {
  page.value = 1
  loadRules()
}

// 切换页码
const changePage = (newPage) => {
  if (newPage < 1 || newPage > totalPages.value) {
    return
  }
  page.value = newPage
  loadRules()
}

// 打开新增对话框
const openAddDialog = () => {
  isEditing.value = false
  currentRule.value = null
  ruleForm.value = {
    type: 'cbt',
    name: '',
    version: '',
    is_active: true,
    content: ''
  }
  handleTypeChange()
  isDialogVisible.value = true
}

// 监听类型变化，设置默认内容模板
const handleTypeChange = () => {
  if (ruleForm.value.type === 'tcm') {
    ruleForm.value.content = JSON.stringify({
      "keywords": [],
      "affected_zang": "",
      "common_patterns": [],
      "dominant_emotion": "",
      "other_suggestions": [],
      "inhibiting_emotion": "",
      "behavioral_adjustment": []
    }, null, 2)
  } else if (ruleForm.value.type === 'cbt') {
    ruleForm.value.content = JSON.stringify({
        "examples": [],
        "strategy": "",
        "description": ""
    }, null, 2)
  }
}

// 编辑规则
const editRule = (rule) => {
  isEditing.value = true
  currentRule.value = rule
  ruleForm.value = {
    type: rule.type,
    name: rule.name,
    version: rule.version,
    is_active: rule.is_active,
    content: typeof rule.content === 'object' ? JSON.stringify(rule.content, null, 2) : rule.content
  }
  isDialogVisible.value = true
}

// 关闭对话框
const closeDialog = () => {
  isDialogVisible.value = false
  currentRule.value = null
}

// 保存规则
const saveRule = async () => {
  // 验证表单
  if (!ruleForm.value.name || !ruleForm.value.version || !ruleForm.value.content) {
    ElMessage.error('请填写完整的规则信息')
    return
  }

  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    let url, method
    if (isEditing.value && currentRule.value) {
      url = `${API_BASE_URL}/api/admin/rules/${currentRule.value.id}`
      method = 'PUT'
    } else {
      url = `${API_BASE_URL}/api/admin/rules`
      method = 'POST'
    }

    // 处理content字段，确保它是对象
    let ruleData = { ...ruleForm.value }
    try {
      // 尝试解析content为JSON对象
      ruleData.content = JSON.parse(ruleForm.value.content)
    } catch (parseError) {
      // 如果解析失败，保持原样
      console.error('Failed to parse content as JSON:', parseError)
    }
    
    // 处理is_active字段，确保它是布尔值
    ruleData.is_active = ruleForm.value.is_active === 'true' || ruleForm.value.is_active === true

    const response = await fetch(url, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(ruleData)
    })

    if (!response.ok) {
      throw new Error(isEditing.value ? '更新规则失败' : '新增规则失败')
    }

    ElMessage.success(isEditing.value ? '规则更新成功' : '规则新增成功')
    closeDialog()
    loadRules()
  } catch (error) {
    console.error('Error saving rule:', error)
    ElMessage.error(error.message || '保存规则失败')
  }
}

// 删除规则
const deleteRule = async (rule) => {
  if (!confirm('确定要删除该规则吗？')) return

  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/admin/rules/${rule.id}`
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('删除规则失败')
    }

    ElMessage.success('规则删除成功')
    loadRules()
  } catch (error) {
    console.error('Error deleting rule:', error)
    ElMessage.error(error.message || '删除规则失败')
  }
}

// 初始化
onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.rule-management {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

/* 搜索和筛选 */
.rule-filters {
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.type-select {
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.add-button {
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.add-button:hover {
  background-color: #218838;
}

/* 规则列表 */
.rule-list {
  margin-bottom: 20px;
}

.rule-table {
  width: 100%;
  border-collapse: collapse;
}

.rule-table th,
.rule-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.rule-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.rule-table tr:hover {
  background-color: #f8f9fa;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.edit-button,
.delete-button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
}

.edit-button {
  background-color: #007bff;
  color: white;
}

.edit-button:hover {
  background-color: #0069d9;
}

.delete-button {
  background-color: #dc3545;
  color: white;
}

.delete-button:hover {
  background-color: #c82333;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  font-size: 16px;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.page-button {
  padding: 8px 16px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-button:hover:not(:disabled) {
  background-color: #e2e6ea;
  border-color: #dae0e5;
}

.page-button:disabled {
  background-color: #f8f9fa;
  border-color: #dee2e6;
  color: #6c757d;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6c757d;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.close-button:hover {
  background-color: #f8f9fa;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.json-editor {
  margin-top: 5px;
}

.json-textarea {
  width: 100%;
  min-height: 200px;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  font-family: monospace;
  resize: vertical;
}

.dialog-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #f8f9fa;
}

.cancel-button,
.save-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
}

.cancel-button {
  background-color: #6c757d;
  color: white;
}

.cancel-button:hover {
  background-color: #5a6268;
}

.save-button {
  background-color: #007bff;
  color: white;
}

.save-button:hover {
  background-color: #0069d9;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rule-management {
    padding: 15px;
  }
  
  .search-box {
    flex-direction: column;
    align-items: stretch;
  }
  
  .rule-table th,
  .rule-table td {
    padding: 8px;
    font-size: 14px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 5px;
  }
  
  .edit-button,
  .delete-button {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .dialog-content {
    width: 95%;
  }
  
  .dialog-header,
  .dialog-body,
  .dialog-footer {
    padding: 15px;
  }
}
</style>