<template>
  <div class="datastores">
    <el-card>
      <template #header>
        <span>Datastores</span>
      </template>
      
      <el-table :data="datastores" v-loading="loading" stripe>
        <el-table-column prop="name" label="Name" min-width="180" />
        <el-table-column prop="type" label="Type" width="120" />
        <el-table-column label="Capacity" width="120">
          <template #default="{ row }">
            {{ (row.capacity_gb / 1024).toFixed(2) }} TB
          </template>
        </el-table-column>
        <el-table-column label="Free" width="120">
          <template #default="{ row }">
            {{ (row.free_gb / 1024).toFixed(2) }} TB
          </template>
        </el-table-column>
        <el-table-column label="Usage" width="200">
          <template #default="{ row }">
            <el-progress 
              :percentage="getUsagePercent(row)" 
              :color="getUsageColor(row)"
              :stroke-width="10"
            />
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && datastores.length === 0" description="No datastores found" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { infraApi } from '@/api/infrastructure'
import { ElMessage } from 'element-plus'

const datastores = ref<any[]>([])
const loading = ref(false)

function getUsagePercent(ds: any) {
  if (!ds.capacity_gb) return 0
  return Math.round(((ds.capacity_gb - ds.free_gb) / ds.capacity_gb) * 100)
}

function getUsageColor(ds: any) {
  const percent = getUsagePercent(ds)
  if (percent > 90) return '#f56c6c'
  if (percent > 70) return '#e6a23c'
  return '#67c23a'
}

async function loadDatastores() {
  loading.value = true
  try {
    const response = await infraApi.getDatastores()
    datastores.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load datastores:', error)
    ElMessage.error('Failed to load datastores')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDatastores()
})
</script>
