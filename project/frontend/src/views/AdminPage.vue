<template>
  <AdminLayout>
    <UserManagement v-if="currentRoute === '/admin/users'" />
    <RuleManagement v-else-if="currentRoute === '/admin/rules'" />
    <AlertManagement v-else-if="currentRoute === '/admin/alerts'" />
    <QuestionnaireManagement v-else-if="currentRoute === '/admin/questionnaires'" />
    <AuditLog v-else-if="currentRoute === '/admin/audit-logs'" />
    <div v-else class="default-content">
      <h2>欢迎来到后台管理</h2>
      <p>请选择左侧菜单进行操作</p>
    </div>
  </AdminLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayout from '../components/admin/AdminLayout.vue'
import UserManagement from '../components/admin/UserManagement.vue'
import RuleManagement from '../components/admin/RuleManagement.vue'
import AlertManagement from '../components/admin/AlertManagement.vue'
import QuestionnaireManagement from '../components/admin/QuestionnaireManagement.vue'
import AuditLog from '../components/admin/AuditLog.vue'

const route = useRoute()
const currentRoute = computed(() => route.path)
</script>

<style scoped>
.default-content {
  padding: 40px;
  text-align: center;
  color: #6c757d;
}

.default-content h2 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #333;
}

.default-content p {
  font-size: 16px;
}
</style>