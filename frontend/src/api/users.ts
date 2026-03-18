import api from './index'

export interface User {
  id: number
  username: string
  email?: string
  role: string
  is_active: boolean
  created_at?: string
}

export interface UserCreate {
  username: string
  password: string
  email?: string
  role?: string
}

export interface UserUpdate {
  email?: string
  password?: string
  role?: string
  is_active?: boolean
}

export const usersApi = {
  getList: (params?: { page?: number; page_size?: number }) => 
    api.get('/users', { params }),
  
  getById: (id: number) => api.get(`/users/${id}`),
  
  create: (data: UserCreate) => api.post('/users', data),
  
  update: (id: number, data: UserUpdate) => api.put(`/users/${id}`, data),
  
  delete: (id: number) => api.delete(`/users/${id}`)
}
