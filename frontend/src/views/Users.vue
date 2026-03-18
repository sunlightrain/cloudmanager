<template>
  <div class="users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>User Management</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            Add User
          </el-button>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="Username" width="150" />
        <el-table-column prop="email" label="Email" min-width="180" />
        <el-table-column prop="role" label="Role" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? 'Active' : 'Inactive' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created" width="180">
          <template #default="{ row }">
            {{ row.created_at ? formatDate(row.created_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="handleEdit(row)">Edit</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)" :disabled="row.id === currentUserId">
                Delete
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
        @current-change="loadUsers"
      />
    </el-card>
    
    <el-dialog v-model="showCreateDialog" title="Add User" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="Username">
          <el-input v-model="createForm.username" placeholder="Enter username" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="createForm.password" type="password" placeholder="Enter password" show-password />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="createForm.email" placeholder="Enter email" />
        </el-form-item>
        <el-form-item label="Role">
          <el-select v-model="createForm.role" placeholder="Select role">
            <el-option label="Admin" value="admin" />
            <el-option label="User" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">Create</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showEditDialog" title="Edit User" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="Email">
          <el-input v-model="editForm.email" placeholder="Enter email" />
        </el-form-item>
        <el-form-item label="New Password">
          <el-input v-model="editForm.password" type="password" placeholder="Leave blank to keep current" show-password />
        </el-form-item>
        <el-form-item label="Role" v-if="isAdmin">
          <el-select v-model="editForm.role" placeholder="Select role">
            <el-option label="Admin" value="admin" />
            <el-option label="User" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="Status" v-if="isAdmin">
          <el-switch v-model="editForm.is_active" />
          <span style="margin-left: 10px">{{ editForm.is_active ? 'Active' : 'Inactive' }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { usersApi, type User, type UserCreate, type UserUpdate } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.user_id)
const isAdmin = computed(() => authStore.user?.username === 'admin')

const users = ref<User[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const updating = ref(false)
const editingUserId = ref<number | null>(null)

const createForm = reactive<UserCreate>({
  username: '',
  password: '',
  email: '',
  role: 'user'
})

const editForm = reactive<UserUpdate>({
  email: '',
  password: '',
  role: 'user',
  is_active: true
})

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

async function loadUsers() {
  loading.value = true
  try {
    const response = await usersApi.getList({ page: page.value, page_size: pageSize.value })
    users.value = response.data.data.items || []
    total.value = response.data.data.total || 0
  } catch (error: any) {
    if (error.response?.status === 403) {
      ElMessage.error('Admin permission required')
    } else {
      ElMessage.error('Failed to load users')
    }
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.username || !createForm.password) {
    ElMessage.warning('Please enter username and password')
    return
  }
  
  creating.value = true
  try {
    await usersApi.create(createForm)
    ElMessage.success('User created successfully')
    showCreateDialog.value = false
    createForm.username = ''
    createForm.password = ''
    createForm.email = ''
    createForm.role = 'user'
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to create user')
  } finally {
    creating.value = false
  }
}

function handleEdit(user: User) {
  editingUserId.value = user.id
  editForm.email = user.email || ''
  editForm.password = ''
  editForm.role = user.role || 'user'
  editForm.is_active = user.is_active
  showEditDialog.value = true
}

async function handleUpdate() {
  if (!editingUserId.value) return
  
  updating.value = true
  try {
    await usersApi.update(editingUserId.value, editForm)
    ElMessage.success('User updated successfully')
    showEditDialog.value = false
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to update user')
  } finally {
    updating.value = false
  }
}

async function handleDelete(user: User) {
  try {
    await ElMessageBox.confirm(`Are you sure you want to delete user "${user.username}"?`, 'Confirm', { type: 'warning' })
    await usersApi.delete(user.id)
    ElMessage.success('User deleted successfully')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || 'Failed to delete user')
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
