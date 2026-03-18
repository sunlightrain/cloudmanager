<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>Total Hosts</span>
          </template>
          <div class="stat-value">{{ stats.total_hosts || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>Total VMs</span>
          </template>
          <div class="stat-value">{{ stats.total_vms || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>Powered On</span>
          </template>
          <div class="stat-value success">{{ stats.vm_by_status?.poweredOn || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>Powered Off</span>
          </template>
          <div class="stat-value warning">{{ stats.vm_by_status?.poweredOff || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>Quick Actions</span>
          </template>
          <el-space wrap>
            <el-button type="primary" @click="$router.push('/vms/create')">
              Create VM
            </el-button>
            <el-button type="success" @click="$router.push('/vms')">
              View All VMs
            </el-button>
            <el-button type="info" @click="$router.push('/tasks')">
              View Tasks
            </el-button>
            <el-button type="warning" @click="$router.push('/settings')">
              Settings
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'

const stats = ref<any>({})

onMounted(async () => {
  try {
    const response = await api.get('/hosts/overview')
    stats.value = response.data.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>

<style scoped>
.stat-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  padding: 20px 0;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.warning {
  color: #e6a23c;
}
</style>
