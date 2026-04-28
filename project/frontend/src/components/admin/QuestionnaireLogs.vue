<template>
  <div class="questionnaire-logs">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterAction" placeholder="操作类型" clearable style="width: 150px">
        <el-option label="全部操作" value="" />
        <el-option label="查看记录" value="view_record" />
        <el-option label="修改结果等级" value="modify_result" />
        <el-option label="启用问卷" value="enable_template" />
        <el-option label="禁用问卷" value="disable_template" />
        <el-option label="修改评分规则" value="modify_rule" />
      </el-select>
      <el-input v-model="searchUser" placeholder="搜索用户ID" style="width: 200px" clearable />
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 250px"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button @click="refreshData">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <!-- 日志表格 -->
    <el-table :data="logs" v-loading="isLoading" style="width: 100%">
      <el-table-column label="时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="管理员" prop="admin_username" width="120" />
      <el-table-column label="操作类型" width="150">
        <template #default="{ row }">
          <el-tag :type="getActionType(row.action)" effect="dark" size="small">
            {{ row.action_text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用户ID" prop="user_id" width="150" />
      <el-table-column label="问卷模板" prop="template_code" width="120" />
      <el-table-column label="详情" min-width="200">
        <template #default="{ row }">
          <div v-if="row.action === 'modify_result'" class="log-detail">
            <span>从 <el-tag size="small">{{ getLevelText(row.old_value?.result_level) }}</el-tag></span>
            <span> 修改为 <el-tag size="small" type="danger">{{ getLevelText(row.new_value?.result_level) }}</el-tag></span>
            <div class="reason">原因: {{ row.reason }}</div>
          </div>
          <div v-else-if="row.action === 'enable_template' || row.action === 'disable_template'" class="log-detail">
            {{ row.new_value?.template_name || row.template_code }}
          </div>
          <div v-else class="log-detail">
            {{ row.reason || '-' }}
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'

const store = useAdminQuestionnaireStore()
const logs = ref([])
const total = ref(0)
const isLoading = ref(false)
const filterAction = ref('')
const searchUser = ref('')
const dateRange = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

const getActionType = (action) => {
  const map = {
    view_record: 'info',
    modify_result: 'danger',
    enable_template: 'success',
    disable_template: 'warning',
    modify_rule: 'primary'
  }
  return map[action] || 'info'
}

const getLevelText = (level) => {
  const map = { none: '正常', mild: '轻度', moderate: '中度', moderately_severe: '中重度', severe: '重度' }
  return map[level] || level
}

const formatDate = (date) => {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const refreshData = () => {
  loadData()
}

const loadData = async () => {
  isLoading.value = true
  try {
    const filters = {
      action: filterAction.value || undefined,
      user_id: searchUser.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      filters.start_date = dateRange.value[0].toISOString().split('T')[0]
      filters.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const res = await store.getLogs(filters)
    logs.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('Load logs error:', error)
  } finally {
    isLoading.value = false
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  loadData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.questionnaire-logs {
  padding: 20px 0;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.log-detail {
  font-size: 14px;
}
.log-detail .reason {
  color: #909399;
  margin-top: 4px;
  font-size: 12px;
}
.pagination-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
