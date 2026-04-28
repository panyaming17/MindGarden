<template>
  <div class="audit-log-container">
    <h2>审计日志</h2>
    
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <el-input
            v-model="filters.admin_id"
            placeholder="管理员ID"
            clearable
          />
        </div>
        <div class="filter-item">
          <el-select
            v-model="filters.action"
            placeholder="操作类型"
            clearable
          >
            <el-option
              v-for="action in actionOptions"
              :key="action.value"
              :label="action.label"
              :value="action.value"
            />
          </el-select>
        </div>
        <div class="filter-item date-range">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>
    
    <!-- 表格区域 -->
    <el-table
      v-loading="loading"
      :data="auditLogs"
      style="width: 100%"
      border
    >
      <el-table-column prop="id" label="序号" width="80" />
      <el-table-column prop="admin_id" label="管理员名称" width="120" />
      <el-table-column prop="action" label="操作类型" width="150" />
      <el-table-column prop="target" label="目标" width="120" />
      <el-table-column label="详情" width="250">
        <template #default="scope">
          <span v-if="isJson(scope.row.details)">
            <el-button type="text" @click="showDetails(scope.row)">查看详情</el-button>
          </span>
          <span v-else>{{ scope.row.details }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP地址" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button type="primary" size="small" @click="showDetails(scope.row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页组件 -->
    <div class="pagination-section">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="操作详情"
      width="50%"
    >
      <pre v-if="currentLog">{{ JSON.stringify(currentLog.details, null, 2) }}</pre>
      <div v-else>无详情数据</div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

// 状态管理
const authStore = useAuthStore()
const loading = ref(false)
const auditLogs = ref([])
const total = ref(0)
const page = ref(1)
const perPage = ref(10)

// 筛选条件
const filters = ref({
  admin_id: '',
  action: '',
  dateRange: []
})

// 操作类型选项
const actionOptions = ref([
  { value: 'create_strategy', label: '创建策略' },
  { value: 'update_strategy', label: '更新策略' },
  { value: 'delete_strategy', label: '删除策略' },
  { value: 'create_user', label: '创建用户' },
  { value: 'update_user', label: '更新用户' },
  { value: 'delete_user', label: '删除用户' }
])

// 详情对话框
const dialogVisible = ref(false)
const currentLog = ref(null)

// API基础URL
const API_BASE_URL = 'http://localhost:8000'

// 加载审计日志
const loadAuditLogs = async () => {
  loading.value = true
  try {
    const token = authStore.getToken
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      loading.value = false
      return
    }

    // 构建查询参数
    const params = new URLSearchParams()
    params.append('page', page.value)
    params.append('per_page', perPage.value)
    
    if (filters.value.admin_id) {
      params.append('admin_id', filters.value.admin_id)
    }
    if (filters.value.action) {
      params.append('action', filters.value.action)
    }
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.append('start_date', filters.value.dateRange[0])
      params.append('end_date', filters.value.dateRange[1])
    }

    const url = `${API_BASE_URL}/api/v1/admin/logs?${params.toString()}`
    // console.log('获取日志信息接口:', url)
    // console.log('获取日志信息参数:', params.toString())
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('获取审计日志失败')
    }

    const data = await response.json()
    // console.log('获取日志信息响应:', data)
    auditLogs.value = data.logs
    total.value = data.total
    
    // 从日志数据中提取唯一的操作类型，动态更新操作类型选项
    const uniqueActions = [...new Set(data.logs.map(log => log.action))]
    const dynamicActionOptions = uniqueActions.map(action => {
      const existingOption = actionOptions.value.find(opt => opt.value === action)
      if (existingOption) {
        return existingOption
      } else {
        return { value: action, label: action }
      }
    })
    
    // 合并静态选项和动态选项，确保不重复
    const mergedOptions = [...actionOptions.value]
    dynamicActionOptions.forEach(option => {
      if (!mergedOptions.find(opt => opt.value === option.value)) {
        mergedOptions.push(option)
      }
    })
    
    actionOptions.value = mergedOptions
  } catch (error) {
    console.error('Error loading audit logs:', error)
    ElMessage.error(error.message || '获取审计日志失败')
    // 模拟数据
    auditLogs.value = [
      {
        id: 1,
        admin_id: 1,
        action: 'create',
        target_type: 'rule',
        target_id: 1,
        details: {"rule_id": 1, "action": "创建规则", "rule_name": "认知重构"},
        created_at: '2026-03-05T10:00:00'
      },
      {
        id: 2,
        admin_id: 1,
        action: 'update',
        target_type: 'rule',
        target_id: 1,
        details: {"rule_id": 1, "action": "更新规则", "rule_name": "认知重构", "changes": {"version": "1.1"}},
        created_at: '2026-03-05T10:30:00'
      },
      {
        id: 3,
        admin_id: 2,
        action: 'delete',
        target_type: 'user',
        target_id: 3,
        details: {"user_id": 3, "action": "删除用户", "user_name": "test"},
        created_at: '2026-03-05T11:00:00'
      }
    ]
    total.value = 3
  } finally {
    loading.value = false
  }
}

// 处理搜索
const handleSearch = () => {
  page.value = 1
  loadAuditLogs()
}

// 处理重置
const handleReset = () => {
  filters.value = {
    admin_id: '',
    action: '',
    dateRange: []
  }
  page.value = 1
  loadAuditLogs()
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  perPage.value = size
  page.value = 1
  loadAuditLogs()
}

// 处理当前页变化
const handleCurrentChange = (current) => {
  page.value = current
  loadAuditLogs()
}

// 显示详情
const showDetails = (log) => {
  currentLog.value = log
  dialogVisible.value = true
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 判断是否为JSON
const isJson = (value) => {
  try {
    JSON.parse(JSON.stringify(value))
    return typeof value === 'object' && value !== null
  } catch (e) {
    return false
  }
}

// 初始加载
onMounted(() => {
  loadAuditLogs()
})
</script>

<style scoped>
.audit-log-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 80vh;
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.filter-section {
  background-color: white;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-row {
  display: flex;
  gap: 15px;
  align-items: center;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.date-range {
  flex: 1.5;
}

.filter-actions {
  display: flex;
  gap: 10px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.el-table {
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.el-table th {
  background-color: #f5f7fa;
}

.dialog-footer {
  text-align: right;
}
</style>