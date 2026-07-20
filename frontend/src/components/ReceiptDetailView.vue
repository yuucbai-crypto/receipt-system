<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'
import AppImagePreview from './ui/AppImagePreview.vue'

// Store
const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()

// Data
const loading = ref(false)
const error = ref<string | null>(null)
const receiptData = ref<any>(null)
const imagePreviewOpen = ref(false)
const previewImage = ref('')

// Methods
const loadReceipt = async (id: number) => {
  loading.value = true
  error.value = null
  
  try {
    // TODO: API呼び出しを実装
    // const response = await receiptsStore.getReceipt(id)
    // receiptData.value = response.data
    
    console.log(`Loading receipt ${id}...`)
    
    // デモ用のダミーデータ
    receiptData.value = {
      id: 1,
      date: '2026-07-15',
      store: '○○スーパー',
      amount: '¥2,480',
      category: '消耗品費',
      status: '承認済み',
      ocr_text: '店舗名：○○スーパー\n日付：2026年7月15日\n金額：2,480円\n商品：牛乳 1000円、パン 800円、卵 680円',
      ai_comment: 'このレシートは日常的な生活費のため、消耗品費として分類します。',
      tags: ['日用品', '食費'],
      image_url: 'https://picsum.photos/800/600'
    }
    
  } catch (err) {
    error.value = 'レシート詳細の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleImagePreview = (src: string) => {
  previewImage.value = src
  imagePreviewOpen.value = true
}

// Lifecycle
onMounted(() => {
  // TODO: ルートパラメータからIDを取得してloadReceiptを呼び出す
  const receiptId = 1; // デモ用
  loadReceipt(receiptId)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">レシート詳細</h2>
      <AppButton variant="secondary" size="sm">
        編集
      </AppButton>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading :overlay="true" message="レシート詳細を読み込み中..." />
    </div>

    <div v-if="error" class="bg-white rounded-xl border border-gray-200 p-6 text-red-500">
      {{ error }}
    </div>

    <div v-if="!loading && !error && receiptData" class="bg-white rounded-xl border border-gray-200 p-6 space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Receipt Image -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">レシート画像</h3>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <img 
              :src="receiptData.image_url" 
              :alt="'レシート画像'" 
              class="w-full h-auto cursor-pointer"
              @click="handleImagePreview(receiptData.image_url)"
            />
          </div>
        </div>

        <!-- Receipt Info -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">レシート情報</h3>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-600">日付:</span>
              <span class="font-medium">{{ receiptData.date }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">店舗名:</span>
              <span class="font-medium">{{ receiptData.store }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">金額:</span>
              <span class="font-medium">{{ receiptData.amount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">勘定科目:</span>
              <span class="font-medium">{{ receiptData.category }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">ステータス:</span>
              <span class="font-medium">{{ receiptData.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- OCR Text -->
      <div>
        <h3 class="text-lg font-medium text-gray-900 mb-3">OCRテキスト</h3>
        <div class="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap">
          {{ receiptData.ocr_text }}
        </div>
      </div>

      <!-- AI Comment -->
      <div>
        <h3 class="text-lg font-medium text-gray-900 mb-3">AIコメント</h3>
        <div class="bg-blue-50 rounded-lg p-4">
          {{ receiptData.ai_comment }}
        </div>
      </div>

      <!-- Tags -->
      <div>
        <h3 class="text-lg font-medium text-gray-900 mb-3">タグ</h3>
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="(tag, index) in receiptData.tags" 
            :key="index"
            class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm"
          >
            {{ tag }}
          </span>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <AppImagePreview
      v-model:open="imagePreviewOpen"
      :src="previewImage"
      title="レシート画像プレビュー"
      @close="imagePreviewOpen = false"
    />
  </div>
</template>

<style scoped>
/* Additional styles for receipt detail view */
</style>