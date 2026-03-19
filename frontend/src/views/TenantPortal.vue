<template>
  <div class="tenant-portal">
    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 20px">
      <template #title>
        Welcome to Tenant Self-Service Portal
      </template>
      <template #default>
        Create and manage your department's virtual machines without administrator assistance.
      </template>
    </el-alert>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="quota-card">
          <div class="quota-header">
            <span>My Quota</span>
            <el-tag type="success">Active</el-tag>
          </div>
          <div class="quota-stats">
            <div class="quota-item">
              <span class="label">VMs Allowed</span>
              <span class="value">{{ quota.vm_limit }}</span>
            </div>
            <div class="quota-item">
              <span class="label">VMs Used</span>
              <span class="value">{{ myVms.length }} / {{ quota.vm_limit }}</span>
            </div>
            <div class="quota-item">
              <span class="label">CPU Cores</span>
              <span class="value">{{ quota.cpu_limit }}</span>
            </div>
            <div class="quota-item">
              <span class="label">Memory</span>
              <span class="value">{{ quota.memory_limit_gb }} GB</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="18">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Quick Actions</span>
            </div>
          </template>
          <el-space wrap :size="12">
            <el-button type="primary" @click="showCreateDialog = true" :disabled="myVms.length >= quota.vm_limit">
              <el-icon><Plus /></el-icon>
              New VM
            </el-button>
            <el-button @click="showQuotaDialog = true">
              <el-icon><Money /></el-icon>
              Request Quota
            </el-button>
            <el-button type="warning" @click="showRequestDialog = true">
              <el-icon><Document /></el-icon>
              My Requests
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>My Virtual Machines</span>
          <el-space>
            <el-input v-model="searchQuery" placeholder="Search VMs" clearable style="width: 200px" />
            <el-select v-model="statusFilter" placeholder="Status" clearable style="width: 120px">
              <el-option label="Running" value="poweredOn" />
              <el-option label="Stopped" value="poweredOff" />
            </el-select>
          </el-space>
        </div>
      </template>
      
      <el-table :data="filteredVms" v-loading="loading" stripe>
        <el-table-column prop="name" label="Name" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'poweredOn' ? 'success' : 'info'">
              {{ row.status === 'poweredOn' ? 'Running' : 'Stopped' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cpu" label="CPU" width="80" />
        <el-table-column prop="memory_mb" label="Memory" width="100">
          <template #default="{ row }">
            {{ (row.memory_mb / 1024).toFixed(1) }} GB
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP Address" width="140" show-overflow-tooltip />
        <el-table-column label="Actions" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group size="small">
              <el-button @click="togglePower(row)">
                {{ row.status === 'poweredOn' ? 'Stop' : 'Start' }}
              </el-button>
              <el-button @click="openConsole(row)" :disabled="row.status !== 'poweredOn'">
                Console
              </el-button>
              <el-button @click="viewDetails(row)">
                Details
              </el-button>
              <el-button type="danger" @click="deleteVm(row)" :disabled="row.status === 'poweredOn'">
                Delete
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="Create New VM" width="600px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="VM Name" prop="name">
          <el-input v-model="createForm.name" placeholder="e.g., web-server-01" />
        </el-form-item>
        <el-form-item label="Template" prop="template">
          <el-select v-model="createForm.template" placeholder="Select template" style="width: 100%">
            <el-option label="Ubuntu 22.04" value="ubuntu22" />
            <el-option label="CentOS 7" value="centos7" />
            <el-option label="Windows Server 2019" value="win2019" />
            <el-option label="Custom (Blank)" value="custom" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="CPU Cores" prop="cpu">
              <el-input-number v-model="createForm.cpu" :min="1" :max="quota.cpu_limit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Memory (GB)" prop="memory_gb">
              <el-input-number v-model="createForm.memory_gb" :min="1" :max="quota.memory_limit_gb" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="Disk (GB)" prop="disk_gb">
          <el-input-number v-model="createForm.disk_gb" :min="10" :max="500" />
        </el-form-item>
        <el-form-item label="Purpose" prop="purpose">
          <el-input v-model="createForm.purpose" type="textarea" placeholder="Describe the purpose of this VM" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="submitCreate" :loading="creating">Create VM</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showQuotaDialog" title="Request Quota Increase" width="500px">
      <el-form :model="quotaForm" label-width="140px">
        <el-form-item label="Current VM Limit">
          {{ quota.vm_limit }}
        </el-form-item>
        <el-form-item label="Requested VM Limit" prop="vm_limit">
          <el-input-number v-model="quotaForm.vm_limit" :min="quota.vm_limit + 1" :max="50" />
        </el-form-item>
        <el-form-item label="Reason" prop="reason">
          <el-input v-model="quotaForm.reason" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuotaDialog = false">Cancel</el-button>
        <el-button type="primary" @click="submitQuotaRequest">Submit Request</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRequestDialog" title="My Requests" width="700px">
      <el-table :data="myRequests">
        <el-table-column prop="type" label="Type" width="120" />
        <el-table-column prop="details" label="Details" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="getRequestStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Date" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="consoleDialogVisible" title="VM Console" width="90%" top="5vh">
      <div class="console-container">
        <iframe :src="consoleUrl" class="console-frame" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Money, Document } from '@element-plus/icons-vue'
import { vmsApi } from '@/api/vms'

const searchQuery = ref('')
const statusFilter = ref('')
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const showQuotaDialog = ref(false)
const showRequestDialog = ref(false)
const consoleDialogVisible = ref(false)
const consoleUrl = ref('')
const createFormRef = ref()

const quota = ref({
  vm_limit: 10,
  cpu_limit: 64,
  memory_limit_gb: 256
})

const myVms = ref<any[]>([])

const myRequests = ref<any[]>([])

const createForm = ref({
  name: '',
  template: '',
  cpu: 2,
  memory_gb: 4,
  disk_gb: 40,
  purpose: ''
})

const quotaForm = ref({
  vm_limit: 11,
  reason: ''
})

const createRules = {
  name: [{ required: true, message: 'Please input VM name', trigger: 'blur' }],
  cpu: [{ required: true, message: 'Please select CPU', trigger: 'blur' }],
  memory_gb: [{ required: true, message: 'Please select memory', trigger: 'blur' }]
}

const filteredVms = computed(() => {
  return myVms.value.filter(vm => {
    const matchSearch = !searchQuery.value || vm.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = !statusFilter.value || vm.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

function getRequestStatusType(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'danger'
    case 'pending': return 'warning'
    default: return 'info'
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

async function loadMyVms() {
  loading.value = true
  try {
    const response = await vmsApi.getList({ page_size: 100 })
    myVms.value = response.data.data.items || []
  } catch (error) {
    console.error('Failed to load VMs:', error)
  } finally {
    loading.value = false
  }
}

async function togglePower(vm: any) {
  try {
    const action = vm.status === 'poweredOn' ? 'stop' : 'start'
    await ElMessageBox.confirm(`Are you sure you want to ${action} this VM?`, 'Confirm')
    await vmsApi.power(vm.vm_id, action)
    ElMessage.success(`VM ${action === 'start' ? 'starting' : 'stopping'}`)
    loadMyVms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Operation failed')
    }
  }
}

function openConsole(vm: any) {
  consoleUrl.value = `/vmrc?vm=${vm.vm_id}`
  consoleDialogVisible.value = true
}

function viewDetails(vm: any) {
  window.location.href = `/vms/${vm.vm_id}`
}

async function deleteVm(vm: any) {
  try {
    await ElMessageBox.confirm(
      `This will permanently delete "${vm.name}". Continue?`,
      'Warning',
      { type: 'warning' }
    )
    await vmsApi.delete(vm.vm_id)
    ElMessage.success('VM deleted')
    loadMyVms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Delete failed')
    }
  }
}

async function submitCreate() {
  creating.value = true
  try {
    await vmsApi.create({
      name: createForm.value.name,
      cpu: createForm.value.cpu,
      memory_mb: createForm.value.memory_gb * 1024,
      disk_gb: createForm.value.disk_gb
    })
    ElMessage.success('VM creation request submitted')
    showCreateDialog.value = false
    loadMyVms()
  } catch (error) {
    ElMessage.error('Failed to create VM')
  } finally {
    creating.value = false
  }
}

async function submitQuotaRequest() {
  ElMessage.success('Quota increase request submitted for approval')
  showQuotaDialog.value = false
}

onMounted(() => {
  loadMyVms()
})
</script>

<style scoped>
.tenant-portal {
  padding: 0;
}

.quota-card {
  height: 100%;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.quota-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.quota-item {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.quota-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.quota-item .value {
  display: block;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.console-container {
  height: calc(90vh - 100px);
}

.console-frame {
  width: 100%;
  height: 100%;
  border: none;
}

@media (max-width: 768px) {
  .quota-stats {
    grid-template-columns: 1fr;
  }
}
</style>
