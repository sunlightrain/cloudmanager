<template>
  <div class="networks">
    <el-card>
      <template #header>
        <span>Networks</span>
      </template>
      
      <el-table :data="networks" v-loading="loading" stripe>
        <el-table-column prop="name" label="Name" min-width="200" />
        <el-table-column prop="type" label="Type" width="150">
          <template #default="{ row }">
            <el-tag :type="row.type === 'DistributedPortGroup' ? 'primary' : 'info'">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && networks.length === 0" description="No networks found" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { infraApi } from '@/api/infrastructure'
import { ElMessage } from 'element-plus'

const networks = ref<any[]>([])
const loading = ref(false)

async function loadNetworks() {
  loading.value = true
  try {
    const response = await infraApi.getNetworks()
    networks.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load networks:', error)
    ElMessage.error('Failed to load networks')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadNetworks()
})
</script>
