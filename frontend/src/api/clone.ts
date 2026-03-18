import api from './index'

export interface CloneRequest {
  vm_id: string
  name: string
  resource_pool?: string
}

export const cloneApi = {
  clone: (data: CloneRequest) => api.post('/clone', data)
}
