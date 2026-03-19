import api from './index'

export interface ScheduledTask {
  id: number
  name: string
  task_type: string
  target_type: string
  target_ids: string[]
  cron_expression: string
  action_params: any
  is_active: boolean
  last_run_at: string
  next_run_at: string
}

export interface ServiceTemplate {
  id: number
  name: string
  category: string
  cpu: number
  memory_mb: number
  disk_gb: number
  os_type: string
  price: number
}

export const automationApi = {
  getScheduledTasks: (taskType?: string) =>
    api.get('/automation/scheduled-tasks', { params: taskType ? { task_type: taskType } : {} }),
  
  createScheduledTask: (data: {
    name: string
    task_type: string
    target_type: string
    cron_expression: string
    target_ids?: string[]
    action_params?: any
  }) => api.post('/automation/scheduled-tasks', null, { params: data }),
  
  runTask: (taskId: number) => api.post(`/automation/scheduled-tasks/${taskId}/run`),
  
  getServiceTemplates: (category?: string) =>
    api.get('/automation/service-templates', { params: category ? { category } : {} }),
  
  createServiceTemplate: (data: Partial<ServiceTemplate>) =>
    api.post('/automation/service-templates', null, { params: data }),
}
