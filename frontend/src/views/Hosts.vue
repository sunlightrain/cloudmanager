<template>
  <div class="hosts">
    <el-card>
      <template #header>
        <span>Hosts</span>
      </template>
      
      <el-table :data="hosts" v-loading="loading" stripe>
        <el-table-column prop="name" label="Host Name" min-width="180" />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'connected' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="maintenance_mode" label="Maintenance" width="120">
          <template #default="{ row }">
            <el-tag :type="row.maintenance_mode ? 'warning' : 'info'">
              {{ row.maintenance_mode ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">Details</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && hosts.length === 0" description="No hosts found" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

const hosts = ref<any[]>([])
const loading = ref(false)

async function loadHosts() {
  loading.value = true
  try {
    const response = await api.get('/hosts')
    hosts.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load hosts:', error)
    ElMessage.error('Failed to load hosts')
  } finally {
    loading.value = false
  }
}

function viewDetail(host: any) {
  ElMessage.info(`Host: ${host.name}`)
}

onMounted(() => {
  loadHosts()
})
</script>
