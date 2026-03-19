<template>
  <div class="topology-view">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="tree-panel">
          <template #header>
            <span>Infrastructure</span>
            <el-button text @click="expandAll">
              <el-icon><Expand /></el-icon>
            </el-button>
          </template>
          <el-scrollbar height="calc(100vh - 200px)">
            <el-tree
              ref="treeRef"
              :data="treeData"
              :props="treeProps"
              node-key="id"
              :expand-on-click-node="false"
              :default-expand-all="false"
              @node-click="handleNodeClick"
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <el-icon v-if="data.type === 'datacenter'"><Office /></el-icon>
                  <el-icon v-else-if="data.type === 'cluster'"><Grid /></el-icon>
                  <el-icon v-else-if="data.type === 'host'"><Monitor /></el-icon>
                  <el-icon v-else-if="data.type === 'vm'"><Cpu /></el-icon>
                  <span>{{ data.label }}</span>
                  <el-tag v-if="data.count" size="small" type="info">{{ data.count }}</el-tag>
                </span>
              </template>
            </el-tree>
          </el-scrollbar>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <el-card shadow="hover" class="topology-panel">
          <template #header>
            <div class="card-header">
              <span>{{ selectedNode?.label || 'Topology Overview' }}</span>
              <el-space>
                <el-button @click="refreshTopology">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-select v-model="viewMode" style="width: 120px">
                  <el-option label="Tree" value="tree" />
                  <el-option label="Cards" value="cards" />
                </el-select>
              </el-space>
            </div>
          </template>
          
          <div v-if="loading" v-loading="loading" class="loading-area"></div>
          
          <div v-else-if="!selectedNode" class="overview-grid">
            <div class="overview-item" v-for="dc in datacenters" :key="dc.id">
              <div class="dc-card" @click="selectNode({ ...dc, type: 'datacenter', id: `dc-${dc.id}` })">
                <div class="dc-icon">
                  <el-icon><Office /></el-icon>
                </div>
                <div class="dc-name">{{ dc.name }}</div>
                <div class="dc-stats">
                  <span><Cpu /> {{ dc.clusterCount || 0 }} clusters</span>
                  <span><Monitor /> {{ dc.hostCount || 0 }} hosts</span>
                  <span><Cpu /> {{ dc.vmCount || 0 }} VMs</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else-if="viewMode === 'tree'" class="topology-tree">
            <div class="tree-visual">
              <div class="level datacenter" v-if="selectedNode?.type !== 'vm'">
                <div class="node-box dc">
                  <el-icon><Office /></el-icon>
                  <span>{{ selectedNode.label }}</span>
                </div>
              </div>
              
              <div class="level clusters" v-if="selectedNode?.type === 'datacenter'">
                <div 
                  v-for="cluster in selectedNode.children || []" 
                  :key="cluster.id"
                  class="node-box cluster"
                  @click="selectNode(cluster)"
                >
                  <el-icon><Grid /></el-icon>
                  <span>{{ cluster.label }}</span>
                  <span class="node-count">{{ cluster.children?.length || 0 }} hosts</span>
                </div>
              </div>
              
              <div class="level hosts" v-if="selectedNode?.type === 'cluster'">
                <div 
                  v-for="host in selectedNode.children || []" 
                  :key="host.id"
                  class="node-box host"
                  @click="selectNode(host)"
                >
                  <el-icon><Monitor /></el-icon>
                  <span>{{ host.label }}</span>
                  <span class="node-count">{{ host.vmCount || 0 }} VMs</span>
                </div>
              </div>
              
              <div class="level vms" v-if="selectedNode?.type === 'host'">
                <div 
                  v-for="vm in selectedNode.children || []" 
                  :key="vm.id"
                  class="node-box vm"
                  :class="{ running: vm.status === 'poweredOn', stopped: vm.status === 'poweredOff' }"
                  @click="selectNode(vm)"
                >
                  <el-icon><Cpu /></el-icon>
                  <span>{{ vm.label }}</span>
                  <el-tag size="small" :type="vm.status === 'poweredOn' ? 'success' : 'info'">
                    {{ vm.status }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="vm-cards">
            <el-row :gutter="16">
              <el-col 
                v-for="vm in selectedNode?.children || selectedVms" 
                :key="vm.id"
                :xs="24" :sm="12" :md="8" :lg="6"
              >
                <el-card shadow="hover" class="vm-card" @click="$router.push(`/vms/${vm.vm_id || vm.id}`)">
                  <div class="vm-card-header">
                    <el-icon size="24" :class="vm.status">
                      <Cpu />
                    </el-icon>
                    <span class="vm-name">{{ vm.label || vm.name }}</span>
                  </div>
                  <div class="vm-card-body">
                    <div class="vm-info">
                      <span>CPU: {{ vm.cpu || vm.config?.hardware?.numCPU || 0 }}</span>
                      <span>Memory: {{ formatMemory(vm.memory_mb || vm.config?.hardware?.memoryMB || 0) }}</span>
                    </div>
                    <div class="vm-actions" @click.stop>
                      <el-button-group size="small">
                        <el-button @click="openConsole(vm)" title="Console">
                          <el-icon><Monitor /></el-icon>
                        </el-button>
                        <el-button 
                          v-if="vm.status !== 'poweredOn'" 
                          @click="powerOn(vm)"
                          title="Start"
                        >
                          <el-icon><VideoPlay /></el-icon>
                        </el-button>
                        <el-button 
                          v-if="vm.status === 'poweredOn'" 
                          @click="powerOff(vm)"
                          title="Stop"
                        >
                          <el-icon><VideoPause /></el-icon>
                        </el-button>
                      </el-button-group>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Office, Grid, Monitor, Cpu, Expand, Refresh, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { inventoryApi } from '@/api/inventory'
import { vmsApi } from '@/api/vms'

const loading = ref(false)
const viewMode = ref('tree')
const treeRef = ref()
const treeData = ref<any[]>([])
const selectedNode = ref<any>(null)
const datacenters = ref<any[]>([])
const selectedVms = ref<any[]>([])

const treeProps = {
  children: 'children',
  label: 'label'
}

async function loadTopology() {
  loading.value = true
  try {
    const dcResponse = await inventoryApi.getDatacenters()
    const clusterResponse = await inventoryApi.getClusters()
    const hostResponse = await inventoryApi.getHosts()
    const vmResponse = await inventoryApi.getVms()
    
    const clusters = clusterResponse.data.data || []
    const hosts = hostResponse.data.data || []
    const vms = vmResponse.data.data || []
    
    datacenters.value = (dcResponse.data.data || []).map((dc: any) => ({
      ...dc,
      clusterCount: clusters.filter((c: any) => c.datacenter_id === dc.id).length,
      hostCount: hosts.filter((h: any) => h.datacenter_id === dc.id).length,
      vmCount: vms.filter((v: any) => v.datacenter_id === dc.id).length
    }))
    
    treeData.value = datacenters.value.map(dc => ({
      id: `dc-${dc.id}`,
      label: dc.name,
      type: 'datacenter',
      count: dc.vmCount,
      children: clusters
        .filter((c: any) => c.datacenter_id === dc.id)
        .map((cluster: any) => ({
          id: `cluster-${cluster.id}`,
          label: cluster.name,
          type: 'cluster',
          datacenter_id: dc.id,
          children: hosts
            .filter((h: any) => h.cluster_id === cluster.id)
            .map((host: any) => ({
              id: `host-${host.id}`,
              label: host.name,
              type: 'host',
              cluster_id: cluster.id,
              datacenter_id: dc.id,
              vmCount: vms.filter((v: any) => v.host_id === host.id).length,
              children: vms
                .filter((v: any) => v.host_id === host.id)
                .map((vm: any) => ({
                  id: `vm-${vm.id}`,
                  label: vm.name,
                  type: 'vm',
                  host_id: host.id,
                  datacenter_id: dc.id,
                  vm_id: vm.vm_id || vm.id,
                  status: vm.status,
                  cpu: vm.cpu,
                  memory_mb: vm.memory_mb
                }))
            }))
        }))
    }))
    
    selectedVms.value = vms
  } catch (error) {
    console.error('Failed to load topology:', error)
    ElMessage.error('Failed to load infrastructure topology')
  } finally {
    loading.value = false
  }
}

function handleNodeClick(data: any) {
  selectedNode.value = data
}

function selectNode(node: any) {
  selectedNode.value = node
}

function expandAll() {
  if (treeRef.value) {
    const nodes = treeRef.value.store.nodesMap
    for (const key in nodes) {
      nodes[key].expanded = true
    }
  }
}

function refreshTopology() {
  loadTopology()
}

function formatMemory(mb: number) {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(0)} GB`
  }
  return `${mb} MB`
}

function openConsole(vm: any) {
  const vmId = vm.vm_id || vm.id
  window.open(`/console/${vmId}`, '_blank', 'width=1024,height=768')
}

async function powerOn(vm: any) {
  try {
    await vmsApi.powerOn(vm.vm_id || vm.id)
    ElMessage.success(`VM ${vm.label || vm.name} powered on`)
    refreshTopology()
  } catch (error: any) {
    ElMessage.error(`Failed: ${error.message}`)
  }
}

async function powerOff(vm: any) {
  try {
    await vmsApi.powerOff(vm.vm_id || vm.id)
    ElMessage.success(`VM ${vm.label || vm.name} powered off`)
    refreshTopology()
  } catch (error: any) {
    ElMessage.error(`Failed: ${error.message}`)
  }
}

onMounted(() => {
  loadTopology()
})
</script>

<style scoped>
.topology-view {
  padding: 20px;
  height: calc(100vh - 120px);
}

.tree-panel {
  height: calc(100vh - 140px);
}

.tree-panel :deep(.el-card__header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topology-panel {
  height: calc(100vh - 140px);
}

.loading-area {
  height: 400px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 10px;
}

.dc-card {
  background: linear-gradient(135deg, #409eff10, #409eff20);
  border: 1px solid #409eff30;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.dc-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px #409eff20;
}

.dc-icon {
  width: 50px;
  height: 50px;
  background: #409eff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  margin-bottom: 12px;
}

.dc-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.dc-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #606266;
}

.dc-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.topology-tree {
  padding: 20px;
}

.tree-visual {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.level {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
}

.level.datacenter {
  justify-content: center;
}

.node-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 140px;
}

.node-box:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.node-box.dc {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: white;
  font-size: 16px;
  font-weight: bold;
}

.node-box.cluster {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
}

.node-box.host {
  background: linear-gradient(135deg, #909399, #b1b3b8);
  color: white;
}

.node-box.vm {
  background: white;
  border: 2px solid #dcdfe6;
  color: #303133;
}

.node-box.vm.running {
  border-color: #67c23a;
  background: #67c23a10;
}

.node-box.vm.stopped {
  border-color: #909399;
  background: #90939910;
}

.node-box span {
  margin-top: 6px;
  font-size: 13px;
  text-align: center;
}

.node-count {
  font-size: 11px !important;
  opacity: 0.8;
}

.vm-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.vm-card:hover {
  transform: translateY(-2px);
}

.vm-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.vm-card-header .el-icon {
  color: #909399;
}

.vm-card-header .el-icon.running {
  color: #67c23a;
}

.vm-card-header .el-icon.poweredOn {
  color: #67c23a;
}

.vm-name {
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vm-card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.vm-info {
  font-size: 12px;
  color: #606266;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tree-node .el-icon {
  color: #409eff;
}

@media (max-width: 768px) {
  .topology-view {
    padding: 10px;
  }
  
  .el-col-span-6 {
    display: none;
  }
  
  .el-col-span-18 {
    width: 100%;
  }
}
</style>
