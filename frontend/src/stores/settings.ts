import { defineStore } from 'pinia'
import { apiClient } from '../api/client'

interface Settings {
  api_keys?: {
    openrouter?: string
  }
  folder_paths?: {
    unparsed?: string
    unapproved?: string
    failed?: string
    approved?: string
  }
  ocr_engine?: string
  ai_model?: string
  categories?: { id: number; name: string }[]
  tags?: { id: number; name: string }[]
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    settings: {} as Settings,
    loading: false,
  }),

  actions: {
    async loadSettings() {
      try {
        // API呼び出し
        const response = await apiClient.get('/api/v1/settings')
        this.settings = response.data
        
        // ローカルストレージから設定を読み込む（フォールバック）
        const storedSettings = localStorage.getItem('receipt_settings')
        if (storedSettings) {
          const parsedSettings = JSON.parse(storedSettings)
          // 既存の設定とマージ
          this.settings = { ...parsedSettings, ...this.settings }
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
        // ローカルストレージから読み込み（フォールバック）
        const storedSettings = localStorage.getItem('receipt_settings')
        if (storedSettings) {
          this.settings = JSON.parse(storedSettings)
        }
        throw error
      }
    },

    async saveSettings(settings: Settings) {
      try {
        // API呼び出し
        const response = await apiClient.put('/api/v1/settings', settings)
        
        // ローカルストレージに保存
        localStorage.setItem('receipt_settings', JSON.stringify(settings))
        
        // ステートを更新
        this.settings = response.data
        
        return response.data
      } catch (error) {
        console.error('Failed to save settings:', error)
        throw error
      }
    },

    // 設定のリセット
    resetSettings() {
      this.settings = {}
    },
  },
})