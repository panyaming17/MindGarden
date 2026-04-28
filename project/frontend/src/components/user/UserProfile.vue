<template>
  <div class="user-profile-page">
    <div class="page-header">
      <h1>用户信息</h1>
      <button class="back-button" @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回
      </button>
    </div>
    
    <div class="profile-container">
      <!-- 头像部分 -->
      <div class="avatar-section">
        <div class="avatar-wrapper" @click="openAvatarUpload">
          <img v-if="user.avatar" :src="user.avatar" alt="用户头像" class="avatar-image">
          <span v-else class="avatar-placeholder">{{ user.name ? user.name.charAt(0) : 'U' }}</span>
          <div class="avatar-overlay">
            <span class="upload-text">更换头像</span>
          </div>
        </div>
        <h2 class="user-name">{{ user.name || '用户' }}</h2>
        <p class="user-email">{{ user.email || '未设置邮箱' }}</p>
      </div>
      
      <!-- 个人信息表单 -->
      <div class="info-section">
        <h3>个人资料</h3>
        <el-form :model="userForm" label-width="100px" class="user-form">
          <el-form-item label="用户名">
            <div class="form-item-with-action">
              <el-input 
                v-model="userForm.name" 
                placeholder="请输入用户名" 
                :disabled="userForm.name && !editMode.name"
              />
              <el-button 
                size="small" 
                v-if="userForm.name" 
                @click="toggleEdit('name')"
                :type="editMode.name ? 'primary' : 'default'"
              >
                {{ editMode.name ? '取消' : '修改' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item label="邮箱">
            <div class="form-item-with-action">
              <el-input 
                v-model="userForm.email" 
                type="email" 
                placeholder="请输入邮箱" 
                :disabled="userForm.email && !editMode.email"
              />
              <el-button 
                size="small" 
                v-if="userForm.email" 
                @click="toggleEdit('email')"
                :type="editMode.email ? 'primary' : 'default'"
              >
                {{ editMode.email ? '取消' : '修改' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item label="性别">
            <div class="form-item-with-action">
              <el-radio-group 
                v-model="userForm.gender"
                :disabled="userForm.gender && !editMode.gender"
              >
                <el-radio label="male">男</el-radio>
                <el-radio label="female">女</el-radio>
              </el-radio-group>
              <el-button 
                size="small" 
                v-if="userForm.gender" 
                @click="toggleEdit('gender')"
                :type="editMode.gender ? 'primary' : 'default'"
              >
                {{ editMode.gender ? '取消' : '修改' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item label="年龄">
            <div class="form-item-with-action">
              <el-input 
                v-model="userForm.age" 
                type="number" 
                placeholder="请输入年龄" 
                min="0" 
                max="150" 
                :disabled="userForm.age && !editMode.age"
              />
              <el-button 
                size="small" 
                v-if="userForm.age" 
                @click="toggleEdit('age')"
                :type="editMode.age ? 'primary' : 'default'"
              >
                {{ editMode.age ? '取消' : '修改' }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
        
        <div class="form-actions">
          <el-button 
            @click="resetForm" 
            :disabled="!hasChanges"
          >
            重置
          </el-button>
          <el-button 
            type="primary" 
            @click="saveProfile" 
            :disabled="!hasChanges"
          >
            保存修改
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 头像上传输入 -->
    <input type="file" ref="avatarInput" accept="image/*" style="display: none" @change="handleAvatarUpload">
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

export default {
  name: 'UserProfile',
  components: {
    ArrowLeft
  },
  setup() {
    const router = useRouter()
    const user = ref({})
    const userForm = ref({})
    const originalUser = ref({})
    const avatarInput = ref(null)
    
    // 编辑模式状态
    const editMode = ref({
      name: false,
      email: false,
      gender: false,
      age: false
    })
    
    // 加载用户数据
    const loadUserData = () => {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          user.value = {
            name: parsedUser.username || parsedUser.name,
            email: parsedUser.email,
            gender: parsedUser.gender,
            age: parsedUser.age,
            avatar: parsedUser.avatar
          }
          // 初始化原始数据
          originalUser.value = { ...user.value }
          // 初始化表单数据
          userForm.value = { ...user.value }
        } catch (error) {
          console.error('加载用户数据失败:', error)
          user.value = { name: '用户', avatar: '' }
          originalUser.value = { ...user.value }
          userForm.value = { ...user.value }
        }
      } else {
        user.value = { name: '用户', avatar: '' }
        originalUser.value = { ...user.value }
        userForm.value = { ...user.value }
      }
    }
    
    // 保存个人资料
    const saveProfile = () => {
      // 更新用户数据
      user.value = { ...userForm.value }
      // 保存到本地存储
      localStorage.setItem('user', JSON.stringify(user.value))
      // 更新原始数据
      originalUser.value = { ...user.value }
      // 关闭所有编辑模式
      Object.keys(editMode.value).forEach(key => {
        editMode.value[key] = false
      })
      // 显示成功提示
      ElMessage.success('个人资料保存成功')
    }
    
    // 重置表单
    const resetForm = () => {
      // 恢复原始数据
      userForm.value = { ...originalUser.value }
      // 关闭所有编辑模式
      Object.keys(editMode.value).forEach(key => {
        editMode.value[key] = false
      })
      ElMessage.info('已重置为原始数据')
    }
    
    // 切换编辑模式
    const toggleEdit = (field) => {
      // 如果当前是编辑模式，则取消编辑并恢复原始值
      if (editMode.value[field]) {
        userForm.value[field] = originalUser.value[field]
      }
      // 切换编辑状态
      editMode.value[field] = !editMode.value[field]
    }
    
    // 检查是否有修改
    const hasChanges = computed(() => {
      return JSON.stringify(userForm.value) !== JSON.stringify(originalUser.value)
    })
    
    // 打开头像上传
    const openAvatarUpload = () => {
      avatarInput.value.click()
    }
    
    // 处理头像上传
    const handleAvatarUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          userForm.value.avatar = e.target.result
          user.value.avatar = e.target.result
          originalUser.value.avatar = e.target.result
          localStorage.setItem('user', JSON.stringify(user.value))
          ElMessage.success('头像更新成功')
        }
        reader.readAsDataURL(file)
      }
    }
    
    // 返回上一页
    const goBack = () => {
      router.back()
    }
    
    // 初始化
    onMounted(() => {
      loadUserData()
    })
    
    return {
      user,
      userForm,
      avatarInput,
      editMode,
      saveProfile,
      resetForm,
      toggleEdit,
      hasChanges,
      openAvatarUpload,
      handleAvatarUpload,
      goBack
    }
  }
}
</script>

<style scoped>
.user-profile-page {
  padding: 20px;
  min-height: 100vh;
  background-color: #F9E0C9;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  transition: all 0.3s ease;
}

.back-button:hover {
  color: #4CAF50;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.avatar-section {
  text-align: center;
  margin-bottom: 40px;
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
  cursor: pointer;
  margin-bottom: 20px;
}

.avatar-image {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #f0f0f0;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #4CAF50;
  color: white;
  font-size: 48px;
  font-weight: bold;
  border: 4px solid #f0f0f0;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  color: white;
  font-size: 14px;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.user-name {
  margin: 10px 0 5px;
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.user-email {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.info-section {
  margin-bottom: 40px;
}

.info-section h3,
.account-section h3 {
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
}

.user-form {
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
}

.form-item-with-action {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.form-item-with-action .el-input {
  flex: 1;
}

.form-item-with-action .el-button {
  white-space: nowrap;
}

.account-section {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 20px;
}

.account-info-item {
  display: flex;
  margin-bottom: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #e4e7ed;
}

.account-info-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.account-info-item .label {
  width: 100px;
  font-weight: 500;
  color: #606266;
}

.account-info-item .value {
  flex: 1;
  color: #303133;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 20px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .account-info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .account-info-item .label {
    width: auto;
  }
}
</style>