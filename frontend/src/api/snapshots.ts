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
    api.delete(`/snapshots/${vmId}/${snapshotId}`)
}
