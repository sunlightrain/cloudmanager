<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/hosts')">
          <div class="stat-icon hosts">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_hosts || 0 }}</div>
            <div class="stat-label">Total Hosts</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/vms')">
          <div class="stat-icon vms">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_vms || 0 }}</div>
            <div class="stat-label">Total VMs</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon running">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.vm_by_status?.poweredOn || 0 }}</div>
            <div class="stat-label">Running VMs</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
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
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon memory">
            <el-icon><Memo /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_memory_gb || 0 }} GB</div>
            <div class="stat-label">Total Memory</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card warning" @click="$router.push('/alerts')">
          <div class="stat-icon alerts">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ alertCount }}</div>
            <div class="stat-label">Active Alerts</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="14" :lg="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Resource Usage Overview</span>
              <el-button text @click="$router.push('/topology')">
                <el-icon><Connection /></el-icon>
                Topology
              </el-button>
            </div>
          </template>
          <div class="resource-charts">
            <div class="chart-item">
              <div class="chart-title">VM Status</div>
              <el-progress 
                type="circle" 
                :percentage="runningPercent" 
                :width="120"
                :stroke-width="10"
                color="#67c23a"
              >
                <template #default>
                  <span class="progress-main">{{ stats.vm_by_status?.poweredOn || 0 }}</span>
                  <span class="progress-sub">Running</span>
                </template>
              </el-progress>
              <div class="chart-legend">
                <span class="legend-item running">Running: {{ stats.vm_by_status?.poweredOn || 0 }}</span>
                <span class="legend-item stopped">Stopped: {{ stats.vm_by_status?.poweredOff || 0 }}</span>
              </div>
            </div>
            <div class="chart-item">
              <div class="chart-title">Storage Usage</div>
              <el-progress 
                type="circle" 
                :percentage="stats.used_storage_percent || 0" 
                :width="120"
                :stroke-width="10"
                :color="storageColor"
              >
                <template #default>
                  <span class="progress-main">{{ stats.used_storage_percent || 0 }}%</span>
                  <span class="progress-sub">Used</span>
                </template>
              </el-progress>
              <div class="chart-legend">
                <span class="legend-item">Used: {{ (stats.used_storage_tb || 0).toFixed(1) }} TB</span>
                <span class="legend-item">Free: {{ ((stats.total_storage_tb || 0) - (stats.used_storage_tb || 0)).toFixed(1) }} TB</span>
              </div>
            </div>
            <div class="chart-item">
              <div class="chart-title">Memory Usage</div>
              <el-progress 
                type="circle" 
                :percentage="memoryUsagePercent" 
                :width="120"
                :stroke-width="10"
                :color="memoryColor"
              >
                <template #default>
                  <span class="progress-main">{{ memoryUsagePercent }}%</span>
                  <span class="progress-sub">Used</span>
                </template>
              </el-progress>
              <div class="chart-legend">
                <span class="legend-item">Used: {{ (usedMemoryGB).toFixed(0) }} GB</span>
                <span class="legend-item">Total: {{ (stats.total_memory_gb || 0).toFixed(0) }} GB</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="24" :md="10" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Top Resources</span>
            </div>
          </template>
          <el-table :data="topHosts" size="small" max-height="280">
            <el-table-column prop="name" label="Host" show-overflow-tooltip />
            <el-table-column prop="vmCount" label="VMs" width="60" align="center" />
            <el-table-column prop="cpuUsage" label="CPU %" width="70" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.cpuUsage" :stroke-width="8" :color="cpuColor(row.cpuUsage)" />
              </template>
            </el-table-column>
            <el-table-column prop="memUsage" label="MEM %" width="70" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.memUsage" :stroke-width="8" :color="memColor(row.memUsage)" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <span>Quick Actions</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="showBatchDialog('power-on')" :disabled="selectedVms.length === 0">
              <el-icon><VideoPlay /></el-icon>
              Batch Start
            </el-button>
            <el-button type="warning" @click="showBatchDialog('power-off')" :disabled="selectedVms.length === 0">
              <el-icon><VideoPause /></el-icon>
              Batch Stop
            </el-button>
            <el-button type="danger" @click="showBatchDialog('delete')" :disabled="selectedVms.length === 0">
              <el-icon><Delete /></el-icon>
              Batch Delete
            </el-button>
            <el-button type="success" @click="$router.push('/vms/create')">
              <el-icon><Plus /></el-icon>
              Create VM
            </el-button>
          </div>
          <div class="selected-info" v-if="selectedVms.length > 0">
            {{ selectedVms.length }} VMs selected
            <el-button text size="small" @click="selectedVms = []">Clear</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <span>Recent Alerts</span>
          </template>
          <el-scrollbar height="150px">
            <div v-if="alerts.length === 0" class="no-alerts">
              No active alerts
            </div>
            <div v-else class="alert-list">
              <div v-for="alert in alerts.slice(0, 5)" :key="alert.id" class="alert-item">
                <el-icon :color="alertColor(alert.level)"><Warning /></el-icon>
                <span class="alert-message">{{ alert.message }}</span>
                <span class="alert-time">{{ formatTime(alert.time) }}</span>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <span>Recent Tasks</span>
          </template>
          <el-scrollbar height="150px">
            <div v-if="recentTasks.length === 0" class="no-tasks">
              No recent tasks
            </div>
            <div v-else class="task-list">
              <div v-for="task in recentTasks.slice(0, 5)" :key="task.task_id" class="task-item">
                <span class="task-type">{{ task.task_type }}</span>
                <el-tag :type="getStatusType(task.status)" size="small">{{ task.status }}</el-tag>
                <span class="task-time">{{ formatTime(task.created_at) }}</span>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Virtual Machines</span>
              <el-checkbox v-model="selectionMode" @change="toggleSelectionMode">Selection Mode</el-checkbox>
            </div>
          </template>
          <el-table 
            ref="vmTableRef"
            :data="vms" 
            v-loading="vmsLoading"
            @selection-change="handleSelectionChange"
            max-height="350"
          >
            <el-table-column v-if="selectionMode" type="selection" width="40" />
            <el-table-column prop="name" label="Name" min-width="150" show-overflow-tooltip />
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="getVmStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="host" label="Host" width="120" show-overflow-tooltip />
            <el-table-column prop="cpu" label="CPU" width="60" align="center" />
            <el-table-column prop="memory_mb" label="Memory" width="80" align="center">
              <template #default="{ row }">{{ (row.memory_mb / 1024).toFixed(0) }} GB</template>
            </el-table-column>
            <el-table-column prop="ip_address" label="IP" width="130" show-overflow-tooltip />
            <el-table-column label="Actions" width="200" fixed="right">
              <template #default="{ row }">
                <el-button-group size="small">
                  <el-button @click="handleConsole(row)" title="Console">
                    <el-icon><Monitor /></el-icon>
                  </el-button>
                  <el-button 
                    v-if="row.status === 'poweredOff'" 
                    @click="handlePowerOn(row)"
                    title="Power On"
                  >
                    <el-icon><VideoPlay /></el-icon>
                  </el-button>
                  <el-button 
                    v-if="row.status === 'poweredOn'" 
                    @click="handlePowerOff(row)"
                    title="Power Off"
                  >
                    <el-icon><VideoPause /></el-icon>
                  </el-button>
                  <el-button @click="$router.push(`/vms/${row.vm_id}`)" title="Details">
                    <el-icon><InfoFilled /></el-icon>
                  </el-button>
                  <el-button @click="handleDelete(row)" type="danger" title="Delete">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-dialog v-model="batchDialogVisible" title="Batch Operation" width="400px">
      <p>Are you sure you want to {{ batchAction }} {{ selectedVms.length }} VMs?</p>
      <template #footer>
        <el-button @click="batchDialogVisible = false">Cancel</el-button>
        <el-button :type="batchAction === 'delete' ? 'danger' : 'primary'" @click="executeBatch">
          Confirm
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { inventoryApi } from '@/api/inventory'
import { vmsApi } from '@/api/vms'
import { tasksApi } from '@/api/tasks'
import { Monitor, Cpu, CircleCheck, Box, Plus, Setting, Document, Warning, Connection, VideoPlay, VideoPause, Delete, InfoFilled, Memo } from '@element-plus/icons-vue'

const stats = ref<any>({})
const vms = ref<any[]>([])
const recentTasks = ref<any[]>([])
const alerts = ref<any[]>([])
const alertCount = ref(0)
const topHosts = ref<any[]>([])
const vmsLoading = ref(false)
const selectionMode = ref(false)
const selectedVms = ref<string[]>([])
const batchDialogVisible = ref(false)
const batchAction = ref('')
const vmTableRef = ref()

const runningPercent = computed(() => {
  if (!stats.value.total_vms) return 0
  return Math.round((stats.value.vm_by_status?.poweredOn || 0) / stats.value.total_vms * 100)
})

const memoryUsagePercent = computed(() => {
  if (!stats.value.total_memory_gb) return 0
  const used = stats.value.used_memory_gb || 0
  return Math.round(used / stats.value.total_memory_gb * 100)
})

const usedMemoryGB = computed(() => stats.value.used_memory_gb || 0)

const storageColor = computed(() => {
  const p = stats.value.used_storage_percent || 0
  if (p > 90) return '#f56c6c'
  if (p > 70) return '#e6a23c'
  return '#67c23a'
})

const memoryColor = computed(() => {
  const p = memoryUsagePercent.value
  if (p > 90) return '#f56c6c'
  if (p > 70) return '#e6a23c'
  return '#409eff'
})

function cpuColor(val: number) {
  if (val > 90) return '#f56c6c'
  if (val > 70) return '#e6a23c'
  return '#67c23a'
}

function memColor(val: number) {
  if (val > 90) return '#f56c6c'
  if (val > 70) return '#e6a23c'
  return '#409eff'
}

function alertColor(level: string) {
  switch (level) {
    case 'critical': return '#f56c6c'
    case 'warning': return '#e6a23c'
    default: return '#909399'
  }
}

function getVmStatusType(status: string) {
  switch (status) {
    case 'poweredOn': return 'success'
    case 'poweredOff': return 'info'
    case 'suspended': return 'warning'
    default: return ''
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = (now.getTime() - date.getTime()) / 1000
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return date.toLocaleDateString()
}

async function loadStats() {
  try {
    const response = await inventoryApi.getOverview()
    stats.value = response.data.data || {}
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadVms() {
  vmsLoading.value = true
  try {
    const response = await vmsApi.getList({ page_size: 100 })
    vms.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to load VMs:', error)
  } finally {
    vmsLoading.value = false
  }
}

async function loadRecentTasks() {
  try {
    const response = await tasksApi.getList({ page_size: 5 })
    recentTasks.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

function handleSelectionChange(selection: any[]) {
  selectedVms.value = selection.map(item => item.vm_id)
}

function toggleSelectionMode() {
  if (!selectionMode.value) {
    selectedVms.value = []
    vmTableRef.value?.clearSelection()
  }
}

function showBatchDialog(action: string) {
  batchAction.value = action
  batchDialogVisible.value = true
}

async function executeBatch() {
  batchDialogVisible.value = false
  try {
    let result
    switch (batchAction.value) {
      case 'power-on':
        result = await vmsApi.batchPowerOn(selectedVms.value)
        break
      case 'power-off':
        result = await vmsApi.batchPowerOff(selectedVms.value)
        break
      case 'delete':
        await ElMessageBox.confirm('This action cannot be undone. Continue?', 'Warning', { type: 'warning' })
        result = await vmsApi.batchDelete(selectedVms.value)
        break
    }
    ElMessage.success(`Batch ${batchAction.value} completed`)
    selectedVms.value = []
    loadVms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`Batch operation failed: ${error.message}`)
    }
  }
}

async function handlePowerOn(row: any) {
  try {
    await vmsApi.powerOn(row.vm_id)
    ElMessage.success(`VM ${row.name} powered on`)
    loadVms()
  } catch (error: any) {
    ElMessage.error(`Failed: ${error.message}`)
  }
}

async function handlePowerOff(row: any) {
  try {
    await vmsApi.powerOff(row.vm_id)
    ElMessage.success(`VM ${row.name} powered off`)
    loadVms()
  } catch (error: any) {
    ElMessage.error(`Failed: ${error.message}`)
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`Delete VM ${row.name}?`, 'Warning', { type: 'warning' })
    await vmsApi.delete(row.vm_id)
    ElMessage.success(`VM ${row.name} deleted`)
    loadVms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`Failed: ${error.message}`)
    }
  }
}

function handleConsole(row: any) {
  window.open(`/console/${row.vm_id}`, '_blank', 'width=1024,height=768')
}

onMounted(() => {
  loadStats()
  loadVms()
  loadRecentTasks()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-row {
  margin-bottom: 0;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card.warning .stat-value {
  color: #e6a23c;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  margin-bottom: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
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
.stat-icon.memory { background: #409eff20; color: #409eff; }
.stat-icon.alerts { background: #f56c6c20; color: #f56c6c; }

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-charts {
  display: flex;
  justify-content: space-around;
  padding: 10px 0;
}

.chart-item {
  text-align: center;
}

.chart-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.progress-main {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.progress-sub {
  display: block;
  font-size: 11px;
  color: #909399;
}

.chart-legend {
  margin-top: 10px;
  font-size: 11px;
  color: #606266;
}

.legend-item {
  display: block;
  margin: 2px 0;
}

.legend-item.running { color: #67c23a; }
.legend-item.stopped { color: #909399; }

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.selected-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-alerts, .no-tasks {
  text-align: center;
  color: #909399;
  padding: 30px 0;
}

.alert-list, .task-list {
  padding: 0 8px;
}

.alert-item, .task-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.alert-item:last-child, .task-item:last-child {
  border-bottom: none;
}

.alert-message {
  flex: 1;
  margin: 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-time, .task-time {
  font-size: 11px;
  color: #909399;
  min-width: 50px;
}

.task-type {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
  
  .stat-card {
    padding: 12px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .resource-charts {
    flex-direction: column;
    align-items: center;
  }
  
  .chart-item {
    margin-bottom: 20px;
  }
}
</style>
