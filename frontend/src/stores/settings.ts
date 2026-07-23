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
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    settings: {} as Settings,
    loading: false,
  }),

  actions: {
    async loadSettings() {
      try {
        this.loading = true
        // 仮実装：実際のAPI呼び出しは後で実装
        console.log('Loading settings...')
        
        // ローカルストレージから設定を読み込む（実装例）
        const storedSettings = localStorage.getItem('receipt_settings')
        if (storedSettings) {
          this.settings = JSON.parse(storedSettings)
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async saveSettings(settings: Settings) {
      try {
        this.loading = true
        
        // 仮実装：実際のAPI呼び出しは後で実装
        console.log('Saving settings:', settings)
        
        // ローカルストレージに保存
        localStorage.setItem('receipt_settings', JSON.stringify(settings))
        
        // ステートを更新
        this.settings = settings
        
        return settings
      } catch (error) {
        console.error('Failed to save settings:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 設定のリセット
    resetSettings() {
      this.settings = {}
    },
  },
})