<template>
  <div class="topology">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Infrastructure Topology</span>
          <el-space>
            <el-select v-model="selectedDatacenter" placeholder="Select Datacenter" clearable @change="loadTree" style="width: 180px">
              <el-option v-for="dc in datacenters" :key="dc.name" :label="dc.name" :value="dc.name" />
            </el-select>
            <el-button circle @click="expandAll">
              <el-icon><Rank /></el-icon>
            </el-button>
            <el-button circle @click="collapseAll">
              <el-icon><Calendar /></el-icon>
            </el-button>
          </el-space>
        </div>
      </template>
      
      <div class="topology-container" v-loading="loading">
        <div class="tree-wrapper">
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            node-key="id"
            :default-expand-all="expanded"
            highlight-current
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.type === 'datacenter'" class="node-icon dc"><Office /></el-icon>
                <el-icon v-else-if="data.type === 'cluster'" class="node-icon cluster"><Grid /></el-icon>
                <el-icon v-else-if="data.type === 'host'" class="node-icon host"><Monitor /></el-icon>
                <el-icon v-else-if="data.type === 'vm'" class="node-icon vm"><Cpu /></el-icon>
                <span class="node-label">{{ node.label }}</span>
                <el-tag v-if="data.status" size="small" :type="getStatusType(data.status)" class="node-status">
                  {{ data.status }}
                </el-tag>
                <el-tag v-if="data.maintenance_mode" size="small" type="warning" class="node-status">
                  Maintenance
                </el-tag>
              </span>
            </template>
          </el-tree>
        </div>
        
        <div class="detail-panel" v-if="selectedNode">
          <el-card shadow="hover">
            <template #header>
              <span>{{ selectedNode.name }}</span>
            </template>
            <el-descriptions :column="2" border v-if="selectedNode.type === 'host'">
              <el-descriptions-item label="Status">{{ selectedNode.status }}</el-descriptions-item>
              <el-descriptions-item label="Power">{{ selectedNode.power_state }}</el-descriptions-item>
              <el-descriptions-item label="CPU">{{ selectedNode.cpu?.cores }} cores</el-descriptions-item>
              <el-descriptions-item label="Memory">{{ selectedNode.memory?.total_gb }} GB</el-descriptions-item>
              <el-descriptions-item label="CPU Usage" :span="2">
                <el-progress :percentage="selectedNode.cpu_usage_percent || 0" :color="getUsageColor(selectedNode.cpu_usage_percent)" />
              </el-descriptions-item>
              <el-descriptions-item label="Memory Usage" :span="2">
                <el-progress :percentage="getMemoryPercent(selectedNode)" :color="getUsageColor(getMemoryPercent(selectedNode))" />
              </el-descriptions-item>
            </el-descriptions>
            
            <el-descriptions :column="2" border v-else-if="selectedNode.type === 'vm'">
              <el-descriptions-item label="Status">{{ selectedNode.status }}</el-descriptions-item>
              <el-descriptions-item label="CPU">{{ selectedNode.cpu }}</el-descriptions-item>
              <el-descriptions-item label="Memory">{{ selectedNode.memory_mb / 1024 }} GB</el-descriptions-item>
              <el-descriptions-item label="IP">{{ selectedNode.ip_address || 'N/A' }}</el-descriptions-item>
              <el-descriptions-item label="Host">{{ selectedNode.host }}</el-descriptions-item>
              <el-descriptions-item label="Guest">{{ selectedNode.guest_full_name }}</el-descriptions-item>
            </el-descriptions>
            
            <el-descriptions :column="2" border v-else-if="selectedNode.type === 'cluster'">
              <el-descriptions-item label="Hosts">{{ selectedNode.children?.length || 0 }}</el-descriptions-item>
              <el-descriptions-item label="HA">
                <el-tag v-if="selectedNode.ha_enabled" type="success" size="small">Enabled</el-tag>
                <el-tag v-else type="info" size="small">Disabled</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="DRS">
                <el-tag v-if="selectedNode.drs_enabled" type="success" size="small">Enabled</el-tag>
                <el-tag v-else type="info" size="small">Disabled</el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-else class="no-detail">
              Select a node to view details
            </div>
            
            <div class="node-actions" v-if="selectedNode">
              <el-space v-if="selectedNode.type === 'vm'">
                <el-button size="small" type="primary" @click="openConsole(selectedNode)" :disabled="selectedNode.status !== 'poweredOn'">
                  <el-icon><Monitor /></el-icon>
                  Console
                </el-button>
                <el-button size="small" :type="selectedNode.status === 'poweredOn' ? 'danger' : 'success'" @click="togglePower(selectedNode)">
                  {{ selectedNode.status === 'poweredOn' ? 'Shutdown' : 'Power On' }}
                </el-button>
                <el-button size="small" @click="$router.push(`/vms/${selectedNode.id}`)">
                  Details
                </el-button>
              </el-space>
              <el-button v-else-if="selectedNode.type === 'host'" size="small" @click="loadHostVMs(selectedNode)">
                View VMs
              </el-button>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>
    
    <el-dialog v-model="consoleDialogVisible" title="VM Console" width="90%" top="5vh">
      <div class="console-container">
        <iframe :src="consoleUrl" class="console-frame" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Office, Grid, Monitor, Cpu, Rank, Calendar } from '@element-plus/icons-vue'
import { infraApi } from '@/api/infrastructure'
import { vmsApi } from '@/api/vms'

const treeRef = ref()
const treeData = ref<any[]>([])
const datacenters = ref<any[]>([])
const selectedDatacenter = ref('')
const selectedNode = ref<any>(null)
const loading = ref(false)
const expanded = ref(false)
const consoleDialogVisible = ref(false)
const consoleUrl = ref('')

const treeProps = {
  children: 'children',
  label: 'name'
}

function getStatusType(status: string) {
  switch (status) {
    case 'poweredOn': return 'success'
    case 'poweredOff': return 'info'
    default: return 'warning'
  }
}

function getUsageColor(value: number) {
  if (!value) return '#67c23a'
  if (value >= 80) return '#f56c6c'
  if (value >= 60) return '#e6a23c'
  return '#67c23a'
}

function getMemoryPercent(node: any) {
  if (!node.memory?.total_gb || !node.memory_usage_gb) return 0
  return Math.round((node.memory_usage_gb / node.memory.total_gb) * 100)
}

async function loadDatacenters() {
  try {
    const response = await infraApi.getDatacenters()
    datacenters.value = response.data.data.datacenters || []
    if (datacenters.value.length > 0) {
      selectedDatacenter.value = datacenters.value[0].name
      loadTree()
    }
  } catch (error) {
    console.error('Failed to load datacenters:', error)
  }
}

async function loadTree() {
  if (!selectedDatacenter.value) return
  loading.value = true
  try {
    const response = await infraApi.getDatacenterTree()
    const allDatacenters = response.data.data.datacenters || []
    const selected = allDatacenters.find((dc: any) => dc.name === selectedDatacenter.value)
    treeData.value = selected ? [selected] : allDatacenters
  } catch (error) {
    console.error('Failed to load tree:', error)
    ElMessage.error('Failed to load topology')
  } finally {
    loading.value = false
  }
}

function handleNodeClick(data: any) {
  selectedNode.value = data
}

function expandAll() {
  expanded.value = true
  document.querySelectorAll('.el-tree-node__content').forEach((el) => {
    el.click()
    el.click()
  })
}

function collapseAll() {
  expanded.value = false
}

function openConsole(vm: any) {
  consoleUrl.value = `/vmrc?vm=${vm.id}`
  consoleDialogVisible.value = true
}

async function togglePower(vm: any) {
  try {
    const action = vm.status === 'poweredOn' ? 'stop' : 'start'
    await vmsApi.power(vm.id, action)
    ElMessage.success(`VM ${action === 'start' ? 'powering on' : 'shutting down'}`)
    loadTree()
  } catch (error) {
    ElMessage.error('Failed to toggle power')
  }
}

async function loadHostVMs(host: any) {
  try {
    const response = await infraApi.getHostVMs(host.id)
    const vms = response.data.data || []
    if (vms.length > 0) {
      treeData.value = treeData.value.map((dc: any) => ({
        ...dc,
        children: dc.children?.map((cluster: any) => ({
          ...cluster,
          children: cluster.children?.map((h: any) => 
            h.id === host.id 
              ? { ...h, children: vms.map((vm: any) => ({ ...vm, type: 'vm' })) 
              : h
          )
        }))
      }))
      ElMessage.info(`Loaded ${vms.length} VMs`)
    }
  } catch (error) {
    console.error('Failed to load VMs:', error)
  }
}

onMounted(() => {
  loadDatacenters()
})
</script>

<style scoped>
.topology {
  height: calc(100vh - 140px);
}

.topology-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 280px);
}

.tree-wrapper {
  flex: 1;
  overflow: auto;
  border-right: 1px solid #ebeef5;
  padding-right: 20px;
}

.detail-panel {
  width: 350px;
  flex-shrink: 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-icon.dc { color: #409eff; }
.node-icon.cluster { color: #e6a23c; }
.node-icon.host { color: #67c23a; }
.node-icon.vm { color: #909399; }

.node-label {
  font-size: 13px;
}

.node-status {
  margin-left: 4px;
}

.node-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.no-detail {
  color: #909399;
  text-align: center;
  padding: 20px;
}

.console-container {
  height: calc(90vh - 100px);
}

.console-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 1024px) {
  .topology-container {
    flex-direction: column;
  }
  
  .detail-panel {
    width: 100%;
  }
}
</style>
