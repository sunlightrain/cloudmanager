<template>
  <div class="console-view">
    <div class="console-toolbar">
      <div class="toolbar-left">
        <span class="vm-name">{{ vmName }}</span>
        <el-tag :type="vmStatus === 'poweredOn' ? 'success' : 'info'" size="small">
          {{ vmStatus }}
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="sendCtrlAltDel" title="Send Ctrl+Alt+Del">
            <el-icon><Connection /></el-icon>
          </el-button>
          <el-button @click="sendCtrlC" title="Send Ctrl+C">
            Ctrl+C
          </el-button>
          <el-button @click="sendCtrlV" title="Send Ctrl+V">
            Ctrl+V
          </el-button>
        </el-button-group>
        <el-button @click="fullscreen" title="Fullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>
        <el-button @click="reload" title="Reload">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>
    
    <div class="console-container" ref="consoleContainer">
      <div v-if="loading" v-loading="loading" class="loading-overlay"></div>
      <div v-if="error" class="error-message">
        <el-icon><WarningFilled /></el-icon>
        <p>{{ error }}</p>
        <el-button @click="connect">Retry</el-button>
      </div>
      <div v-if="!loading && !error && !connected" class="connect-prompt">
        <p>Click connect to start the console</p>
        <el-button type="primary" @click="connect">Connect</el-button>
      </div>
      <div v-show="connected" class="console-frame-wrapper">
        <iframe 
          ref="consoleFrame"
          :src="consoleUrl"
          class="console-frame"
          allow="fullscreen"
        ></iframe>
      </div>
    </div>
    
    <div class="console-status">
      <span class="status-indicator" :class="{ connected }"></span>
      <span>{{ connected ? 'Connected' : 'Disconnected' }}</span>
      <span class="connection-info" v-if="connected">{{ connectionInfo }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { WarningFilled, Connection, FullScreen, Refresh } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const consoleContainer = ref()
const consoleFrame = ref()
const loading = ref(true)
const error = ref('')
const connected = ref(false)
const consoleUrl = ref('')
const vmName = ref('')
const vmStatus = ref('')
const connectionInfo = ref('')

async function loadVmInfo() {
  try {
    const vmId = route.params.vmId as string
    const response = await api.get(`/vms/${vmId}`)
    const vm = response.data.data
    vmName.value = vm.name
    vmStatus.value = vm.status
  } catch (err) {
    console.error('Failed to load VM info:', err)
  }
}

async function connect() {
  loading.value = true
  error.value = ''
  
  try {
    const vmId = route.params.vmId as string
    
    const response = await api.post(`/vms/${vmId}/console`)
    const data = response.data.data
    
    if (data.url) {
      consoleUrl.value = data.url
      connected.value = true
      connectionInfo.value = data.info || ''
    } else if (data.no_vmw_tools) {
      error.value = 'VMware Tools is not installed on this VM. Please install VMware Tools for console access.'
    } else {
      error.value = 'Console is not available for this VM'
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to connect to console'
  } finally {
    loading.value = false
  }
}

function sendCtrlAltDel() {
  const iframe = consoleFrame.value
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({ type: 'ctrl-alt-del' }, '*')
  }
}

function sendCtrlC() {
  const iframe = consoleFrame.value
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({ type: 'ctrl-c' }, '*')
  }
}

function sendCtrlV() {
  const iframe = consoleFrame.value
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({ type: 'ctrl-v' }, '*')
  }
}

function fullscreen() {
  const elem = consoleContainer.value
  if (elem) {
    if (elem.requestFullscreen) {
      elem.requestFullscreen()
    }
  }
}

function reload() {
  if (consoleFrame.value) {
    consoleFrame.value.src = consoleUrl.value
  }
}

onMounted(async () => {
  await loadVmInfo()
  loading.value = false
})

onUnmounted(() => {
  connected.value = false
})
</script>

<style scoped>
.console-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #1a1a1a;
}

.console-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vm-name {
  color: #fff;
  font-weight: bold;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-right .el-button {
  color: #fff;
  background: #404040;
  border-color: #505050;
}

.toolbar-right .el-button:hover {
  background: #505050;
}

.console-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-message,
.connect-prompt {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  gap: 16px;
}

.error-message .el-icon {
  font-size: 48px;
  color: #f56c6c;
}

.connect-prompt {
  background: #1a1a1a;
}

.console-frame-wrapper {
  width: 100%;
  height: 100%;
}

.console-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #000;
}

.console-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: #2d2d2d;
  color: #909399;
  font-size: 12px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.status-indicator.connected {
  background: #67c23a;
}

.connection-info {
  margin-left: auto;
  color: #606266;
}
</style>
