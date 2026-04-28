<template>
  <div class="alert-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-icon">🚨</span>
        <h2>预警管理</h2>
        <el-badge 
          v-if="unacknowledgedCount > 0" 
          :value="unacknowledgedCount" 
          class="title-badge"
          type="danger"
        />
      </div>
      <p class="header-subtitle">监控所有用户的预警信息，及时处理高风险情况</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card danger">
        <div class="stat-icon">🔴</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.by_level?.danger || 0 }}</div>
          <div class="stat-label">高危预警</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">🟡</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.by_level?.warning || 0 }}</div>
          <div class="stat-label">中危预警</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">🔵</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.by_level?.info || 0 }}</div>
          <div class="stat-label">低危预警</div>
        </div>
      </div>
      <div class="stat-card total">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.total || 0 }}</div>
          <div class="stat-label">预警总数</div>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="alert-tabs">
      <!-- 预警列表 -->
      <el-tab-pane label="预警列表" name="alerts">
        <div class="tab-content">
          <!-- 筛选器 -->
          <div class="filter-bar">
            <el-select v-model="filterLevel" placeholder="预警等级" clearable style="width: 120px">
              <el-option label="全部等级" value="" />
              <el-option label="高危" value="danger" />
              <el-option label="中危" value="warning" />
              <el-option label="低危" value="info" />
            </el-select>
            <el-select v-model="filterType" placeholder="预警类型" clearable style="width: 120px">
              <el-option label="全部类型" value="" />
              <el-option label="问卷" value="questionnaire" />
              <el-option label="情绪" value="emotion" />
              <el-option label="对话" value="conversation" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
              <el-option label="全部状态" value="" />
              <el-option label="未确认" value="unacknowledged" />
              <el-option label="已确认" value="acknowledged" />
            </el-select>
            <el-input 
              v-model="searchUser" 
              placeholder="搜索用户ID" 
              style="width: 200px"
              clearable
            />
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 预警表格 -->
          <el-table 
            :data="filteredAlerts" 
            style="width: 100%"
            v-loading="isLoading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column label="等级" width="80">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="dark">
                  {{ getLevelText(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getTypeType(row.type)">
                  {{ getTypeText(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip />
            <el-table-column label="用户ID" prop="user_id" width="150" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_acknowledged ? 'success' : 'warning'">
                  {{ row.is_acknowledged ? '已确认' : '未确认' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
                <el-button 
                  v-if="!row.is_acknowledged" 
                  link 
                  type="success" 
                  @click="acknowledge(row)"
                >
                  确认
                </el-button>
                <el-button link type="danger" @click="deleteAlert(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-bar">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
            <div class="batch-actions" v-if="selectedAlerts.length > 0">
              <span class="selected-count">已选择 {{ selectedAlerts.length }} 项</span>
              <el-button type="danger" size="small" @click="batchDelete">
                批量删除
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 高危用户 -->
      <el-tab-pane label="高危用户" name="high-risk">
        <HighRiskUsers />
      </el-tab-pane>

      <!-- 统计分析 -->
      <el-tab-pane label="统计分析" name="statistics">
        <AlertStatistics />
      </el-tab-pane>
    </el-tabs>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="预警详情"
      width="700px"
      destroy-on-close
    >
      <AlertDetail 
        v-if="selectedAlert" 
        :alert="selectedAlert"
        @acknowledge="acknowledge"
        @delete="deleteAlert"
      />
    </el-dialog>

    <!-- 用户画像弹窗 -->
    <el-dialog
      v-model="profileDialogVisible"
      title="用户预警画像"
      width="900px"
      destroy-on-close
    >
      <UserAlertProfile 
        v-if="selectedUserId" 
        :user-id="selectedUserId"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useAdminAlertStore } from '@/stores/adminAlert'
import HighRiskUsers from './HighRiskUsers.vue'
import AlertStatistics from './AlertStatistics.vue'
import AlertDetail from './AlertDetail.vue'
import UserAlertProfile from './UserAlertProfile.vue'

const store = useAdminAlertStore()

// State
const activeTab = ref('alerts')
const filterLevel = ref('')
const filterType = ref('')
const filterStatus = ref('')
const searchUser = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedAlerts = ref([])
const detailDialogVisible = ref(false)
const profileDialogVisible = ref(false)
const selectedAlert = ref(null)
const selectedUserId = ref('')

// Computed
const isLoading = computed(() => store.isLoading)
const stats = computed(() => store.stats)
const total = computed(() => store.total)
const unacknowledgedCount = computed(() => store.unacknowledgedAlerts.length)

const filteredAlerts = computed(() => {
  let result = store.alerts
  
  if (filterLevel.value) {
    result = result.filter(a => a.level === filterLevel.value)
  }
  if (filterType.value) {
    result = result.filter(a => a.type === filterType.value)
  }
  if (filterStatus.value) {
    if (filterStatus.value === 'acknowledged') {
      result = result.filter(a => a.is_acknowledged)
    } else {
      result = result.filter(a => !a.is_acknowledged)
    }
  }
  if (searchUser.value) {
    result = result.filter(a => a.user_id.includes(searchUser.value))
  }
  
  return result
})

// Methods
const getLevelType = (level) => {
  const map = { danger: 'danger', warning: 'warning', info: 'info' }
  return map[level] || 'info'
}

const getLevelText = (level) => {
  const map = { danger: '高危', warning: '中危', info: '低危' }
  return map[level] || level
}

const getTypeType = (type) => {
  const map = { questionnaire: 'primary', emotion: 'success', conversation: 'warning' }
  return map[type] || ''
}

const getTypeText = (type) => {
  const map = { questionnaire: '问卷', emotion: '情绪', conversation: '对话' }
  return map[type] || type
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const refreshData = () => {
  loadData()
  loadStats()
}

const loadData = async () => {
  const filters = {}
  if (filterLevel.value) filters.level = filterLevel.value
  if (filterType.value) filters.type = filterType.value
  if (filterStatus.value) filters.status = filterStatus.value
  if (searchUser.value) filters.user_id = searchUser.value
  
  await store.getAllAlerts(filters)
}

const loadStats = async () => {
  const endDate = new Date().toISOString().split('T')[0]
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  await store.getStatistics(startDate, endDate)
}

const handleSizeChange = (val) => {
  pageSize.value = val
  loadData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadData()
}

const handleSelectionChange = (selection) => {
  selectedAlerts.value = selection
}

const viewDetail = (alert) => {
  selectedAlert.value = alert
  detailDialogVisible.value = true
}

const viewUserProfile = (userId) => {
  selectedUserId.value = userId
  profileDialogVisible.value = true
}

const acknowledge = async (alert) => {
  try {
    await store.acknowledgeAlert(alert.id || alert)
    ElMessage.success('预警已确认')
    if (detailDialogVisible.value) {
      detailDialogVisible.value = false
    }
  } catch (error) {
    ElMessage.error('确认失败')
  }
}

const deleteAlert = async (alert) => {
  try {
    await ElMessageBox.confirm('确定要删除这个预警吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await store.deleteAlert(alert.id, '管理员手动删除')
    ElMessage.success('删除成功')
    if (detailDialogVisible.value) {
      detailDialogVisible.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedAlerts.value.length} 个预警吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedAlerts.value.map(a => a.id)
    await store.batchDeleteAlerts(ids, '批量删除')
    ElMessage.success('批量删除成功')
    selectedAlerts.value = []
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Lifecycle
onMounted(() => {
  loadData()
  loadStats()
  store.initWebSocket()
})

// Watch
watch([filterLevel, filterType, filterStatus], () => {
  currentPage.value = 1
  loadData()
})
</script>

<style scoped>
.alert-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 28px;
}

.header-title h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
  padding-left: 40px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-card.danger {
  border-left: 4px solid #f56c6c;
}

.stat-card.warning {
  border-left: 4px solid #e6a23c;
}

.stat-card.info {
  border-left: 4px solid #409eff;
}

.stat-card.total {
  border-left: 4px solid #67c23a;
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.alert-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.tab-content {
  padding-top: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-count {
  color: #606266;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
  }
  
  .filter-bar .el-select,
  .filter-bar .el-input {
    width: 100% !important;
  }
}
</style>
