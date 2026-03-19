<template>
  <div class="monitoring-view">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Active Alerts</span>
              <el-radio-group v-model="alertFilter">
                <el-radio-button label="all">All</el-radio-button>
                <el-radio-button label="active">Active</el-radio-button>
                <el-radio-button label="acknowledged">Acknowledged</el-radio-button>
                <el-radio-button label="resolved">Resolved</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          
          <el-table :data="filteredAlerts" v-loading="loading" max-height="400">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="severity" label="Severity" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_type" label="Resource" width="120" />
            <el-table-column prop="metric" label="Metric" width="120" />
            <el-table-column prop="value" label="Value" width="100" />
            <el-table-column prop="threshold" label="Threshold" width="100" />
            <el-table-column prop="status" label="Status" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="Triggered" width="180">
              <template #default="{ row }">
                {{ formatTime(row.triggered_at) }}
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="150" fixed="right">
              <template #default="{ row }">
                <el-button-group size="small">
                  <el-button 
                    v-if="row.status === 'active'" 
                    @click="acknowledge(row)"
                  >
                    Ack
                  </el-button>
                  <el-button 
                    v-if="row.status !== 'resolved'" 
                    @click="resolve(row)"
                    type="success"
                    size="small"
                  >
                    Resolve
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>Alert Rules</span>
            <el-button type="primary" size="small" @click="showRuleDialog = true">
              Add Rule
            </el-button>
          </template>
          
          <el-table :data="alertRules" size="small">
            <el-table-column prop="name" label="Name" />
            <el-table-column prop="resource_type" label="Resource" width="100" />
            <el-table-column prop="metric" label="Metric" width="100" />
            <el-table-column prop="condition" label="Condition" width="80" />
            <el-table-column prop="threshold" label="Threshold" width="80" />
            <el-table-column prop="severity" label="Severity" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>Scheduled Tasks</span>
            <el-button type="primary" size="small" @click="showTaskDialog = true">
              Add Task
            </el-button>
          </template>
          
          <el-table :data="scheduledTasks" size="small">
            <el-table-column prop="name" label="Name" />
            <el-table-column prop="task_type" label="Type" width="120" />
            <el-table-column prop="cron_expression" label="Schedule" width="120" />
            <el-table-column prop="is_active" label="Active" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? 'Yes' : 'No' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="next_run_at" label="Next Run" width="180">
              <template #default="{ row }">
                {{ formatTime(row.next_run_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-dialog v-model="showRuleDialog" title="Add Alert Rule" width="500px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item label="Name">
          <el-input v-model="ruleForm.name" />
        </el-form-item>
        <el-form-item label="Resource Type">
          <el-select v-model="ruleForm.resource_type">
            <el-option label="VM" value="vm" />
            <el-option label="Host" value="host" />
            <el-option label="Datastore" value="datastore" />
          </el-select>
        </el-form-item>
        <el-form-item label="Metric">
          <el-input v-model="ruleForm.metric" />
        </el-form-item>
        <el-form-item label="Condition">
          <el-select v-model="ruleForm.condition">
            <el-option label="> (Greater than)" value=">" />
            <el-option label="< (Less than)" value="<" />
            <el-option label=">= (Greater or equal)" value=">=" />
            <el-option label="<= (Less or equal)" value="<=" />
          </el-select>
        </el-form-item>
        <el-form-item label="Threshold">
          <el-input-number v-model="ruleForm.threshold" />
        </el-form-item>
        <el-form-item label="Severity">
          <el-select v-model="ruleForm.severity">
            <el-option label="Info" value="info" />
            <el-option label="Warning" value="warning" />
            <el-option label="Critical" value="critical" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">Cancel</el-button>
        <el-button type="primary" @click="createRule">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { monitoringApi } from '@/api/monitoring'
import { automationApi } from '@/api/automation'

const loading = ref(false)
const alerts = ref<any[]>([])
const alertRules = ref<any[]>([])
const scheduledTasks = ref<any[]>([])
const alertFilter = ref('active')
const showRuleDialog = ref(false)
const showTaskDialog = ref(false)

const ruleForm = ref({
  name: '',
  resource_type: 'vm',
  metric: 'cpu_usage',
  condition: '>',
  threshold: 90,
  severity: 'warning'
})

const filteredAlerts = computed(() => {
  if (alertFilter.value === 'all') return alerts.value
  return alerts.value.filter(a => a.status === alertFilter.value)
})

function getSeverityType(severity: string) {
  switch (severity) {
    case 'critical': return 'danger'
    case 'warning': return 'warning'
    default: return 'info'
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'active': return 'danger'
    case 'acknowledged': return 'warning'
    case 'resolved': return 'success'
    default: return 'info'
  }
}

function formatTime(time: string) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function loadAlerts() {
  loading.value = true
  try {
    const response = await monitoringApi.getAlerts({ limit: 100 })
    alerts.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load alerts:', error)
  } finally {
    loading.value = false
  }
}

async function loadRules() {
  try {
    const response = await monitoringApi.getAlertRules()
    alertRules.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load rules:', error)
  }
}

async function loadTasks() {
  try {
    const response = await automationApi.getScheduledTasks()
    scheduledTasks.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

async function acknowledge(alert: any) {
  try {
    await monitoringApi.acknowledgeAlert(alert.id)
    ElMessage.success('Alert acknowledged')
    loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to acknowledge alert')
  }
}

async function resolve(alert: any) {
  try {
    await monitoringApi.resolveAlert(alert.id)
    ElMessage.success('Alert resolved')
    loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to resolve alert')
  }
}

async function createRule() {
  try {
    await monitoringApi.createAlertRule(ruleForm.value)
    ElMessage.success('Rule created')
    showRuleDialog.value = false
    loadRules()
  } catch (error) {
    ElMessage.error('Failed to create rule')
  }
}

onMounted(() => {
  loadAlerts()
  loadRules()
  loadTasks()
})
</script>

<style scoped>
.monitoring-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
