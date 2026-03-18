<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon hosts">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_hosts || 0 }}</div>
            <div class="stat-label">Total Hosts</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon vms">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_vms || 0 }}</div>
            <div class="stat-label">Total VMs</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon running">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.vm_by_status?.poweredOn || 0 }}</div>
            <div class="stat-label">Running</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon storage">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_storage_tb || 0 }} TB</div>
            <div class="stat-label">Total Storage</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>VM Status Distribution</span>
          </template>
          <div class="chart-container">
            <el-progress 
              type="circle" 
              :percentage="runningPercent" 
              :width="150"
              :stroke-width="12"
              color="#67c23a"
            >
              <template #default>
                <span class="progress-label">Running</span>
              </template>
            </el-progress>
            <el-progress 
              type="circle" 
              :percentage="stoppedPercent" 
              :width="150"
              :stroke-width="12"
              color="#909399"
            >
              <template #default>
                <span class="progress-label">Stopped</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>Storage Usage</span>
          </template>
          <div class="storage-info">
            <el-progress 
              :percentage="stats.used_storage_percent || 0" 
              :stroke-width="20"
              :text-inside="true"
            >
              <span>{{ stats.used_storage_percent || 0 }}% Used</span>
            </el-progress>
            <div class="storage-details">
              <div>Used: {{ (stats.used_storage_tb || 0).toFixed(2) }} TB</div>
              <div>Available: {{ ((stats.total_storage_tb || 0) - (stats.used_storage_tb || 0)).toFixed(2) }} TB</div>
              <div>Total: {{ (stats.total_storage_tb || 0).toFixed(2) }} TB</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Quick Actions</span>
            </div>
          </template>
          <el-space wrap :size="12">
            <el-button type="primary" @click="$router.push('/vms/create')">
              <el-icon><Plus /></el-icon>
              Create VM
            </el-button>
            <el-button type="success" @click="$router.push('/vms')">
              <el-icon><Monitor /></el-icon>
              View All VMs
            </el-button>
            <el-button type="info" @click="$router.push('/hosts')">
              <el-icon><Cpu /></el-icon>
              Hosts
            </el-button>
            <el-button type="warning" @click="$router.push('/datastores')">
              <el-icon><Box /></el-icon>
              Datastores
            </el-button>
            <el-button type="danger" @click="$router.push('/tasks')">
              <el-icon><Document /></el-icon>
              Tasks
            </el-button>
            <el-button @click="$router.push('/settings')">
              <el-icon><Setting /></el-icon>
              Settings
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>Recent Tasks</span>
          </template>
          <el-table :data="recentTasks" v-loading="tasksLoading" max-height="300">
            <el-table-column prop="task_id" label="Task ID" width="280" show-overflow-tooltip />
            <el-table-column prop="task_type" label="Type" width="120" />
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="Created" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { tasksApi } from '@/api/tasks'
import { Monitor, Cpu, CircleCheck, Box, Plus, Setting, Document } from '@element-plus/icons-vue'

const stats = ref<any>({})
const recentTasks = ref<any[]>([])
const tasksLoading = ref(false)

const runningPercent = computed(() => {
  if (!stats.value.total_vms) return 0
  return Math.round((stats.value.vm_by_status?.poweredOn || 0) / stats.value.total_vms * 100)
})

const stoppedPercent = computed(() => {
  if (!stats.value.total_vms) return 0
  return Math.round((stats.value.vm_by_status?.poweredOff || 0) / stats.value.total_vms * 100)
})

function getStatusType(status: string) {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

async function loadStats() {
  try {
    const response = await api.get('/hosts/overview')
    stats.value = response.data.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadRecentTasks() {
  tasksLoading.value = true
  try {
    const response = await tasksApi.getList({ page_size: 5 })
    recentTasks.value = response.data.data.items
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    tasksLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadRecentTasks()
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 16px;
}

.stat-icon.hosts { background: #409eff20; color: #409eff; }
.stat-icon.vms { background: #e6a23c20; color: #e6a23c; }
.stat-icon.running { background: #67c23a20; color: #67c23a; }
.stat-icon.storage { background: #90939920; color: #909399; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px 0;
}

.progress-label {
  font-size: 14px;
  color: #606266;
}

.storage-info {
  padding: 20px 0;
}

.storage-details {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  color: #606266;
  font-size: 14px;
}
</style>
