<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import { useSettingsStore } from '../stores/settings'
import AppButton from './ui/AppButton.vue'
import AppInput from './ui/AppInput.vue'
import AppSelect from './ui/AppSelect.vue'
import AppCheckbox from './ui/AppCheckbox.vue'
import AppModal from './ui/AppModal.vue'

// ストアのインスタンス化
const uiStore = useUIStore()
const settingsStore = useSettingsStore()

// 設定項目
const apiKeys = ref({
  openrouter: '',
})

const folderPaths = ref({
  unparsed: '',
  unapproved: '',
  failed: '',
  approved: '',
})

const ocrEngine = ref('')
const aiModel = ref('')

const newCategoryName = ref('')
const newTagName = ref('')

// 設定の読み込み
const loadSettings = async () => {
  try {
    uiStore.setGlobalLoading({ loading: true, message: '設定を読み込み中...' })
    await settingsStore.loadSettings()
    
    // 設定値をフォームに反映
    apiKeys.value.openrouter = settingsStore.settings.api_keys?.openrouter || ''
    folderPaths.value.unparsed = settingsStore.settings.folder_paths?.unparsed || ''
    folderPaths.value.unapproved = settingsStore.settings.folder_paths?.unapproved || ''
    folderPaths.value.failed = settingsStore.settings.folder_paths?.failed || ''
    folderPaths.value.approved = settingsStore.settings.folder_paths?.approved || ''
    ocrEngine.value = settingsStore.settings.ocr_engine || ''
    aiModel.value = settingsStore.settings.ai_model || ''
  } catch (error) {
    uiStore.showError('設定の読み込みに失敗しました')
    console.error('Failed to load settings:', error)
  } finally {
    uiStore.setGlobalLoading({ loading: false })
  }
}

// 設定の保存
const saveSettings = async () => {
  try {
    const settings = {
      api_keys: {
        openrouter: apiKeys.value.openrouter,
      },
      folder_paths: {
        unparsed: folderPaths.value.unparsed,
        unapproved: folderPaths.value.unapproved,
        failed: folderPaths.value.failed,
        approved: folderPaths.value.approved,
      },
      ocr_engine: ocrEngine.value,
      ai_model: aiModel.value,
      categories: settingsStore.settings.categories || [],
      tags: settingsStore.settings.tags || [],
    }
    
    uiStore.setGlobalLoading({ loading: true, message: '設定を保存中...' })
    await settingsStore.saveSettings(settings)
    uiStore.showSuccess('設定が保存されました')
  } catch (error) {
    uiStore.showError('設定の保存に失敗しました')
    console.error('Failed to save settings:', error)
  } finally {
    uiStore.setGlobalLoading({ loading: false })
  }
}

// 勘定科目の追加
const addCategory = () => {
  if (!newCategoryName.value.trim()) return
  
  const newCategory = {
    id: settingsStore.settings.categories && settingsStore.settings.categories.length > 0 ? Math.max(...settingsStore.settings.categories.map(c => c.id)) + 1 : 1,
    name: newCategoryName.value.trim(),
  }
  
  // ストアに追加
  if (!settingsStore.settings.categories) {
    settingsStore.settings.categories = []
  }
  settingsStore.settings.categories.push(newCategory)
  newCategoryName.value = ''
  
  // 保存
  saveSettings()
}

// 勘定科目の削除
const deleteCategory = (id: number) => {
  if (settingsStore.settings.categories) {
    settingsStore.settings.categories = settingsStore.settings.categories.filter(c => c.id !== id)
  }
  
  // 保存
  saveSettings()
}

// タグの追加
const addTag = () => {
  if (!newTagName.value.trim()) return
  
  const newTag = {
    id: settingsStore.settings.tags && settingsStore.settings.tags.length > 0 ? Math.max(...settingsStore.settings.tags.map(t => t.id)) + 1 : 1,
    name: newTagName.value.trim(),
  }
  
  // ストアに追加
  if (!settingsStore.settings.tags) {
    settingsStore.settings.tags = []
  }
  settingsStore.settings.tags.push(newTag)
  newTagName.value = ''
  
  // 保存
  saveSettings()
}

// タグの削除
const deleteTag = (id: number) => {
  if (settingsStore.settings.tags) {
    settingsStore.settings.tags = settingsStore.settings.tags.filter(t => t.id !== id)
  }
  
  // 保存
  saveSettings()
}

// 初期化
onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="space-y-6">
    <!-- APIキー設定 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="api-keys-section">
      <h3 class="text-lg font-medium text-gray-900 mb-4">APIキー設定</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AppInput
          v-model="apiKeys.openrouter"
          label="OpenRouter APIキー"
          type="password"
          placeholder="sk-or-v1-xxxxxxxxx"
          data-testid="openrouter-api-key-input"
        />
      </div>
    </div>

    <!-- フォルダパス設定 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="folder-paths-section">
      <h3 class="text-lg font-medium text-gray-900 mb-4">フォルダパス設定</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AppInput
          v-model="folderPaths.unparsed"
          label="未解析フォルダパス"
          placeholder="/path/to/unparsed"
          data-testid="unparsed-folder-path-input"
        />
        <AppInput
          v-model="folderPaths.unapproved"
          label="未承認フォルダパス"
          placeholder="/path/to/unapproved"
          data-testid="unapproved-folder-path-input"
        />
        <AppInput
          v-model="folderPaths.failed"
          label="失敗フォルダパス"
          placeholder="/path/to/failed"
          data-testid="failed-folder-path-input"
        />
        <AppInput
          v-model="folderPaths.approved"
          label="仕分け先フォルダパス"
          placeholder="/path/to/approved"
          data-testid="approved-folder-path-input"
        />
      </div>
    </div>

    <!-- OCRとAI設定 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="ocr-ai-section">
      <h3 class="text-lg font-medium text-gray-900 mb-4">OCRエンジン・AIモデル選択</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AppSelect
          v-model="ocrEngine"
          label="OCRエンジン"
          :options="[
            { value: 'tesseract', label: 'Tesseract' },
            { value: 'google-vision', label: 'Google Vision' },
            { value: 'azure-computer-vision', label: 'Azure Computer Vision' }
          ]"
          data-testid="ocr-engine-select"
        />
        
        <AppSelect
          v-model="aiModel"
          label="AIモデル"
          :options="[
            { value: 'gpt-4', label: 'GPT-4' },
            { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
            { value: 'claude-3', label: 'Claude 3' },
            { value: 'gemini-pro', label: 'Gemini Pro' }
          ]"
          data-testid="ai-model-select"
        />
      </div>
    </div>

    <!-- 勘定科目マスタ -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="categories-section">
      <h3 class="text-lg font-medium text-gray-900 mb-4">勘定科目マスタ</h3>
      
      <div class="flex gap-2 mb-4">
        <AppInput
          v-model="newCategoryName"
          label="新規勘定科目"
          placeholder="勘定科目名"
          data-testid="new-category-input"
        />
        <AppButton variant="primary" size="sm" @click="addCategory" data-testid="add-category-btn">
          追加
        </AppButton>
      </div>
      
      <div class="space-y-2">
        <div 
          v-for="category in settingsStore.settings.categories" 
          :key="category.id"
          class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          data-testid="category-item"
        >
          <span>{{ category.name }}</span>
          <AppButton variant="danger" size="sm" @click="deleteCategory(category.id)" data-testid="delete-category-btn">
            削除
          </AppButton>
        </div>
      </div>
    </div>

    <!-- タグマスタ -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="tags-section">
      <h3 class="text-lg font-medium text-gray-900 mb-4">タグマスタ</h3>
      
      <div class="flex gap-2 mb-4">
        <AppInput
          v-model="newTagName"
          label="新規タグ"
          placeholder="タグ名"
          data-testid="new-tag-input"
        />
        <AppButton variant="primary" size="sm" @click="addTag" data-testid="add-tag-btn">
          追加
        </AppButton>
      </div>
      
      <div class="space-y-2">
        <div 
          v-for="tag in settingsStore.settings.tags" 
          :key="tag.id"
          class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          data-testid="tag-item"
        >
          <span>{{ tag.name }}</span>
          <AppButton variant="danger" size="sm" @click="deleteTag(tag.id)" data-testid="delete-tag-btn">
            削除
          </AppButton>
        </div>
      </div>
    </div>

    <!-- 保存ボタン -->
    <div class="flex justify-end">
      <AppButton 
        variant="primary" 
        @click="saveSettings"
        data-testid="save-settings-btn"
      >
        設定を保存
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for settings view */
</style>