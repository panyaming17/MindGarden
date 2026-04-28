<template>
  <div class="high-risk-users">
    <div class="section-header">
      <h3>高危用户排行</h3>
      <p class="subtitle">按预警数量和危险等级排序</p>
    </div>

    <el-table :data="highRiskUsers" style="width: 100%" v-loading="isLoading">
      <el-table-column type="index" label="排名" width="80" align="center">
        <template #default="{ $index }">
          <div class="rank-cell" :class="{ 'top-3': $index < 3 }">
            {{ $index + 1 }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="用户信息" min-width="200">
        <template #default="{ row }">
          <div class="user-info">
            <div class="username">{{ row.username }}</div>
            <div class="user-id">{{ row.user_id }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="邮箱" prop="email" min-width="200" />
      <el-table-column label="预警数量" width="120" align="center">
        <template #default="{ row }">
          <el-tag type="warning" effect="dark">{{ row.alert_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="高危预警" width="120" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.danger_count > 0" type="danger" effect="dark">
            {{ row.danger_count }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewProfile(row.user_id)">
            查看画像
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 用户画像弹窗 -->
    <el-dialog
      v-model="profileDialogVisible"
      title="用户预警画像"
      width="900px"
      destroy-on-close
    >
      <UserAlertProfile v-if="selectedUserId" :user-id="selectedUserId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminAlertStore } from '@/stores/adminAlert'
import UserAlertProfile from './UserAlertProfile.vue'

const store = useAdminAlertStore()

const isLoading = ref(false)
const highRiskUsers = ref([])
const profileDialogVisible = ref(false)
const selectedUserId = ref('')

const loadData = async () => {
  isLoading.value = true
  try {
    const data = await store.getHighRiskUsers(20)
    highRiskUsers.value = data.users
  } finally {
    isLoading.value = false
  }
}

const viewProfile = (userId) => {
  selectedUserId.value = userId
  profileDialogVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.high-risk-users {
  padding: 20px 0;
}

.section-header {
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.rank-cell {
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 50%;
  background: #f5f7fa;
  color: #606266;
  font-weight: 600;
  margin: 0 auto;
}

.rank-cell.top-3 {
  background: #f56c6c;
  color: white;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-weight: 500;
  color: #303133;
}

.user-id {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
