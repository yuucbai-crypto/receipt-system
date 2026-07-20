import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import type { Component } from 'vue'

export interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

export interface Modal {
  id: string
  component: Component
  props?: Record<string, unknown>
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
}

export interface UIState {
  toasts: Toast[]
  modals: Modal[]
  globalLoading: boolean
  loadingMessage: string
}

export interface AddToastPayload {
  message: string
  type: Toast['type']
  duration?: number
}

export interface OpenModalPayload {
  component: Component
  props?: Record<string, unknown>
  size?: Modal['size']
  closeOnOverlayClick?: boolean
}

export interface SetGlobalLoadingPayload {
  loading: boolean
  message?: string
}

export const useUIStore = defineStore('ui', () => {
  const toasts = ref<Toast[]>([])
  const modals = ref<Modal[]>([])
  const globalLoading = ref(false)
  const loadingMessage = ref('')

  const activeToastCount = computed(() => toasts.value.length)

  const addToast = (payload: AddToastPayload): string => {
    const id = Math.random().toString(36).slice(2, 10)
    const newToast = { ...payload, id }
    toasts.value.push(newToast)

    if (payload.duration !== 0) {
      setTimeout(() => {
        removeToast(id)
      }, payload.duration ?? 5000)
    }

    return id
  }

  const removeToast = (id: string): void => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  const clearToasts = (): void => {
    toasts.value = []
  }

  const showSuccess = (message: string, duration?: number): string => {
    return addToast({ message, type: 'success', duration })
  }

  const showError = (message: string, duration?: number): string => {
    return addToast({ message, type: 'error', duration: duration ?? 0 })
  }

  const showWarning = (message: string, duration?: number): string => {
    return addToast({ message, type: 'warning', duration })
  }

  const showInfo = (message: string, duration?: number): string => {
    return addToast({ message, type: 'info', duration })
  }

  const openModal = (payload: OpenModalPayload): string => {
    const id = Math.random().toString(36).slice(2, 10)
    const newModal = { ...payload, id }
    modals.value.push(newModal)
    return id
  }

  const closeModal = (id: string): void => {
    const index = modals.value.findIndex(m => m.id === id)
    if (index !== -1) {
      modals.value.splice(index, 1)
    }
  }

  const closeAllModals = (): void => {
    modals.value = []
  }

  const setGlobalLoading = (payload: SetGlobalLoadingPayload): void => {
    globalLoading.value = payload.loading
    if (payload.message) {
      loadingMessage.value = payload.message
    }
  }

  return {
    toasts,
    modals,
    globalLoading,
    loadingMessage,
    activeToastCount,
    addToast,
    removeToast,
    clearToasts,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    openModal,
    closeModal,
    closeAllModals,
    setGlobalLoading,
  }
}, {
  persist: {
    storage: localStorage,
    pick: ['modals'],
  },
})