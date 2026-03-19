import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true
})

api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message || 'Request failed'
    
    if (error.response?.status === 401) {
      window.location.href = '/login'
      return Promise.reject(error)
    }
    
    if (error.response?.status === 429) {
      ElMessage.error('Too many requests. Please try again later.')
    } else if (error.response?.status === 500) {
      ElMessage.error('Server error. Please contact administrator.')
    } else if (!error.response) {
      ElMessage.error('Network error. Please check your connection.')
    }
    
    return Promise.reject(error)
  }
)

export default api
