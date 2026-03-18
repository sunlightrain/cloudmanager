import api from './index'

export interface Task {
  task_id: string
  task_type: string
  status: string
  result?: string
  error?: string
  created_at: string
  completed_at?: string
}

export const tasksApi = {
  getList: (params?: { page?: number; page_size?: number; status?: string }) => 
    api.get('/tasks', { params }),
  
  getById: (id: string) => api.get(`/tasks/${id}`)
}
