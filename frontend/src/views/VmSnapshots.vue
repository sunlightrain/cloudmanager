<template>
  <div class="vm-snapshots">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Snapshot Management - {{ vmId }}</span>
          <el-button type="primary" @click="showCreateDialog = true">
            Create Snapshot
          </el-button>
        </div>
      </template>
      
      <el-table :data="snapshots" v-loading="loading" stripe>
        <el-table-column prop="name" label="Name" min-width="150" />
        <el-table-column prop="description" label="Description" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created" label="Created" width="180">
          <template #default="{ row }">
            {{ row.created ? formatDate(row.created) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="size_mb" label="Size (MB)" width="120">
          <template #default="{ row }">
            {{ row.size_mb ? (row.size_mb / 1024).toFixed(2) + ' GB' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="success" @click="handleRevert(row)">
                Revert
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                Delete
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && snapshots.length === 0" description="No snapshots found" />
    </el-card>
    
    <el-dialog v-model="showCreateDialog" title="Create Snapshot" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="Name">
          <el-input v-model="createForm.name" placeholder="Snapshot name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="createForm.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="Memory">
          <el-switch v-model="createForm.memory" />
          <span style="margin-left: 10px">Include memory</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { snapshotApi } from '@/api/snapshots'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const vmId = route.params.id as string

const snapshots = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = reactive({
  name: '',
  description: '',
  memory: false
})

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

async function loadSnapshots() {
  loading.value = true
  try {
    const response = await snapshotApi.getList(vmId)
    snapshots.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load snapshots:', error)
    snapshots.value = []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.name) {
    ElMessage.warning('Please enter snapshot name')
    return
  }
  
  creating.value = true
  try {
    await snapshotApi.create(vmId, createForm.name, createForm.description, createForm.memory)
    ElMessage.success('Snapshot created')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    createForm.memory = false
    loadSnapshots()
  } catch (error) {
    ElMessage.error('Failed to create snapshot')
  } finally {
    creating.value = false
  }
}

async function handleRevert(snapshot: any) {
  try {
    await ElMessageBox.confirm('Are you sure you want to revert to this snapshot?', 'Confirm', { type: 'warning' })
    await snapshotApi.revert(vmId, snapshot.snapshot_id)
    ElMessage.success('Snapshot reverted')
    loadSnapshots()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to revert snapshot')
    }
  }
}

async function handleDelete(snapshot: any) {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this snapshot?', 'Confirm', { type: 'warning' })
    await snapshotApi.delete(vmId, snapshot.snapshot_id)
    ElMessage.success('Snapshot deleted')
    loadSnapshots()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete snapshot')
    }
  }
}

onMounted(() => {
  loadSnapshots()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
