<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import { ReceiptsService } from '@/api/services/ReceiptsService';
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'
import AppImagePreview from './ui/AppImagePreview.vue'
import { defineProps } from 'vue'

// Store
const uiStore = useUIStore()

// Props
const props = defineProps<{ id: string }>()

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
    const response = await ReceiptsService.getReceiptApiV1ReceiptsReceiptIdGet(id)
    receiptData.value = response
    
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
  // Use the receiptId from props
  const receiptId = parseInt(props.id)
  loadReceipt(receiptId)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900" data-testid="receipt-detail-title">レシート詳細</h2>
      <AppButton variant="secondary" size="sm" data-testid="edit-receipt-button">
        編集
      </AppButton>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading :overlay="true" message="レシート詳細を読み込み中..." />
    </div>

    <div v-if="error" class="bg-white rounded-xl border border-gray-200 p-6 text-red-500" data-testid="receipt-detail-error">
      {{ error }}
    </div>

    <div v-if="!loading && !error && receiptData" class="bg-white rounded-xl border border-gray-200 p-6 space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Receipt Image -->
        <div data-testid="receipt-image-section">
          <h3 class="text-lg font-medium text-gray-900 mb-3" data-testid="receipt-image-title">レシート画像</h3>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <img 
              :src="receiptData.image_url" 
              :alt="'レシート画像'" 
              class="w-full h-auto cursor-pointer"
              @click="handleImagePreview(receiptData.image_url)"
              data-testid="receipt-image"
            />
          </div>
        </div>

        <!-- Receipt Info -->
        <div data-testid="receipt-info-section">
          <h3 class="text-lg font-medium text-gray-900 mb-3" data-testid="receipt-info-title">レシート情報</h3>
          <div class="space-y-3">
            <div class="flex justify-between" data-testid="receipt-date-row">
              <span class="text-gray-600" data-testid="receipt-date-label">日付:</span>
              <span class="font-medium" data-testid="receipt-date-value">{{ receiptData.date }}</span>
            </div>
            <div class="flex justify-between" data-testid="receipt-store-row">
              <span class="text-gray-600" data-testid="receipt-store-label">店舗名:</span>
              <span class="font-medium" data-testid="receipt-store-value">{{ receiptData.store }}</span>
            </div>
            <div class="flex justify-between" data-testid="receipt-amount-row">
              <span class="text-gray-600" data-testid="receipt-amount-label">金額:</span>
              <span class="font-medium" data-testid="receipt-amount-value">{{ receiptData.amount }}</span>
            </div>
            <div class="flex justify-between" data-testid="receipt-category-row">
              <span class="text-gray-600" data-testid="receipt-category-label">勘定科目:</span>
              <span class="font-medium" data-testid="receipt-category-value">{{ receiptData.category }}</span>
            </div>
            <div class="flex justify-between" data-testid="receipt-status-row">
              <span class="text-gray-600" data-testid="receipt-status-label">ステータス:</span>
              <span class="font-medium" data-testid="receipt-status-value">{{ receiptData.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- OCR Text -->
      <div data-testid="ocr-text-section">
        <h3 class="text-lg font-medium text-gray-900 mb-3" data-testid="ocr-text-title">OCRテキスト</h3>
        <div class="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap" data-testid="ocr-text-content">
          {{ receiptData.ocr_text }}</div>
      </div>

      <!-- AI Comment -->
      <div data-testid="ai-comment-section">
        <h3 class="text-lg font-medium text-gray-900 mb-3" data-testid="ai-comment-title">AIコメント</h3>
        <div class="bg-blue-50 rounded-lg p-4" data-testid="ai-comment-content">
          {{ receiptData.ai_comment }}</div>
      </div>

      <!-- Tags -->
      <div data-testid="tags-section">
        <h3 class="text-lg font-medium text-gray-900 mb-3" data-testid="tags-title">タグ</h3>
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="(tag, index) in receiptData.tags" 
            :key="index"
            class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm"
            data-testid="tag-item"
          >
            {{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <AppImagePreview
      v-model:open="imagePreviewOpen"
      :src="previewImage"
      title="レシート画像プレビュー"
      @close="imagePreviewOpen = false"
      data-testid="image-preview-modal"
    />
  </div>
</template>

<style scoped>
/* Additional styles for receipt detail view */
</style>