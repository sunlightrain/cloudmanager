import api from './index'

export interface VM {
  vm_id: string
  name: string
  status: string
  cpu: number
  memory_mb: number
  disk_gb?: number
  ip_address?: string
  host?: string
}

export interface VMCreate {
  name: string
  cpu: number
  memory_mb: number
  disk_gb: number
  network_name?: string
  datastore?: string
  guest_id?: string
}

export interface VMUpdate {
  cpu?: number
  memory_mb?: number
}

export const vmsApi = {
  getList: (params?: { page?: number; page_size?: number; name?: string; status?: string }) => 
    api.get('/vms', { params }),
  
  getById: (id: string) => api.get(`/vms/${id}`),
  
  create: (data: VMCreate) => api.post('/vms', data),
  
  update: (id: string, data: VMUpdate) => api.patch(`/vms/${id}`, data),
  
  delete: (id: string) => api.delete(`/vms/${id}`),
  
  power: (id: string, action: 'start' | 'stop' | 'restart') => 
    api.post(`/vms/${id}/power`, { action })
}
