<template>
  <div class="vm-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Virtual Machines</span>
          <el-button type="primary" @click="$router.push('/vms/create')">
            Create VM
          </el-button>
        </div>
      </template>
      
      <el-table :data="vms" v-loading="loading" stripe>
        <el-table-column prop="name" label="Name" min-width="150" />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'poweredOn' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cpu" label="CPU" width="80" />
        <el-table-column prop="memory_mb" label="Memory (MB)" width="120">
          <template #default="{ row }">
            {{ (row.memory_mb / 1024).toFixed(1) }} GB
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP Address" width="140" />
        <el-table-column prop="host" label="Host" min-width="120" />
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                size="small" 
                :type="row.status === 'poweredOn' ? 'danger' : 'success'"
                @click="togglePower(row)"
              >
                {{ row.status === 'poweredOn' ? 'Stop' : 'Start' }}
              </el-button>
              <el-button size="small" @click="$router.push(`/vms/${row.vm_id}`)">
                Details
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
        @current-change="loadVMs"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { vmsApi } from '@/api/vms'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { VM } from '@/api/vms'

const vms = ref<VM[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function loadVMs() {
  loading.value = true
  try {
    const response = await vmsApi.getList({ page: page.value, page_size: pageSize.value })
    vms.value = response.data.data.items
    total.value = response.data.data.total
  } catch (error) {
    console.error('Failed to load VMs:', error)
    ElMessage.error('Failed to load VMs')
  } finally {
    loading.value = false
  }
}

async function togglePower(vm: VM) {
  const action = vm.status === 'poweredOn' ? 'stop' : 'start'
  const actionName = vm.status === 'poweredOn' ? 'stop' : 'start'
  
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to ${actionName} this VM?`,
      'Confirm',
      { type: 'warning' }
    )
    
    await vmsApi.power(vm.vm_id, action as 'start' | 'stop')
    ElMessage.success(`VM ${actionName} successful`)
    loadVMs()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`Failed to ${actionName} VM`)
    }
  }
}

onMounted(() => {
  loadVMs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
