<template>
  <div class="questionnaire-records">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterTemplate" placeholder="问卷类型" clearable style="width: 150px">
        <el-option label="全部问卷" value="" />
        <el-option v-for="t in store.templates" :key="t.code" :label="t.name" :value="t.code" />
      </el-select>
      <el-select v-model="filterLevel" placeholder="结果等级" clearable style="width: 150px">
        <el-option label="全部等级" value="" />
        <el-option label="正常" value="none" />
        <el-option label="轻度" value="mild" />
        <el-option label="中度" value="moderate" />
        <el-option label="中重度" value="moderately_severe" />
        <el-option label="重度" value="severe" />
      </el-select>
      <el-input v-model="searchUser" placeholder="搜索用户ID" style="width: 200px" clearable />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button @click="refreshData">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <!-- 记录表格 -->
    <el-table :data="store.records" v-loading="store.isLoading" style="width: 100%">
      <el-table-column label="ID" prop="id" width="80" />
      <el-table-column label="用户" min-width="150">
        <template #default="{ row }">
          <div class="user-info">
            <span class="username">{{ row.username || '未知用户' }}</span>
            <span class="user-id">{{ row.user_id }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="问卷类型" prop="template_name" width="150" />
      <el-table-column label="得分" width="100" align="center">
        <template #default="{ row }">
          <span class="score" :class="getScoreClass(row.result_level)">{{ row.total_score }}</span>
        </template>
      </el-table-column>
      <el-table-column label="结果等级" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getLevelType(row.result_level)" effect="dark" size="small">
            {{ row.result_level_text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="预警" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.has_alert" type="danger" effect="dark" size="small">已触发</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="答题时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="store.totalRecords"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="答题详情" width="700px" destroy-on-close>
      <QuestionnaireRecordDetail 
        v-if="selectedRecord" 
        :record="store.recordDetail" 
        @modified="handleRecordModified"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'
import QuestionnaireRecordDetail from './QuestionnaireRecordDetail.vue'

const store = useAdminQuestionnaireStore()
const filterTemplate = ref('')
const filterLevel = ref('')
const searchUser = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const detailDialogVisible = ref(false)
const selectedRecord = ref(null)

const getScoreClass = (level) => {
  const map = { none: 'success', mild: 'warning', moderate: 'warning', moderately_severe: 'danger', severe: 'danger' }
  return map[level] || ''
}

const getLevelType = (level) => {
  const map = { none: 'success', mild: 'warning', moderate: 'warning', moderately_severe: 'danger', severe: 'danger' }
  return map[level] || 'info'
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

const loadData = () => {
  store.getRecords({
    template_code: filterTemplate.value || undefined,
    result_level: filterLevel.value || undefined,
    user_id: searchUser.value || undefined,
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const handleSizeChange = (val) => {
  pageSize.value = val
  loadData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadData()
}

const viewDetail = async (row) => {
  selectedRecord.value = row
  await store.getRecordDetail(row.id)
  detailDialogVisible.value = true
}

const handleRecordModified = () => {
  detailDialogVisible.value = false
  loadData() // 刷新列表
}

watch([filterTemplate, filterLevel], () => {
  currentPage.value = 1
  loadData()
})
</script>

<style scoped>
.questionnaire-records {
  padding: 20px 0;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.username {
  font-weight: 500;
}
.user-id {
  font-size: 12px;
  color: #909399;
}
.score {
  font-weight: 600;
  font-size: 16px;
}
.score.success { color: #67c23a; }
.score.warning { color: #e6a23c; }
.score.danger { color: #f56c6c; }
.pagination-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
