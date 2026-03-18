<template>
  <div class="vm-detail" v-loading="loading">
    <div v-if="vm">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="vm-title">
                  <span class="vm-name">{{ vm.name }}</span>
                  <el-tag :type="vm.status === 'poweredOn' ? 'success' : 'info'" size="large">
                    {{ vm.status === 'poweredOn' ? 'Running' : 'Stopped' }}
                  </el-tag>
                </div>
                <el-button-group>
                  <el-button :type="vm.status === 'poweredOn' ? 'danger' : 'success'" @click="togglePower">
                    {{ vm.status === 'poweredOn' ? 'Stop' : 'Start' }}
                  </el-button>
                  <el-button type="warning" @click="handleRestart" :disabled="vm.status !== 'poweredOn'">Restart</el-button>
                  <el-button type="primary" @click="showEditDialog = true">Edit Config</el-button>
                  <el-button type="info" @click="showCloneDialog = true">Clone</el-button>
                  <el-button type="danger" @click="handleDelete">Delete</el-button>
                </el-button-group>
              </div>
            </template>
            
            <el-tabs v-model="activeTab">
              <el-tab-pane label="Overview" name="overview">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="VM ID" :span="2">{{ vm.vm_id }}</el-descriptions-item>
                  <el-descriptions-item label="Host">{{ vm.host || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="Datastore">{{ vm.datastore || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="Guest OS">{{ vm.guest_full_name || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="Guest ID">{{ vm.guest_id || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="IP Address">
                    <el-tag v-if="vm.ip_address" type="success">{{ vm.ip_address }}</el-tag>
                    <span v-else>N/A</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="Created">{{ vm.created || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="CPU">{{ vm.cpu }} cores</el-descriptions-item>
                  <el-descriptions-item label="Memory">{{ formatMemory(vm.memory_mb) }}</el-descriptions-item>
                  <el-descriptions-item label="CPU Reservation">{{ vm.cpu_reservation || 0 }} MHz</el-descriptions-item>
                  <el-descriptions-item label="Memory Reservation">{{ formatMemory(vm.memory_reservation || 0) }}</el-descriptions-item>
                  <el-descriptions-item label="Annotation" :span="2">{{ vm.annotation || 'N/A' }}</el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              
              <el-tab-pane label="Hardware" name="hardware">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="CPU">
                    <el-progress :percentage="50" :stroke-width="8" :show-text="false" />
                    <span class="hardware-info">{{ vm.cpu }} cores</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="Memory">
                    <el-progress :percentage="memoryPercent" :stroke-width="8" :show-text="false" color="#409eff" />
                    <span class="hardware-info">{{ formatMemory(vm.memory_mb) }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="Network Adapters">
                    <el-tag v-for="i in vm.num_ethernet_cards || 0" :key="i" style="margin-right: 8px">
                      Network Adapter {{ i }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="Disks">
                    <div v-if="vm.disks && vm.disks.length > 0">
                      <div v-for="disk in vm.disks" :key="disk.label" class="disk-item">
                        <span>{{ disk.label }}</span>
                        <span>{{ disk.capacity_gb || (disk.capacity_kb / 1024 / 1024).toFixed(0) }} GB</span>
                      </div>
                    </div>
                    <span v-else>No disk information</span>
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              
              <el-tab-pane label="Performance" name="performance">
                <el-row :gutter="20">
                  <el-col :span="8">
                    <div class="perf-card">
                      <div class="perf-label">CPU Usage</div>
                      <el-progress type="circle" :percentage="performance.cpu_usage" :width="100" :stroke-width="10">
                        <template #default>
                          <span class="perf-value">{{ performance.cpu_usage }}%</span>
                        </template>
                      </el-progress>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="perf-card">
                      <div class="perf-label">Memory Usage</div>
                      <el-progress type="circle" :percentage="performance.memory_usage" :width="100" :stroke-width="10" color="#409eff">
                        <template #default>
                          <span class="perf-value">{{ performance.memory_usage }}%</span>
                        </template>
                      </el-progress>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="perf-card">
                      <div class="perf-label">Uptime</div>
                      <div class="perf-value uptime">{{ formatUptime(performance.uptime_seconds) }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-tab-pane>
              
              <el-tab-pane label="Actions" name="actions">
                <div class="actions-grid">
                  <el-button type="primary" size="large" @click="$router.push(`/vms/${vm.vm_id}/snapshots`)">
                    <el-icon><Camera /></el-icon>
                    Manage Snapshots
                  </el-button>
                  <el-button type="success" size="large" @click="showConsoleDialog = true">
                    <el-icon><Monitor /></el-icon>
                    Open Console
                  </el-button>
                  <el-button type="warning" size="large" @click="showEditDialog = true">
                    <el-icon><Edit /></el-icon>
                    Edit Configuration
                  </el-button>
                  <el-button type="info" size="large" @click="showCloneDialog = true">
                    <el-icon><CopyDocument /></el-icon>
                    Clone VM
                  </el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <span>Quick Info</span>
            </template>
            <div class="quick-info">
              <div class="info-item">
                <el-icon><Monitor /></el-icon>
                <span>Status</span>
                <el-tag :type="vm.status === 'poweredOn' ? 'success' : 'info'">
                  {{ vm.status === 'poweredOn' ? 'Running' : 'Stopped' }}
                </el-tag>
              </div>
              <div class="info-item">
                <el-icon><Cpu /></el-icon>
                <span>CPU</span>
                <span>{{ vm.cpu }} cores</span>
              </div>
              <div class="info-item">
                <el-icon><MemoryStick /></el-icon>
                <span>Memory</span>
                <span>{{ formatMemory(vm.memory_mb) }}</span>
              </div>
              <div class="info-item">
                <el-icon><IpAddress /></el-icon>
                <span>IP</span>
                <span>{{ vm.ip_address || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <el-icon><Office /></el-icon>
                <span>Host</span>
                <span>{{ vm.host || 'N/A' }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <el-dialog v-model="showEditDialog" title="Edit VM Configuration" width="500px">
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="CPU Cores">
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
    
    <el-dialog v-model="showCloneDialog" title="Clone VM" width="500px">
      <el-form :model="cloneForm" label-width="100px">
        <el-form-item label="New VM Name">
          <el-input v-model="cloneForm.name" placeholder="Enter new VM name" />
        </el-form-item>
        <el-form-item label="Resource Pool">
          <el-input v-model="cloneForm.resource_pool" placeholder="Optional" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloneDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleClone" :loading="cloning">Clone</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showConsoleDialog" title="VM Console" width="800px" top="5vh">
      <div class="console-placeholder">
        <el-icon size="64"><Monitor /></el-icon>
        <p>VM Console requires WebMKS or VMRC integration</p>
        <p class="console-info">Web Console URL: https://{{ vm?.host }}/?vmId={{ vm?.vm_id }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vmsApi, type VM, type VMUpdate } from '@/api/vms'
import { cloneApi } from '@/api/clone'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, Cpu, MemoryStick, IpAddress, Office, Camera, Edit, CopyDocument } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const vm = ref<VM | null>(null)
const loading = ref(false)
const activeTab = ref('overview')
const showEditDialog = ref(false)
const showCloneDialog = ref(false)
const showConsoleDialog = ref(false)
const cloning = ref(false)
const performance = ref({
  cpu_usage: 0,
  memory_usage: 0,
  uptime_seconds: 0
})

const editForm = reactive<VMUpdate>({
  cpu: 2,
  memory_mb: 4096
})

const cloneForm = reactive({
  name: '',
  resource_pool: ''
})

const memoryPercent = computed(() => {
  return Math.min(Math.round((vm.value?.memory_mb || 0) / 131072 * 100), 100)
})

function formatMemory(mb: number) {
  if (mb >= 1024) {
    return (mb / 1024).toFixed(1) + ' GB'
  }
  return mb + ' MB'
}

function formatUptime(seconds: number) {
  if (!seconds) return 'N/A'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

async function loadVM() {
  loading.value = true
  try {
    const response = await vmsApi.getById(route.params.id as string)
    vm.value = response.data.data
    if (vm.value) {
      editForm.cpu = vm.value.cpu
      editForm.memory_mb = vm.value.memory_mb
    }
    loadPerformance()
  } catch (error) {
    console.error('Failed to load VM:', error)
    ElMessage.error('Failed to load VM')
  } finally {
    loading.value = false
  }
}

async function loadPerformance() {
  try {
    const response = await api.get(`/vms/${route.params.id}/performance`)
    if (response.data.data) {
      performance.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to load performance:', error)
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

async function handleRestart() {
  if (!vm.value) return
  
  try {
    await ElMessageBox.confirm('Are you sure you want to restart this VM?', 'Confirm', { type: 'warning' })
    await vmsApi.power(vm.value.vm_id, 'restart')
    ElMessage.success('VM restart initiated')
    loadVM()
  } catch (error) {
    ElMessage.error('Failed to restart VM')
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

async function handleClone() {
  if (!vm.value || !cloneForm.name) {
    ElMessage.warning('Please enter new VM name')
    return
  }
  
  cloning.value = true
  try {
    await cloneApi.clone({
      vm_id: vm.value.vm_id,
      name: cloneForm.name,
      resource_pool: cloneForm.resource_pool
    })
    ElMessage.success('VM clone started')
    showCloneDialog.value = false
    cloneForm.name = ''
    cloneForm.resource_pool = ''
  } catch (error) {
    ElMessage.error('Failed to clone VM')
  } finally {
    cloning.value = false
  }
}

async function handleDelete() {
  if (!vm.value) return
  
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this VM? This action cannot be undone!', 'Confirm', { type: 'error' })
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

.vm-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vm-name {
  font-size: 18px;
  font-weight: 600;
}

.hardware-info {
  margin-left: 10px;
  color: #606266;
}

.disk-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.disk-item:last-child {
  border-bottom: none;
}

.perf-card {
  text-align: center;
  padding: 20px;
}

.perf-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
}

.perf-value {
  font-size: 20px;
  font-weight: 600;
}

.perf-value.uptime {
  font-size: 24px;
  margin-top: 20px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  padding: 20px;
}

.actions-grid .el-button {
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.quick-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-item .el-icon {
  font-size: 18px;
  color: #409eff;
}

.info-item span:first-of-type {
  color: #909399;
  width: 80px;
}

.console-placeholder {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  color: #fff;
}

.console-placeholder .el-icon {
  color: #409eff;
  margin-bottom: 20px;
}

.console-info {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
