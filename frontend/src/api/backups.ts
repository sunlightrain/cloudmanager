import api from './index'

export interface BackupPolicy {
  id: number
  name: string
  tenant_id: number
  target_type: string
  target_ids: string[]
  backup_type: 'full' | 'incremental'
  schedule: 'daily' | 'weekly' | 'monthly'
  retention_count: number
  is_active: boolean
  last_backup_at: string
  next_backup_at: string
}

export interface BackupJob {
  id: number
  policy_id: number
  resource_type: string
  resource_id: string
  backup_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'expired'
  size_bytes: number
  backup_path: string
  started_at: string
  completed_at: string
  error_message: string
}

export interface BackupHistory {
  id: number
  backup_type: string
  status: string
  size_bytes: number
  backup_path: string
  completed_at: string
}

export const backupsApi = {
  getPolicies: (tenantId?: number) =>
    api.get('/backups/policies', { params: tenantId ? { tenant_id: tenantId } : {} }),
  
  createPolicy: (data: {
    name: string
    tenant_id: number
    target_type: string
    target_ids?: string[]
    backup_type?: 'full' | 'incremental'
    schedule?: 'daily' | 'weekly' | 'monthly'
    retention_count?: number
  }) => api.post('/backups/policies', null, { params: data }),
  
  getJobs: (params?: { policy_id?: number; resource_type?: string; status?: string; limit?: number }) =>
    api.get('/backups/jobs', { params }),
  
  createJob: (data: { resource_type: string; resource_id: string; backup_type?: string }) =>
    api.post('/backups/jobs', data),
  
  restoreBackup: (jobId: number, restoreType?: string, targetHostId?: string) =>
    api.post(`/backups/jobs/${jobId}/restore`, null, { 
      params: { restore_type: restoreType, target_host_id: targetHostId } 
    }),
  
  getHistory: (resourceType: string, resourceId: string, limit?: number) =>
    api.get(`/backups/history/${resourceType}/${resourceId}`, { params: { limit } }),
}
