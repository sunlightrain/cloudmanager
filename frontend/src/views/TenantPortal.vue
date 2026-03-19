<template>
  <div class="tenant-portal">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>My Virtual Machines</span>
              <el-button type="primary" @click="showCreateDialog = true">
                <el-icon><Plus /></el-icon>
                Request New VM
              </el-button>
            </div>
          </template>
          
          <div class="filter-bar">
            <el-input v-model="searchQuery" placeholder="Search VMs..." clearable style="width: 200px">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="statusFilter" placeholder="Status" clearable style="width: 140px">
              <el-option label="All" value="" />
              <el-option label="Running" value="poweredOn" />
              <el-option label="Stopped" value="poweredOff" />
              <el-option label="Suspended" value="suspended" />
            </el-select>
          </div>
          
          <el-table :data="filteredVms" v-loading="loading" max-height="400">
            <el-table-column prop="name" label="Name" min-width="150" />
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cpu" label="CPU" width="60" align="center" />
            <el-table-column prop="memory_mb" label="Memory" width="80" align="center">
              <template #default="{ row }">{{ formatMemory(row.memory_mb) }}</template>
            </el-table-column>
            <el-table-column prop="ip_address" label="IP Address" width="130" />
            <el-table-column label="Actions" width="200" fixed="right">
              <template #default="{ row }">
                <el-button-group size="small">
                  <el-button @click="openConsole(row)" title="Console">
                    <el-icon><Monitor /></el-icon>
                  </el-button>
                  <el-button v-if="row.status === 'poweredOff'" @click="handleAction(row, 'power-on')">
                    <el-icon><VideoPlay /></el-icon>
                  </el-button>
                  <el-button v-if="row.status === 'poweredOn'" @click="handleAction(row, 'power-off')">
                    <el-icon><VideoPause /></el-icon>
                  </el-button>
                  <el-button @click="showResizeDialog(row)">
                    <el-icon><Setting /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card shadow="hover" style="margin-top: 20px">
          <template #header>
            <span>My Resource Usage</span>
          </template>
          <div class="resource-usage">
            <div class="usage-item">
              <div class="usage-label">CPU Cores</div>
              <el-progress :percentage="cpuUsagePercent" :stroke-width="20">
                <template #default>{{ myResources.cpuUsed }} / {{ myResources.cpuTotal }} cores</template>
              </el-progress>
            </div>
            <div class="usage-item">
              <div class="usage-label">Memory</div>
              <el-progress :percentage="memoryUsagePercent" :stroke-width="20" color="#409eff">
                <template #default>{{ formatMemory(myResources.memoryUsed) }} / {{ formatMemory(myResources.memoryTotal) }}</template>
              </el-progress>
            </div>
            <div class="usage-item">
              <div class="usage-label">Storage</div>
              <el-progress :percentage="storageUsagePercent" :stroke-width="20" color="#67c23a">
                <template #default>{{ myResources.storageUsed }} / {{ myResources.storageTotal }} GB</template>
              </el-progress>
            </div>
            <div class="usage-item">
              <div class="usage-label">VMs</div>
              <el-progress :percentage="vmUsagePercent" :stroke-width="20" color="#e6a23c">
                <template #default>{{ myVms.length }} / {{ myResources.vmLimit }} VMs</template>
              </el-progress>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>Quota & Limits</span>
          </template>
          <div class="quota-info">
            <div class="quota-item">
              <el-icon><Cpu /></el-icon>
              <span class="quota-label">CPU Cores</span>
              <span class="quota-value">{{ myResources.cpuTotal }}</span>
            </div>
            <div class="quota-item">
              <el-icon><Memo /></el-icon>
              <span class="quota-label">Memory</span>
              <span class="quota-value">{{ formatMemory(myResources.memoryTotal) }}</span>
            </div>
            <div class="quota-item">
              <el-icon><Box /></el-icon>
              <span class="quota-label">Storage</span>
              <span class="quota-value">{{ myResources.storageTotal }} GB</span>
            </div>
            <div class="quota-item">
              <el-icon><Cpu /></el-icon>
              <span class="quota-label">Max VMs</span>
              <span class="quota-value">{{ myResources.vmLimit }}</span>
            </div>
          </div>
        </el-card>
        
        <el-card shadow="hover" style="margin-top: 20px">
          <template #header>
            <span>Quick Actions</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" plain @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              Request VM
            </el-button>
            <el-button type="success" plain @click="handleActionBatch('power-on')" :disabled="selectedVms.length === 0">
              <el-icon><VideoPlay /></el-icon>
              Start Selected
            </el-button>
            <el-button type="warning" plain @click="handleActionBatch('power-off')" :disabled="selectedVms.length === 0">
              <el-icon><VideoPause /></el-icon>
              Stop Selected
            </el-button>
            <el-button type="danger" plain @click="handleActionBatch('delete')" :disabled="selectedVms.length === 0">
              <el-icon><Delete /></el-icon>
              Delete Selected
            </el-button>
          </div>
        </el-card>
        
        <el-card shadow="hover" style="margin-top: 20px">
          <template #header>
            <span>My Requests</span>
          </template>
          <el-scrollbar height="200px">
            <div v-if="myRequests.length === 0" class="no-requests">
              No pending requests
            </div>
            <div v-else class="request-list">
              <div v-for="req in myRequests" :key="req.id" class="request-item">
                <div class="request-info">
                  <span class="request-type">{{ req.type }}</span>
                  <span class="request-status">
                    <el-tag :type="getRequestStatusType(req.status)" size="small">{{ req.status }}</el-tag>
                  </span>
                </div>
                <div class="request-detail">{{ req.detail }}</div>
                <div class="request-time">{{ formatTime(req.created_at) }}</div>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
    
    <el-dialog v-model="showCreateDialog" title="Request New VM" width="600px">
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="VM Name">
          <el-input v-model="createForm.name" placeholder="my-vm-01" />
        </el-form-item>
        <el-form-item label="CPU Cores">
          <el-input-number v-model="createForm.cpu" :min="1" :max="myResources.cpuTotal - myResources.cpuUsed" />
        </el-form-item>
        <el-form-item label="Memory">
          <el-input-number v-model="createForm.memory_mb" :min="512" :max="myResources.memoryTotal - myResources.memoryUsed" :step="512" />
          <span class="form-hint">MB</span>
        </el-form-item>
        <el-form-item label="Disk Size">
          <el-input-number v-model="createForm.disk_gb" :min="10" :max="myResources.storageTotal" />
          <span class="form-hint">GB</span>
        </el-form-item>
        <el-form-item label="Operating System">
          <el-select v-model="createForm.guest_id" placeholder="Select OS">
            <el-option label="Ubuntu 22.04" value="ubuntu64Guest" />
            <el-option label="Ubuntu 20.04" value="ubuntu64Guest" />
            <el-option label="CentOS 7" value="centos7_64Guest" />
            <el-option label="CentOS 8" value="centos8_64Guest" />
            <el-option label="Windows Server 2019" value="windows9_64Guest" />
            <el-option label="Windows Server 2022" value="windows9_64Guest" />
          </el-select>
        </el-form-item>
        <el-form-item label="Purpose">
          <el-input v-model="createForm.description" type="textarea" rows="2" placeholder="Describe the purpose of this VM..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="submitRequest">Submit Request</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showResizeDialog" title="Resize VM" width="400px">
      <el-form label-width="100px">
        <el-form-item label="CPU Cores">
          <el-input-number v-model="resizeForm.cpu" :min="1" :max="8" />
        </el-form-item>
        <el-form-item label="Memory">
          <el-input-number v-model="resizeForm.memory_mb" :min="512" :max="65536" :step="512" />
          <span class="form-hint">MB</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResizeDialog = false">Cancel</el-button>
        <el-button type="primary" @click="submitResize">Apply Changes</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Monitor, VideoPlay, VideoPause, Setting, Delete, Cpu, Memo, Box } from '@element-plus/icons-vue'
import { vmsApi } from '@/api/vms'

const loading = ref(false)
const showCreateDialog = ref(false)
const showResizeDialog = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const selectedVms = ref<string[]>([])
const myVms = ref<any[]>([])
const myRequests = ref<any[]>([])

const createForm = ref({
  name: '',
  cpu: 1,
  memory_mb: 2048,
  disk_gb: 50,
  guest_id: 'ubuntu64Guest',
  description: ''
})

const resizeForm = ref({
  vmId: '',
  cpu: 1,
  memory_mb: 2048
})

const myResources = ref({
  cpuTotal: 32,
  cpuUsed: 8,
  memoryTotal: 65536,
  memoryUsed: 16384,
  storageTotal: 500,
  storageUsed: 200,
  vmLimit: 10
})

const filteredVms = computed(() => {
  let result = myVms.value
  if (searchQuery.value) {
    result = result.filter(vm => vm.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
  }
  if (statusFilter.value) {
    result = result.filter(vm => vm.status === statusFilter.value)
  }
  return result
})

const cpuUsagePercent = computed(() => Math.round(myResources.value.cpuUsed / myResources.value.cpuTotal * 100))
const memoryUsagePercent = computed(() => Math.round(myResources.value.memoryUsed / myResources.value.memoryTotal * 100))
const storageUsagePercent = computed(() => Math.round(myResources.value.storageUsed / myResources.value.storageTotal * 100))
const vmUsagePercent = computed(() => Math.round(myVms.value.length / myResources.value.vmLimit * 100))

function formatMemory(mb: number) {
  if (mb >= 1024) return `${(mb / 1024).toFixed(0)} GB`
  return `${mb} MB`
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

function getStatusType(status: string) {
  switch (status) {
    case 'poweredOn': return 'success'
    case 'poweredOff': return 'info'
    case 'suspended': return 'warning'
    default: return ''
  }
}

function getRequestStatusType(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'pending': return 'warning'
    case 'rejected': return 'danger'
    default: return 'info'
  }
}

async function loadMyVms() {
  loading.value = true
  try {
    const response = await vmsApi.getList({ page_size: 100 })
    myVms.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to load VMs:', error)
  } finally {
    loading.value = false
  }
}

function openConsole(vm: any) {
  window.open(`/console/${vm.vm_id}`, '_blank', 'width=1024,height=768')
}

async function handleAction(vm: any, action: string) {
  try {
    switch (action) {
      case 'power-on':
        await vmsApi.powerOn(vm.vm_id)
        ElMessage.success(`VM ${vm.name} started`)
        break
      case 'power-off':
        await vmsApi.powerOff(vm.vm_id)
        ElMessage.success(`VM ${vm.name} stopped`)
        break
    }
    loadMyVms()
  } catch (error: any) {
    ElMessage.error(`Action failed: ${error.message}`)
  }
}

async function handleActionBatch(action: string) {
  try {
    switch (action) {
      case 'power-on':
        await vmsApi.batchPowerOn(selectedVms.value)
        ElMessage.success('VMs started')
        break
      case 'power-off':
        await vmsApi.batchPowerOff(selectedVms.value)
        ElMessage.success('VMs stopped')
        break
      case 'delete':
        await ElMessageBox.confirm('Delete selected VMs?', 'Warning', { type: 'warning' })
        await vmsApi.batchDelete(selectedVms.value)
        ElMessage.success('VMs deleted')
        break
    }
    selectedVms.value = []
    loadMyVms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`Action failed: ${error.message}`)
    }
  }
}

function showResizeDialog(vm: any) {
  resizeForm.value = {
    vmId: vm.vm_id,
    cpu: vm.cpu,
    memory_mb: vm.memory_mb
  }
  showResizeDialog.value = true
}

async function submitResize() {
  try {
    await vmsApi.hotResize(resizeForm.value.vmId, {
      cpu: resizeForm.value.cpu,
      memory_mb: resizeForm.value.memory_mb
    })
    ElMessage.success('VM resized successfully')
    showResizeDialog.value = false
    loadMyVms()
  } catch (error: any) {
    ElMessage.error(`Resize failed: ${error.message}`)
  }
}

async function submitRequest() {
  if (!createForm.value.name) {
    ElMessage.warning('Please enter a VM name')
    return
  }
  
  try {
    await vmsApi.create({
      name: createForm.value.name,
      cpu: createForm.value.cpu,
      memory_mb: createForm.value.memory_mb,
      disk_gb: createForm.value.disk_gb,
      guest_id: createForm.value.guest_id
    })
    ElMessage.success('VM request submitted successfully')
    showCreateDialog.value = false
    loadMyVms()
  } catch (error: any) {
    ElMessage.error(`Request failed: ${error.message}`)
  }
}

onMounted(() => {
  loadMyVms()
})
</script>

<style scoped>
.tenant-portal {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.resource-usage {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.usage-item {
  padding: 0 10px;
}

.usage-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.quota-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quota-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.quota-item .el-icon {
  font-size: 18px;
  color: #409eff;
}

.quota-label {
  flex: 1;
  color: #606266;
}

.quota-value {
  font-weight: bold;
  color: #303133;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
}

.no-requests {
  text-align: center;
  color: #909399;
  padding: 30px 0;
}

.request-list {
  padding: 0 8px;
}

.request-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.request-item:last-child {
  border-bottom: none;
}

.request-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.request-type {
  font-weight: bold;
  color: #303133;
}

.request-detail {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.request-time {
  font-size: 11px;
  color: #909399;
}

.form-hint {
  margin-left: 8px;
  color: #909399;
}

@media (max-width: 1024px) {
  .el-col-span-16 {
    width: 100%;
  }
  
  .el-col-span-8 {
    width: 100%;
    margin-top: 20px;
  }
}
</style>
