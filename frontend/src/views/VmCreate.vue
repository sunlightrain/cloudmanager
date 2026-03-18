<template>
  <div class="vm-create">
    <el-card>
      <template #header>
        <span>Create Virtual Machine</span>
      </template>
      
      <el-form :model="form" label-width="140px">
        <el-form-item label="VM Name">
          <el-input v-model="form.name" placeholder="Enter VM name" />
        </el-form-item>
        
        <el-form-item label="CPU Cores">
          <el-input-number v-model="form.cpu" :min="1" :max="64" />
        </el-form-item>
        
        <el-form-item label="Memory (MB)">
          <el-input-number v-model="form.memory_mb" :min="512" :max="131072" :step="512" />
        </el-form-item>
        
        <el-form-item label="Disk (GB)">
          <el-input-number v-model="form.disk_gb" :min="1" :max="1000" />
        </el-form-item>
        
        <el-form-item label="Network">
          <el-input v-model="form.network_name" placeholder="VM Network" />
        </el-form-item>
        
        <el-form-item label="Datastore">
          <el-input v-model="form.datastore" placeholder="datastore1" />
        </el-form-item>
        
        <el-form-item label="Guest OS">
          <el-select v-model="form.guest_id" placeholder="Select OS">
            <el-option label="Ubuntu 64-bit" value="ubuntu64Guest" />
            <el-option label="CentOS 64-bit" value="centos7-64Guest" />
            <el-option label="Windows 2019 64-bit" value="windows9_64Guest" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            Create
          </el-button>
          <el-button @click="$router.back()">Cancel</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { vmsApi } from '@/api/vms'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  name: '',
  cpu: 2,
  memory_mb: 4096,
  disk_gb: 50,
  network_name: 'VM Network',
  datastore: 'datastore1',
  guest_id: 'ubuntu64Guest'
})

async function handleSubmit() {
  if (!form.name) {
    ElMessage.warning('Please enter VM name')
    return
  }
  
  loading.value = true
  try {
    const response = await vmsApi.create(form)
    ElMessage.success('VM created successfully')
    router.push('/vms')
  } catch (error) {
    console.error('Failed to create VM:', error)
    ElMessage.error('Failed to create VM')
  } finally {
    loading.value = false
  }
}
</script>
