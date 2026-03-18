import api from './index'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  user_id: number
  username: string
}

export const authApi = {
  login: (data: LoginRequest) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me')
}
