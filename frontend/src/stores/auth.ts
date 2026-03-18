import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, type LoginRequest, type LoginResponse } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<LoginResponse | null>(null)
  const loading = ref(false)

  const isAuthenticated = ref(false)

  async function login(credentials: LoginRequest) {
    loading.value = true
    try {
      const response = await authApi.login(credentials)
      user.value = response.data.data
      isAuthenticated.value = true
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
      isAuthenticated.value = false
    }
  }

  async function checkAuth() {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data.data
      isAuthenticated.value = true
    } catch {
      user.value = null
      isAuthenticated.value = false
    }
  }

  return {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    checkAuth
  }
})
