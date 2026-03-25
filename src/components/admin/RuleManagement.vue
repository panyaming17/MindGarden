<template>
  <div class="rule-management">
    <!-- 搜索和新增按钮 -->
    <div class="rule-filters">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="按策略内容搜索"
          class="search-input"
          @input="handleSearch"
        >
        <select v-model="filters" class="type-select" @change="handleSearch">
          <option value="">全部</option>
          <option value="cbt">CBT</option>
          <option value="tcm">中医</option>
        </select>
        <button class="add-button" @click="openAddDialog">新增策略</button>
      </div>
    </div>
    
    <!-- 规则列表 -->
    <div class="rule-list">
      <table class="rule-table">
        <thead>
          <tr>
            <th>序号</th>
            <th>情志强度</th>
            <th>情志快感度</th>
            <th>情志紧张度</th>
            <th>情志复杂度</th>
            <th>融合模式</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(strategy, index) in strategies" :key="strategy.id" :class="{ 'new-strategy-row': newStrategies.has(strategy.id), 'updated-strategy-row': updatedStrategies.has(strategy.id) }">
            <td>{{ index + 1 }}</td>
            <td>{{ strategy.intensity_level }}</td>
            <td>{{ strategy.hedonic }}</td>
            <td>{{ strategy.tension }}</td>
            <td>{{ strategy.complexity }}</td>
            <td>{{ formatFusionMode(strategy.fusion_mode) }}</td>
            <td>{{ formatDate(strategy.created_at) }}</td>
            <td class="action-buttons">
              <button class="edit-button" @click="editRule(strategy)">编辑</button>
              <button class="delete-button" @click="deleteRule(strategy)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 空状态 -->
      <div v-if="strategies.length === 0" class="empty-state">
        暂无策略数据
      </div>
    </div>
    

    
    <!-- 新增/编辑规则对话框 -->
    <div v-if="isDialogVisible" class="dialog-overlay" @click="closeDialog">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h3>{{ isEditing ? '编辑策略' : '新增策略' }}</h3>
          <button class="close-button" @click="closeDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>情志强度</label>
            <select 
              v-model="strategyForm.intensity_level" 
              class="form-select"
            >
              <option value="">请选择情志强度</option>
              <option value="高">高</option>
              <option value="中">中</option>
              <option value="低">低</option>
            </select>
          </div>
          <div class="form-group">
            <label>情志快感度</label>
            <select 
              v-model="strategyForm.hedonic" 
              class="form-select"
            >
              <option value="">请选择情志快感度</option>
              <option value="负性">负性</option>
              <option value="正性">正性</option>
              <option value="中性">中性</option>
            </select>
          </div>
          <div class="form-group">
            <label>情志紧张度</label>
            <select 
              v-model="strategyForm.tension" 
              class="form-select"
            >
              <option value="">请选择情志紧张度</option>
              <option value="高">高</option>
              <option value="中">中</option>
              <option value="低">低</option>
            </select>
          </div>
          <div class="form-group">
            <label>情志复杂度</label>
            <select 
              v-model="strategyForm.complexity" 
              class="form-select"
            >
              <option value="">请选择情志复杂度</option>
              <option value="简单">简单</option>
              <option value="复杂">复杂</option>
            </select>
          </div>
          <div class="form-group">
            <label>融合模式</label>
            <select 
              v-model="strategyForm.fusion_mode" 
              class="form-select"
            >
              <option value="">请选择融合模式</option>
              <option value="CBT">认知行为疗法</option>
              <option value="中医">中医情志疗法</option>
              <option value="cbt_main_tcm_aux">认知行为疗法为主，中医情志疗法为辅</option>
              <option value="tcm_main_cbt_aux">中医情志疗法为主，认知行为疗法为辅</option>
              <option value="tcm_first_then_cbt">先中医情志疗法后认知行为疗法</option>
              <option value="cbt_first_then_tcm">先认知行为疗法后中医情志疗法</option>
              <option value="integrated_cbt_tcm">认知行为疗法与中医情志疗法融合</option>
            </select>
          </div>
          <div class="form-group">
            <label>CBT技术</label>
            <input 
              type="text" 
              v-model="strategyForm.cbt_techniques" 
              class="form-input"
              placeholder="请输入CBT技术"
            >
          </div>
          <div class="form-group">
            <label>中医方法</label>
            <input 
              type="text" 
              v-model="strategyForm.tcm_methods" 
              class="form-input"
              placeholder="请输入中医方法"
            >
          </div>
          <div class="form-group">
            <label>策略内容</label>
            <textarea 
              v-model="strategyForm.strategy_content" 
              class="form-textarea"
              placeholder="请输入策略内容"
            ></textarea>
          </div>
          <div class="form-group">
            <label>示例</label>
            <textarea 
              v-model="strategyForm.example" 
              class="form-textarea"
              placeholder="请输入示例"
            ></textarea>
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
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth.js'

// 响应式数据
const strategies = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const searchQuery = ref('')
const filters = ref('')
const isDialogVisible = ref(false)
const isEditing = ref(false)
const currentStrategy = ref(null)
const newStrategies = ref(new Set())
const updatedStrategies = ref(new Set())

// 策略表单数据
const strategyForm = ref({
  intensity_level: '',
  hedonic: '',
  tension: '',
  complexity: '',
  fusion_mode: '',
  cbt_techniques: '',
  tcm_methods: '',
  strategy_content: '',
  example: ''
})

// 监听融合模式变化，生成策略内容模板
watch(() => strategyForm.value.fusion_mode, (newValue) => {
  if (newValue) {
    switch (newValue) {
      case '中医':
      case 'tcm':
        strategyForm.value.strategy_content = '【中医情志疗法】';
        break;
      case 'CBT':
      case 'cbt':
        strategyForm.value.strategy_content = '【CBT技术】';
        break;
      case 'CBT+中医':
      case 'cbt_tcm':
        strategyForm.value.strategy_content = '【CBT技术】\n【中医情志疗法】';
        break;
      case 'cbt_main_tcm_aux':
        strategyForm.value.strategy_content = '【CBT为主】\n【中医情志疗法为辅】';
        break;
      case 'tcm_main_cbt_aux':
        strategyForm.value.strategy_content = '【中医情志疗法为主】\n【CBT为辅】';
        break;
      case 'tcm_first_then_cbt':
        strategyForm.value.strategy_content = '先【中医情志疗法】\n后【认知行为疗法】';
        break;
      case 'cbt_first_then_tcm':
        strategyForm.value.strategy_content = '先【认知行为疗法】\n后【中医情志疗法】';
        break;
      case 'integrated_cbt_tcm':
        strategyForm.value.strategy_content = '【CBT与中医情志疗法融合】';
        break;
      default:
        strategyForm.value.strategy_content = '';
    }
  } else {
    strategyForm.value.strategy_content = '';
  }
})

// API基础URL
const API_BASE_URL = 'http://localhost:8000'

// 获取auth store
const authStore = useAuthStore()

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(total.value / size.value)
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 转换融合模式为中文显示
const formatFusionMode = (fusionMode) => {
  const fusionModeMap = {
    'cbt': '认知行为疗法',
    'tcm': '中医情志疗法',
    '中医': '中医情志疗法',
    'CBT': '认知行为疗法',
    'CBT+中医': '认知行为疗法+中医情志疗法',
    'cbt_tcm': '认知行为疗法+中医情志疗法',
    '中医认知行为疗法': '中医情志疗法',
    'cbt_main_tcm_aux': '认知行为疗法为主，中医情志疗法为辅',
    'tcm_main_cbt_aux': '中医情志疗法为主，认知行为疗法为辅',
    'tcm_first_then_cbt': '先中医情志疗法，后认知行为疗法',
    'cbt_first_then_tcm': '先认知行为疗法，后中医情志疗法',
    'integrated_cbt_tcm': '认知行为疗法+中医情志疗法融合'
  }
  return fusionModeMap[fusionMode] || fusionMode
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/v1/admin/strategies?size=1000&filters=${encodeURIComponent(filters.value)}`
    console.log('加载策略列表接口:', url)
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('获取策略列表失败')
    }
    else{
      ElMessage.success('策略列表加载成功')
    }
    const data = await response.json()
    console.log('加载策略列表响应:', data)
    
    // 对策略列表按创建时间正序排列，这样最新的策略会显示在最后面
    // 确保排序逻辑正确，最新的策略显示在最后面
    strategies.value = [...data.strategies].sort((a, b) => {
      const dateA = new Date(a.created_at)
      const dateB = new Date(b.created_at)
      console.log(`Comparing dates: ${dateA} vs ${dateB}, result: ${dateA - dateB}`)
      return dateA - dateB
    })
    console.log('排序后的策略列表:', strategies.value)
    total.value = data.total
  } catch (error) {
    console.error('Error loading strategies:', error)
    ElMessage.error(error.message || '获取策略列表失败')
    // 模拟数据
    strategies.value = [
      {
        id: 1,
        intensity_level: '低',
        hedonic: '积极',
        tension: '低',
        complexity: '简单',
        fusion_mode: 'CBT',
        cbt_techniques: '认知重构',
        tcm_methods: '',
        strategy_content: '通过认知重构技术，识别并挑战负面思维模式',
        example: '当你感到焦虑时，尝试写下你的担忧，然后寻找证据来反驳它们',
        created_at: '2026-03-05T00:00:00'
      },
      {
        id: 2,
        intensity_level: '中',
        hedonic: '消极',
        tension: '中',
        complexity: '中等',
        fusion_mode: '中医',
        cbt_techniques: '',
        tcm_methods: '肝气郁结调理',
        strategy_content: '通过中医方法调理肝气郁结，缓解情绪压力',
        example: '尝试进行深呼吸练习，配合轻柔的伸展运动',
        created_at: '2026-03-06T00:00:00'
      }
    ]
    total.value = 2
  }
}

// 处理搜索
const handleSearch = () => {
  page.value = 1
  loadStrategies()
}

// 切换页码
const changePage = (newPage) => {
  if (newPage < 1 || newPage > totalPages.value) {
    return
  }
  page.value = newPage
  loadStrategies()
}

// 打开新增对话框
const openAddDialog = () => {
  isEditing.value = false
  currentStrategy.value = null
  strategyForm.value = {
    intensity_level: '',
    hedonic: '',
    tension: '',
    complexity: '',
    fusion_mode: '',
    cbt_techniques: '',
    tcm_methods: '',
    strategy_content: '',
    example: ''
  }
  
  isDialogVisible.value = true
}

// 编辑策略
const editRule = (strategy) => {
  isEditing.value = true
  currentStrategy.value = strategy
  
  // 转换融合模式为下拉菜单选项值
  let fusionModeValue = strategy.fusion_mode
  const fusionModeReverseMap = {
    'tcm': '中医',
    'cbt': 'CBT',
    'cbt_tcm': 'CBT+中医'
  }
  if (fusionModeReverseMap[fusionModeValue]) {
    fusionModeValue = fusionModeReverseMap[fusionModeValue]
  }
  
  strategyForm.value = {
    intensity_level: strategy.intensity_level,
    hedonic: strategy.hedonic,
    tension: strategy.tension,
    complexity: strategy.complexity,
    fusion_mode: fusionModeValue,
    cbt_techniques: strategy.cbt_techniques,
    tcm_methods: strategy.tcm_methods,
    strategy_content: strategy.strategy_content,
    example: strategy.example
  }
  isDialogVisible.value = true
}

// 关闭对话框
const closeDialog = () => {
  isDialogVisible.value = false
  currentStrategy.value = null
}

// 保存策略
const saveRule = async () => {
  // 验证表单
  if (!strategyForm.value.intensity_level || !strategyForm.value.hedonic || !strategyForm.value.tension || !strategyForm.value.complexity || !strategyForm.value.fusion_mode) {
    ElMessage.error('请填写完整的策略信息，必须选择融合模式')
    return
  }
  if (!strategyForm.value.strategy_content || !strategyForm.value.example) {
    ElMessage.error('请填写完整的策略信息')
    return
  }

  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    let url, method
    if (isEditing.value && currentStrategy.value) {
      url = `${API_BASE_URL}/api/v1/admin/strategies/${currentStrategy.value.id}`
      method = 'PUT'
    } else {
      url = `${API_BASE_URL}/api/v1/admin/strategies`
      method = 'POST'
    }

    console.log('保存策略接口:', url)
    console.log('保存策略方法:', method)
    console.log('保存策略参数:', strategyForm.value)

    // 转换字段数据
    const transformedStrategyForm = {
      ...strategyForm.value,
      fusion_mode: strategyForm.value.fusion_mode === '中医' ? 'tcm' : 
                  strategyForm.value.fusion_mode === 'CBT' ? 'cbt' : 
                  strategyForm.value.fusion_mode === 'CBT+中医' ? 'cbt_tcm' : 
                  strategyForm.value.fusion_mode
    }
    
    console.log('转换后的策略参数:', transformedStrategyForm)

    // 调整请求体格式以匹配API要求
    const requestBody = {
      strategy_data: transformedStrategyForm,
      request: {}
    }
    
    console.log('保存策略请求体:', requestBody)
    
    const response = await fetch(url, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      if (response.status === 400) {
        ElMessage.error('策略已存在')
        return
      }
      throw new Error(isEditing.value ? '更新策略失败' : '新增策略失败')
    }

    // 处理响应，更新策略的响应是字符串，添加策略的响应是对象
    let data
    try {
      data = await response.json()
    } catch (e) {
      // 如果响应不是JSON格式，可能是字符串
      data = await response.text()
    }
    console.log('保存策略响应:', data)

    ElMessage.success(isEditing.value ? '策略更新成功' : '策略新增成功')
    closeDialog()
    
    // 记录新增或更新的策略ID
    if (isEditing.value && currentStrategy.value) {
      // 更新策略
      updatedStrategies.value.add(currentStrategy.value.id)
    } else if (data && data.id) {
      // 新增策略
      newStrategies.value.add(data.id)
    }
    
    // 重新加载策略列表，获取最新的策略数据
    await loadStrategies()
  } catch (error) {
    console.error('Error saving strategy:', error)
    ElMessage.error(error.message || '保存策略失败')
  }
}

// 删除策略
const deleteRule = async (strategy) => {
  if (!confirm('确定要删除该策略吗？')) return

  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/v1/admin/strategies/${strategy.id}`
    console.log('删除策略接口:', url)
    console.log('删除策略方法:', 'DELETE')
    console.log('删除策略ID:', strategy.id)

    // 构造请求体
    const requestBody = {
      additionalProp1: {}
    }
    
    console.log('删除策略请求体:', requestBody)
    
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error('删除策略失败')
    }

    // 处理响应，删除策略的响应是字符串
    let data
    try {
      data = await response.json()
    } catch (e) {
      // 如果响应不是JSON格式，可能是字符串
      data = await response.text()
    }
    console.log('删除策略响应:', data)

    ElMessage.success('策略删除成功')
    loadStrategies()
  } catch (error) {
    console.error('Error deleting strategy:', error)
    ElMessage.error(error.message || '删除策略失败')
  }
}

// 初始化
onMounted(() => {
  loadStrategies()
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
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
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
  
  /* 新增策略行背景色 */
  .new-strategy-row {
    background-color: #e6f7ff !important;
  }
  
  /* 更新策略行背景色 */
  .updated-strategy-row {
    background-color: #f6ffed !important;
  }
}
</style>