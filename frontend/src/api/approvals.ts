import api from './index'

export interface ApprovalTemplate {
  id: number
  name: string
  request_type: string
  steps: any[]
  is_auto_approve: boolean
}

export interface ApprovalRequest {
  id: number
  request_type: string
  tenant_id: number
  applicant_id: number
  resource_type: string
  resource_id: string
  detail: any
  status: 'pending' | 'approved' | 'rejected'
  template_id: number
  current_step: number
  created_at: string
}

export interface ApprovalRecord {
  id: number
  step_order: number
  approver_id: number
  approver_name: string
  action: 'approve' | 'reject'
  comment: string
  created_at: string
}

export const approvalsApi = {
  getTemplates: (requestType?: string) => 
    api.get('/approvals/templates', { params: requestType ? { request_type: requestType } : {} }),
  
  createTemplate: (data: Partial<ApprovalTemplate>) => 
    api.post('/approvals/templates', null, { params: data }),
  
  getRequests: (params?: { tenant_id?: number; status?: string; request_type?: string }) =>
    api.get('/approvals', { params }),
  
  getById: (id: number) => api.get(`/approvals/${id}`),
  
  create: (data: {
    request_type: string
    tenant_id: number
    resource_type: string
    resource_id: string
    detail: any
    template_id?: number
  }) => api.post('/approvals', data),
  
  approve: (id: number, comment?: string) => 
    api.post(`/approvals/${id}/approve`, null, { params: comment ? { comment } : {} }),
  
  reject: (id: number, comment?: string) => 
    api.post(`/approvals/${id}/reject`, null, { params: comment ? { comment } : {} }),
  
  getHistory: (id: number) => api.get(`/approvals/${id}/history`),
  
  getPendingMine: () => api.get('/approvals/pending/mine'),
}
