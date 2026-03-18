<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>vSphere Connection Settings</span>
      </template>
      
      <el-form :model="form" label-width="140px">
        <el-form-item label="vCenter Host">
          <el-input v-model="form.host" placeholder="vcenter.example.com" />
        </el-form-item>
        
        <el-form-item label="Port">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="Username">
          <el-input v-model="form.username" placeholder="administrator@vsphere.local" />
        </el-form-item>
        
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" placeholder="Password" show-password />
        </el-form-item>
        
        <el-form-item label="Datacenter">
          <el-input v-model="form.datacenter" placeholder="Datacenter" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">Save</el-button>
          <el-button type="success" @click="handleTest" :loading="testing">Test Connection</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

const saving = ref(false)
const testing = ref(false)

const form = reactive({
  host: '',
  port: 443,
  username: '',
  password: '',
  datacenter: ''
})

async function loadSettings() {
  try {
    const response = await api.get('/settings/vsphere')
    const data = response.data.data
    form.host = data.host
    form.port = data.port
    form.username = data.username
    form.datacenter = data.datacenter
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

async function handleSave() {
  saving.value = true
  try {
    await api.put('/settings/vsphere', form)
    ElMessage.success('Settings saved')
  } catch (error) {
    ElMessage.error('Failed to save settings')
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  try {
    const response = await api.post('/settings/vsphere/test', form)
    ElMessage.success(`Connection successful: ${response.data.data?.version || 'connected'}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Connection failed')
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
