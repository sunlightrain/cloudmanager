<template>
  <div class="logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Operation Logs</span>
          <el-select v-model="filterOperation" placeholder="Filter by operation" clearable style="width: 200px">
            <el-option label="All Operations" value="" />
            <el-option label="VM Create" value="vm_create" />
            <el-option label="VM Delete" value="vm_delete" />
            <el-option label="VM Update" value="vm_update" />
            <el-option label="VM Power" value="vm_power" />
          </el-select>
        </div>
      </template>
      
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="User" width="120" />
        <el-table-column prop="operation" label="Operation" width="150">
          <template #default="{ row }">
            <el-tag :type="getOperationType(row.operation)">
              {{ formatOperation(row.operation) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="Target" min-width="150" show-overflow-tooltip />
        <el-table-column prop="detail" label="Detail" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button v-if="row.detail" size="small" @click="showDetail(row.detail)">
              View
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Time" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
        @current-change="loadLogs"
      />
    </el-card>
    
    <el-dialog v-model="showDetailDialog" title="Operation Detail" width="600px">
      <pre class="detail-json">{{ detailContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

const logs = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterOperation = ref('')
const showDetailDialog = ref(false)
const detailContent = ref('')

function getOperationType(operation: string) {
  if (operation.includes('create')) return 'success'
  if (operation.includes('delete')) return 'danger'
  if (operation.includes('update')) return 'warning'
  if (operation.includes('power')) return 'primary'
  return 'info'
}

function formatOperation(operation: string) {
  return operation.replace(/_/g, ' ').toUpperCase()
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

function showDetail(detail: string) {
  try {
    detailContent.value = JSON.stringify(JSON.parse(detail), null, 2)
  } catch {
    detailContent.value = detail
  }
  showDetailDialog.value = true
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filterOperation.value) {
      params.operation = filterOperation.value
    }
    const response = await api.get('/logs', { params })
    logs.value = response.data.data.items || []
    total.value = response.data.data.total || 0
  } catch (error) {
    console.error('Failed to load logs:', error)
    ElMessage.error('Failed to load logs')
  } finally {
    loading.value = false
  }
}

watch(filterOperation, () => {
  page.value = 1
  loadLogs()
})

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-json {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  max-height: 400px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
