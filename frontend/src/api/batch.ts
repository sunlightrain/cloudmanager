import api from './index'

export interface BatchPowerRequest {
  vm_ids: string[]
  action: 'start' | 'stop' | 'restart'
}

export interface BatchDeleteRequest {
  vm_ids: string[]
}

export const batchApi = {
  power: (data: BatchPowerRequest) => api.post('/batch/power', data),
  delete: (data: BatchDeleteRequest) => api.post('/batch/delete', data)
}
