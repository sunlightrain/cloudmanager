<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon hosts">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_hosts || overview?.hosts?.total || 0 }}</div>
            <div class="stat-label">Total Hosts</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon vms">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_vms || overview?.vms?.total || 0 }}</div>
            <div class="stat-label">Total VMs</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon running">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.vm_by_status?.poweredOn || overview?.vms?.powered_on || 0 }}</div>
            <div class="stat-label">Running VMs</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon storage">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatStorage(stats.total_storage_tb || overview?.storage?.total_gb / 1024 || 0) }}</div>
            <div class="stat-label">Total Storage</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Resource Usage</span>
              <el-select v-model="selectedDatacenter" placeholder="Select Datacenter" clearable @change="loadOverview" style="width: 150px">
                <el-option v-for="dc in datacenters" :key="dc.name" :label="dc.name" :value="dc.name" />
              </el-select>
            </div>
          </template>
          <div class="resource-grid">
            <div class="resource-item">
              <div class="resource-header">
                <span>CPU Usage</span>
                <span :class="getUsageClass(cpuUsage)">{{ cpuUsage }}%</span>
              </div>
              <el-progress :percentage="cpuUsage" :color="getUsageColor(cpuUsage)" :stroke-width="10" />
              <div class="resource-detail">
                {{ cpuCores }} cores total
              </div>
            </div>
            <div class="resource-item">
              <div class="resource-header">
                <span>Memory Usage</span>
                <span :class="getUsageClass(memoryUsage)">{{ memoryUsage }}%</span>
              </div>
              <el-progress :percentage="memoryUsage" :color="getUsageColor(memoryUsage)" :stroke-width="10" />
              <div class="resource-detail">
                {{ formatStorage(memoryTotal) }} total
              </div>
            </div>
            <div class="resource-item">
              <div class="resource-header">
                <span>Storage Usage</span>
                <span :class="getUsageClass(storageUsage)">{{ storageUsage }}%</span>
              </div>
              <el-progress :percentage="storageUsage" :color="getUsageColor(storageUsage)" :stroke-width="10" />
              <div class="resource-detail">
                {{ formatStorage(storageUsed) }} / {{ formatStorage(storageTotal) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>VM Status</span>
            </div>
          </template>
          <div class="chart-container">
            <el-progress 
              type="circle" 
              :percentage="runningPercent" 
              :width="120"
              :stroke-width="10"
              color="#67c23a"
            >
              <template #default>
                <span class="progress-value">{{ overview?.vms?.powered_on || 0 }}</span>
                <span class="progress-label">Running</span>
              </template>
            </el-progress>
            <el-progress 
              type="circle" 
              :percentage="stoppedPercent" 
              :width="120"
              :stroke-width="10"
              color="#909399"
            >
              <template #default>
                <span class="progress-value">{{ overview?.vms?.powered_off || 0 }}</span>
                <span class="progress-label">Stopped</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>Top Hosts by CPU Usage</span>
          </template>
          <el-table :data="hostTopByCpu" style="width: 100%" max-height="250" v-loading="loadingTop">
            <el-table-column prop="name" label="Host" min-width="150" show-overflow-tooltip />
            <el-table-column prop="cpu_usage_percent" label="CPU %" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.cpu_usage_percent || 0" :color="getUsageColor(row.cpu_usage_percent)" :stroke-width="6" />
              </template>
            </el-table-column>
            <el-table-column prop="cpu" label="Cores" width="80" />
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>Top Hosts by Memory Usage</span>
          </template>
          <el-table :data="hostTopByMemory" style="width: 100%" max-height="250" v-loading="loadingTop">
            <el-table-column prop="name" label="Host" min-width="150" show-overflow-tooltip />
            <el-table-column prop="memory_usage_gb" label="Memory GB" width="100">
              <template #default="{ row }">
                {{ row.memory_usage_gb?.toFixed(1) || 0 }} GB
              </template>
            </el-table-column>
            <el-table-column prop="memory" label="Total" width="100">
              <template #default="{ row }">
                {{ row.memory?.total_gb || 0 }} GB
              </template>
            </el-table-column>
          </el-table>
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
            <el-button @click="$router.push('/topology')">
              <el-icon><Connection /></el-icon>
              Topology
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
            <el-table-column prop="task_id" label="Task ID" width="220" show-overflow-tooltip />
            <el-table-column prop="task_type" label="Type" width="140" />
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
import { infraApi } from '@/api/infrastructure'
import { Monitor, Cpu, CircleCheck, Box, Plus, Setting, Document, Connection } from '@element-plus/icons-vue'

const stats = ref<any>({})
const overview = ref<any>(null)
const recentTasks = ref<any[]>([])
const tasksLoading = ref(false)
const loadingTop = ref(false)
const datacenters = ref<any[]>([])
const selectedDatacenter = ref<string>('')
const hostTopByCpu = ref<any[]>([])
const hostTopByMemory = ref<any[]>([])

const cpuUsage = computed(() => {
  return overview.value?.compute?.cpu_usage_percent || 0
})

const cpuCores = computed(() => {
  return overview.value?.compute?.total_cpu_cores || 0
})

const memoryUsage = computed(() => {
  return overview.value?.compute?.mem_usage_percent || 0
})

const memoryTotal = computed(() => {
  return overview.value?.compute?.total_memory_gb || 0
})

const storageUsage = computed(() => {
  return overview.value?.storage?.usage_percent || 0
})

const storageUsed = computed(() => {
  return overview.value?.storage?.used_gb || 0
})

const storageTotal = computed(() => {
  return overview.value?.storage?.total_gb || 0
})

const runningPercent = computed(() => {
  const total = overview.value?.vms?.total || 0
  if (!total) return 0
  return Math.round((overview.value?.vms?.powered_on || 0) / total * 100)
})

const stoppedPercent = computed(() => {
  const total = overview.value?.vms?.total || 0
  if (!total) return 0
  return Math.round((overview.value?.vms?.powered_off || 0) / total * 100)
})

function getUsageClass(value: number) {
  if (value >= 80) return 'usage-high'
  if (value >= 60) return 'usage-medium'
  return 'usage-normal'
}

function getUsageColor(value: number) {
  if (value >= 80) return '#f56c6c'
  if (value >= 60) return '#e6a23c'
  return '#67c23a'
}

function formatStorage(value: number) {
  if (value >= 1024) {
    return (value / 1024).toFixed(1) + ' TB'
  }
  return value.toFixed(1) + ' GB'
}

function getStatusType(status: string) {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
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

async function loadDatacenters() {
  try {
    const response = await infraApi.getDatacenters()
    datacenters.value = response.data.data.datacenters || []
    if (datacenters.value.length > 0) {
      selectedDatacenter.value = datacenters.value[0]?.name || ''
      loadOverview()
    }
  } catch (error) {
    console.error('Failed to load datacenters:', error)
  }
}

async function loadOverview() {
  if (!selectedDatacenter.value) return
  loadingTop.value = true
  try {
    const response = await infraApi.getDatacenterOverview(selectedDatacenter.value)
    overview.value = response.data.data
    
    const hosts: any[] = []
    for (const cluster of overview.value?.clusters?.items || []) {
      try {
        const hostsResp = await infraApi.getClusterHosts(cluster.cluster_id)
        hosts.push(...(hostsResp.data.data || []))
      } catch (e) {
        console.error('Failed to load cluster hosts:', e)
      }
    }
    
    hostTopByCpu.value = [...hosts]
      .sort((a, b) => (b.cpu_usage_percent || 0) - (a.cpu_usage_percent || 0))
      .slice(0, 5)
    
    hostTopByMemory.value = [...hosts]
      .sort((a, b) => (b.memory_usage_gb || 0) - (a.memory_usage_gb || 0))
      .slice(0, 5)
  } catch (error) {
    console.error('Failed to load overview:', error)
  } finally {
    loadingTop.value = false
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
  loadDatacenters()
  loadRecentTasks()
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 14px;
}

.stat-icon.hosts { background: #409eff20; color: #409eff; }
.stat-icon.vms { background: #e6a23c20; color: #e6a23c; }
.stat-icon.running { background: #67c23a20; color: #67c23a; }
.stat-icon.storage { background: #90939920; color: #909399; }

.stat-content { flex: 1; }

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.resource-item {
  padding: 8px 0;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.resource-detail {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.usage-high { color: #f56c6c; font-weight: bold; }
.usage-medium { color: #e6a23c; font-weight: bold; }
.usage-normal { color: #67c23a; }

.chart-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px 0;
}

.progress-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.progress-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .stat-card { flex-direction: column; text-align: center; }
  .stat-icon { margin-right: 0; margin-bottom: 10px; }
}
</style>
