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

// Props
const props = defineProps({
  receiptId: {
    type: Number,
    required: false
  }
})

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
    const response = await receiptsStore.getReceipt(id)
    receiptData.value = response.data
    
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

const handleApprove = () => {
  // TODO: Implement approval functionality
  uiStore.showSuccess('承認が完了しました')
  console.log('Approve receipt:', receiptData.value?.id)
}

const handleReject = () => {
  // TODO: Implement rejection functionality
  uiStore.showSuccess('却下処理が完了しました')
  console.log('Reject receipt:', receiptData.value?.id)
}

const handleReanalyze = () => {
  // TODO: Implement re-analysis functionality
  uiStore.showSuccess('再解析処理が開始されました')
  console.log('Re-analyze receipt:', receiptData.value?.id)
}

// Lifecycle
onMounted(() => {
  if (props.receiptId) {
    loadReceipt(props.receiptId)
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">レシート詳細</h2>
      <div class="flex gap-2">
        <AppButton variant="secondary" size="sm" @click="handleReanalyze" data-testid="receipt-detail-reanalyze">
          再解析
        </AppButton>
        <AppButton variant="primary" size="sm" @click="handleApprove" data-testid="receipt-detail-approve">
          承認
        </AppButton>
        <AppButton variant="danger" size="sm" @click="handleReject" data-testid="receipt-detail-reject">
          却下
        </AppButton>
      </div>
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
              data-testid="receipt-detail-image"
            />
          </div>
        </div>

        <!-- Receipt Info -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">レシート情報</h3>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-600">ID:</span>
              <span class="font-medium">{{ receiptData.id }}</span>
            </div>
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
        <div class="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap" data-testid="receipt-detail-ocr">
          {{ receiptData.ocr_text }}
        </div>
      </div>

      <!-- AI Comment -->
      <div>
        <h3 class="text-lg font-medium text-gray-900 mb-3">AIコメント</h3>
        <div class="bg-blue-50 rounded-lg p-4" data-testid="receipt-detail-ai-comment">
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
            data-testid="receipt-detail-tag"
          >
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Metadata -->
      <div>
        <h3 class="text-lg font-medium text-gray-900 mb-3">メタデータ</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="font-medium mb-2">ファイル情報</h4>
            <div class="space-y-1 text-sm">
              <div><span class="text-gray-600">ファイル名:</span> {{ receiptData.file_name }}</div>
              <div><span class="text-gray-600">ファイルサイズ:</span> {{ receiptData.file_size }} bytes</div>
              <div><span class="text-gray-600">作成日時:</span> {{ receiptData.created_at }}</div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="font-medium mb-2">解析情報</h4>
            <div class="space-y-1 text-sm">
              <div><span class="text-gray-600">OCR解析日時:</span> {{ receiptData.ocr_processed_at }}</div>
              <div><span class="text-gray-600">AI解析日時:</span> {{ receiptData.ai_processed_at }}</div>
              <div><span class="text-gray-600">解析状態:</span> {{ receiptData.processing_status }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <AppImagePreview
      v-model:open="imagePreviewOpen"
      :src="previewImage"
      title="レシート画像プレビュー"
      @close="imagePreviewOpen = false"
      data-testid="receipt-detail-image-preview"
    />
  </div>
</template>

<style scoped>
/* Additional styles for receipt detail view */
</style>