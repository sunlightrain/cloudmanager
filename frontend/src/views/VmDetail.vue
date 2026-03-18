<template>
  <div class="vm-detail" v-loading="loading">
    <el-card v-if="vm">
      <template #header>
        <div class="card-header">
          <span>{{ vm.name }}</span>
          <el-button-group>
            <el-button :type="vm.status === 'poweredOn' ? 'danger' : 'success'" @click="togglePower">
              {{ vm.status === 'poweredOn' ? 'Stop' : 'Start' }}
            </el-button>
            <el-button type="primary" @click="showEditDialog = true">Edit</el-button>
            <el-button type="danger" @click="handleDelete">Delete</el-button>
          </el-button-group>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="VM ID">{{ vm.vm_id }}</el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag :type="vm.status === 'poweredOn' ? 'success' : 'info'">
            {{ vm.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="CPU">{{ vm.cpu }} cores</el-descriptions-item>
        <el-descriptions-item label="Memory">{{ (vm.memory_mb / 1024).toFixed(1) }} GB</el-descriptions-item>
        <el-descriptions-item label="IP Address">{{ vm.ip_address || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Host">{{ vm.host || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Guest OS" :span="2">{{ vm.guest_full_name || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Annotation" :span="2">{{ vm.annotation || 'N/A' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <el-dialog v-model="showEditDialog" title="Edit VM" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="CPU">
          <el-input-number v-model="editForm.cpu" :min="1" :max="64" />
        </el-form-item>
        <el-form-item label="Memory (MB)">
          <el-input-number v-model="editForm.memory_mb" :min="512" :max="131072" :step="512" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleEdit">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vmsApi, type VM, type VMUpdate } from '@/api/vms'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

const vm = ref<VM | null>(null)
const loading = ref(false)
const showEditDialog = ref(false)
const editForm = reactive<VMUpdate>({
  cpu: 2,
  memory_mb: 4096
})

async function loadVM() {
  loading.value = true
  try {
    const response = await vmsApi.getById(route.params.id as string)
    vm.value = response.data.data
    if (vm.value) {
      editForm.cpu = vm.value.cpu
      editForm.memory_mb = vm.value.memory_mb
    }
  } catch (error) {
    console.error('Failed to load VM:', error)
    ElMessage.error('Failed to load VM')
  } finally {
    loading.value = false
  }
}

async function togglePower() {
  if (!vm.value) return
  const action = vm.value.status === 'poweredOn' ? 'stop' : 'start'
  
  try {
    await vmsApi.power(vm.value.vm_id, action as 'start' | 'stop')
    ElMessage.success(`VM ${action} successful`)
    loadVM()
  } catch (error) {
    ElMessage.error(`Failed to ${action} VM`)
  }
}

async function handleEdit() {
  if (!vm.value) return
  
  try {
    await vmsApi.update(vm.value.vm_id, editForm)
    ElMessage.success('VM updated successfully')
    showEditDialog.value = false
    loadVM()
  } catch (error) {
    ElMessage.error('Failed to update VM')
  }
}

async function handleDelete() {
  if (!vm.value) return
  
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this VM?', 'Confirm', {
      type: 'warning'
    })
    
    await vmsApi.delete(vm.value.vm_id)
    ElMessage.success('VM deleted successfully')
    router.push('/vms')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete VM')
    }
  }
}

onMounted(() => {
  loadVM()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
