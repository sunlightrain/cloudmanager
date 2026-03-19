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

export interface VMCloneRequest {
  name: string
  target_host_id?: string
  target_datastore_id?: string
  linked_clone?: boolean
  snapshot_id?: string
}

export interface VMMigrateRequest {
  target_host_id?: string
  target_datastore_id?: string
  target_cluster_id?: string
  priority?: string
}

export interface VMHotResizeRequest {
  cpu?: number
  memory_mb?: number
  disk_gb?: number
}

export const vmsApi = {
  getList: (params?: { page?: number; page_size?: number; name?: string; status?: string }) => 
    api.get('/vms', { params }),
  
  getById: (id: string) => api.get(`/vms/${id}`),
  
  create: (data: VMCreate) => api.post('/vms', data),
  
  update: (id: string, data: VMUpdate) => api.patch(`/vms/${id}`, data),
  
  delete: (id: string) => api.delete(`/vms/${id}`),
  
  power: (id: string, action: 'start' | 'stop' | 'restart') => 
    api.post(`/vms/${id}/power`, { action }),
  
  powerOn: (id: string) => api.post(`/vms/${id}/power-on`),
  
  powerOff: (id: string) => api.post(`/vms/${id}/power-off`),
  
  restart: (id: string) => api.post(`/vms/${id}/restart`),
  
  suspend: (id: string) => api.post(`/vms/${id}/suspend`),
  
  migrate: (id: string, data: VMMigrateRequest) => api.post(`/vms/${id}/migrate`, data),
  
  storageVmotion: (id: string, target_datastore_id: string) => 
    api.post(`/vms/${id}/storage-vmotion`, { target_datastore_id }),
  
  hotResize: (id: string, data: VMHotResizeRequest) => api.post(`/vms/${id}/hot-resize`, data),
  
  clone: (id: string, data: VMCloneRequest) => api.post(`/vms/${id}/clone`, data),
  
  convertToTemplate: (id: string) => api.post(`/vms/${id}/convert-to-template`),
  
  convertToVm: (templateId: string, targetHostId?: string) => 
    api.post(`/vms/templates/${templateId}/convert-to-vm`, { target_host_id: targetHostId }),
  
  batchPowerOn: (ids: string[]) => api.post('/vms/batch/power-on', ids),
  
  batchPowerOff: (ids: string[]) => api.post('/vms/batch/power-off', ids),
  
  batchDelete: (ids: string[]) => api.post('/vms/batch/delete', ids),
  
  getSnapshots: (id: string) => api.get(`/vms/${id}/snapshots`),
  
  createSnapshot: (id: string, name: string, description?: string, memory?: boolean) =>
    api.post(`/vms/${id}/snapshots`, null, { params: { name, description, memory } }),
  
  revertSnapshot: (id: string, snapshotId: string) =>
    api.post(`/vms/${id}/snapshots/${snapshotId}/revert`),
  
  deleteSnapshot: (id: string, snapshotId: string) =>
    api.delete(`/vms/${id}/snapshots/${snapshotId}`),
  
  getPerformance: (id: string) => api.get(`/vms/${id}/performance`),
}
