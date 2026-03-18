<template>
  <div class="tasks">
    <el-card>
      <template #header>
        <span>Tasks</span>
      </template>
      
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="task_id" label="Task ID" width="300" />
        <el-table-column prop="task_type" label="Type" width="120" />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="Error" />
        <el-table-column prop="created_at" label="Created" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="Completed" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
        @current-change="loadTasks"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { tasksApi } from '@/api/tasks'
import { ElMessage } from 'element-plus'
import type { Task } from '@/api/tasks'

const tasks = ref<Task[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function getStatusType(status: string) {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

async function loadTasks() {
  loading.value = true
  try {
    const response = await tasksApi.getList({ page: page.value, page_size: pageSize.value })
    tasks.value = response.data.data.items
    total.value = response.data.data.total
  } catch (error) {
    console.error('Failed to load tasks:', error)
    ElMessage.error('Failed to load tasks')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>
