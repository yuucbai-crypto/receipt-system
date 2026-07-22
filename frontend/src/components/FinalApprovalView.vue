<template>
  <div class="final-approval-view" data-testid="final-approval-view">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-semibold text-gray-900">最終承認判定</h2>
      <div v-if="loading" class="text-sm text-gray-600">
        読み込み中...
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading :overlay="true" message="データを読み込み中..." />
    </div>

    <div v-if="error" class="bg-white rounded-xl border border-gray-200 p-6 text-red-500" data-testid="error-message">
      {{ error }}
    </div>

    <div v-if="!loading && !error && receiptData" class="space-y-6">
      <!-- Receipt Information -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">レシート情報</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span class="text-sm text-gray-600">店舗名</span>
            <p class="font-medium">{{ receiptData.store }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-600">日付</span>
            <p class="font-medium">{{ receiptData.date }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-600">金額</span>
            <p class="font-medium">{{ formatCurrency(receiptData.amount) }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-600">分類</span>
            <p class="font-medium">{{ receiptData.category }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-600">重複判定</span>
            <p class="font-medium" :class="duplicateDecisionClass">
              {{ duplicateDecisionText }}
            </p>
          </div>
          <div>
            <span class="text-sm text-gray-600">AIコメント</span>
            <p class="font-medium">{{ receiptData.ai_comment }}</p>
          </div>
        </div>
      </div>

      <!-- Receipt Image -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">レシート画像</h3>
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <img 
            :src="receiptData.image_url" 
            :alt="'レシート画像'" 
            class="w-full h-auto"
          />
        </div>
      </div>

      <!-- AI Comment -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">AIコメント</h3>
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p class="text-gray-800">{{ receiptData.ai_comment }}</p>
        </div>
      </div>

      <!-- Approval/Rejection Buttons -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">最終判定</h3>
        
        <!-- Approval Button -->
        <div class="mb-6">
          <button
            @click="handleApproval"
            :disabled="approving"
            :data-testid="'btn-approve'"
            class="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-medium"
          >
            {{ approving ? '承認処理中...' : '合格' }}
          </button>
        </div>

        <!-- Rejection Button -->
        <div>
          <button
            @click="handleRejection"
            :disabled="approving"
            :data-testid="'btn-reject'"
            class="w-full bg-red-600 text-white py-3 px-6 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-medium"
          >
            {{ approving ? '却下処理中...' : '不合格' }}
          </button>
        </div>

        <!-- Reason Input Form (Rejection) -->
        <div v-if="rejected && showReasonForm" class="mt-6 pt-6 border-t border-gray-200">
          <h4 class="text-lg font-medium text-gray-900 mb-4">却下理由の入力（必須）</h4>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1" for="reasonCode">却下理由コード</label>
              <select
                id="reasonCode"
                v-model="rejectForm.reason_code"
                :data-testid="'final-reason-code-select'"
                class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 py-2 px-3"
              >
                <option value="">選択してください</option>
                <option value="DUPLICATE">重複あり</option>
                <option value="INVALID_FORMAT">形式不正</option>
                <option value="LOW_QUALITY">品質不足</option>
                <option value="AMOUNT_MISMATCH">金額不一致</option>
                <option value="OTHER">その他</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1" for="reasonText">却下理由テキスト</label>
              <textarea
                id="reasonText"
                v-model="rejectForm.reason_text"
                :data-testid="'final-reason-text-input'"
                rows="3"
                class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 py-2 px-3"
                placeholder="具体的な理由を入力してください"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                <input
                  type="checkbox"
                  v-model="rejectForm.is_for_ai_training"
                  :data-testid="'final-ai-training-checkbox'"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                AI学習用データとして使用
              </label>
            </div>
            <button
              @click="submitRejection"
              :disabled="!isFormValid || submitting"
              :data-testid="'btn-submit-final-rejection'"
              class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ submitting ? '送信中...' : '送信' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUIStore } from '../stores/ui'
import { useRoute, useRouter } from 'vue-router'
import { formatCurrency } from '@/utils/currency'
import { ReceiptsService } from '@/api/services/ReceiptsService'
import { ReceiptApprovalService } from '@/api/services/ReceiptApprovalService'
import AppLoading from './ui/AppLoading.vue'

// Types
interface ReceiptData {
  id: number
  date: string
  store: string
  amount: number
  category: string
  image_url: string
  ai_comment: string
  duplicate_decision: string
}

interface RejectForm {
  reason_code: string
  reason_text: string
  is_for_ai_training: boolean
}

// Store
const uiStore = useUIStore()
const route = useRoute()
const router = useRouter()

// Data
const loading = ref(false)
const approving = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const rejected = ref(false)
const showReasonForm = ref(false)

const receiptData = ref<ReceiptData | null>(null)
const duplicateDecision = ref<'duplicate' | 'not-duplicate'>('not-duplicate')

const rejectForm = ref<RejectForm>({
  reason_code: '',
  reason_text: '',
  is_for_ai_training: true
})

// Computed
const isFormValid = computed(() => {
  return rejectForm.value.reason_code !== '' && rejectForm.value.reason_text.trim() !== ''
})

const duplicateDecisionText = computed(() => {
  return duplicateDecision.value === 'duplicate' ? '重複あり' : '重複なし'
})

const duplicateDecisionClass = computed(() => {
  return duplicateDecision.value === 'duplicate' ? 'text-red-600' : 'text-green-600'
})

const loadReceiptData = async (receiptId: number) => {
  loading.value = true
  error.value = null
  
  try {
    const response = await ReceiptsService.getReceiptApiV1ReceiptsReceiptIdGet(receiptId)
    
    receiptData.value = {
      id: response.id,
      date: response.receipt_date || '',
      store: response.store_name || '',
      amount: response.total_amount || 0,
      category: response.category_name || '',
      image_url: response.image_url || '',
      ai_comment: response.ai_comment || '',
      duplicate_decision: duplicateDecision.value
    }
  } catch (err) {
    error.value = 'レシートデータの読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleApproval = async () => {
  if (!receiptData.value) {
    error.value = 'レシートデータが見つかりません'
    return
  }
  
  approving.value = true
  error.value = null
  
  try {
    const session = localStorage.getItem('session') || 'demo'
    const response = await ReceiptApprovalService.approveReceiptApiV1ReceiptApprovalApprovePost({
      receipt_id: receiptData.value.id,
      category: receiptData.value.category,
      tag: receiptData.value.tags || []
    })
    
    // ダッシュボードへ遷移
    router.push({ name: 'Dashboard' })
    
  } catch (err: any) {
    error.value = '承認処理に失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    approving.value = false
  }
}

const handleRejection = () => {
  if (!receiptData.value) {
    error.value = 'レシートデータが見つかりません'
    return
  }
  
  rejected.value = true
  showReasonForm.value = true
}

const submitRejection = async () => {
  if (!isFormValid.value) {
    error.value = '却下理由を正しく入力してください'
    return
  }
  
  if (!receiptData.value) {
    submitting.value = false
    return
  }
  
  submitting.value = true
  
  try {
    const session = localStorage.getItem('session') || 'demo'
    const response = await ReceiptApprovalService.rejectReceiptApiV1ReceiptApprovalRejectPost(
      session,
      {
        receipt_id: receiptData.value.id,
        reason_code: rejectForm.value.reason_code,
        reason_text: rejectForm.value.reason_text,
        is_for_ai_training: rejectForm.value.is_for_ai_training
      }
    )
    
    rejected.value = false
    showReasonForm.value = false
    submitting.value = false
    
    // ダッシュボードへ遷移
    router.push({ name: 'Dashboard' })
    
  } catch (err: any) {
    error.value = '却下理由の送信に失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  const receiptIdParam = route.params.receiptId as string
  const decisionParam = route.params.duplicateDecision as string
  
  const receiptId = receiptIdParam ? parseInt(receiptIdParam, 10) : 1
  const decision = decisionParam || 'not-duplicate'
  
  duplicateDecision.value = decision as 'duplicate' | 'not-duplicate'
  
  if (isNaN(receiptId)) {
    error.value = '無効なレシートIDです'
    return
  }
  
  loadReceiptData(receiptId)
})
</script>

<style scoped>
.final-approval-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>