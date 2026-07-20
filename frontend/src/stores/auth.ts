import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: string
  email: string
  name: string
  role: string
  avatar?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface LoginPayload {
  email: string
  password: string
}

export interface LoginResponse {
  success: boolean
  error?: string
  token?: string
  user?: User
}

export interface SetUserPayload {
  user: User | null
}

export interface SetTokenPayload {
  token: string | null
}

export interface SetLoadingPayload {
  loading: boolean
}

export interface SetErrorPayload {
  error: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const setUser = (payload: SetUserPayload): void => {
    user.value = payload.user
  }

  const setToken = (payload: SetTokenPayload): void => {
    token.value = payload.token
    if (payload.token) {
      localStorage.setItem('auth_token', payload.token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }

  const setLoading = (payload: SetLoadingPayload): void => {
    isLoading.value = payload.loading
  }

  const setError = (payload: SetErrorPayload): void => {
    error.value = payload.error
  }

  const login = async (_payload: LoginPayload): Promise<LoginResponse> => {
    setLoading({ loading: true })
    setError({ error: null })
    let result: LoginResponse
    try {
      // API call will be implemented here
      // const response = await api.auth.login(payload)
      // setToken({ token: response.token })
      // setUser({ user: response.user })
      // return response
      result = { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'ログインに失敗しました'
      setError({ error: message })
      result = { success: false, error: message }
    } finally {
      setLoading({ loading: false })
    }
    return result!
  }

  const logout = (): void => {
    setToken({ token: null })
    setUser({ user: null })
  }

  const initializeAuth = (): void => {
    const savedToken = localStorage.getItem('auth_token')
    if (savedToken) {
      token.value = savedToken
      // Optionally validate token and fetch user
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    setUser,
    setToken,
    setLoading,
    setError,
    login,
    logout,
    initializeAuth,
  }
})