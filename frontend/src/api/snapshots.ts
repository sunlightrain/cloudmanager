import api from './index'

export interface Snapshot {
  snapshot_id: string
  name: string
  description: string
  created: string
  path: string
  size_mb: number
}

export const snapshotApi = {
  getList: (vmId: string) => api.get(`/snapshots/${vmId}`),
  
  create: (vmId: string, name: string, description: string = "", memory: boolean = false) => 
    api.post(`/snapshots/${vmId}?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}&memory=${memory}`),
  
  revert: (vmId: string, snapshotId: string) => 
    api.post(`/snapshots/${vmId}/${snapshotId}/revert`),
  
  delete: (vmId: string, snapshotId: string) => 
    api.delete(`/snapshots/${vmId}/${snapshotId}`),
  
  batchCleanup: (vmId: string, keepCount: number = 0) => 
    api.post(`/snapshots/${vmId}/cleanup?keep_count=${keepCount}`),
  
  getLongRunning: () => api.get('/monitoring/alerts?severity=warning&metric=snapshot_age'),
}

export const snapshotApi = {
  getList: (vmId: string) => api.get(`/snapshots/${vmId}`),
  
  create: (vmId: string, name: string, description: string = "", memory: boolean = false) => 
    api.post(`/snapshots/${vmId}?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}&memory=${memory}`),
  
  revert: (vmId: string, snapshotId: string) => 
    api.post(`/snapshots/${vmId}/${snapshotId}/revert`),
  
  delete: (vmId: string, snapshotId: string) => 
    api.delete(`/snapshots/${vmId}/${snapshotId}`)
}
