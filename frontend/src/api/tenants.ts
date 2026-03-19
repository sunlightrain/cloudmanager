import api from './index'

export interface Tenant {
  id: number
  name: string
  code: string
  parent_id: number | null
  level: number
  quota_cpu: number
  quota_memory_gb: number
  quota_storage_gb: number
  quota_vm_count: number
  is_active: boolean
}

export interface TenantQuota {
  tenant_id: number
  quota: {
    cpu: number
    memory_gb: number
    storage_gb: number
    vm_count: number
  }
  usage: {
    cpu: number
    memory_gb: number
    storage_gb: number
    vm_count: number
  }
  available: {
    cpu: number
    memory_gb: number
    storage_gb: number
    vm_count: number
  }
}

export const tenantsApi = {
  getList: () => api.get('/tenants'),
  
  getTree: () => api.get('/tenants/tree'),
  
  getById: (id: number) => api.get(`/tenants/${id}`),
  
  create: (data: Partial<Tenant>) => api.post('/tenants', null, { params: data }),
  
  update: (id: number, data: Partial<Tenant>) => api.put(`/tenants/${id}`, null, { params: data }),
  
  delete: (id: number) => api.delete(`/tenants/${id}`),
  
  getQuota: (id: number) => api.get(`/tenants/${id}/quota`),
  
  getUsers: (id: number) => api.get(`/tenants/${id}/users`),
  
  addUser: (tenantId: number, userId: number, role: string = 'member') => 
    api.post(`/tenants/${tenantId}/users`, null, { params: { user_id: userId, role } }),
  
  removeUser: (tenantId: number, userId: number) => 
    api.delete(`/tenants/${tenantId}/users/${userId}`),
}
