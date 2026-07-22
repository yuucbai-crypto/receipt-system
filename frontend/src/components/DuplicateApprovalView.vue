<template>
  <div class="duplicate-approval-view" data-testid="duplicate-approval-view">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-semibold text-gray-900">重複判定・承認</h2>
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

    <div v-if="!loading && !error && receiptData && duplicateCheckResults" class="space-y-6">
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
        </div>
      </div>

      <!-- Images Comparison -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">画像比較</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <span class="text-sm text-gray-600">今回のレシート</span>
            <div class="mt-2 border border-gray-200 rounded-lg overflow-hidden">
              <img 
                :src="receiptData.image_url" 
                :alt="'今回のレシート'" 
                class="w-full h-auto"
              />
            </div>
          </div>
          <div v-if="duplicateCheckResults.length > 0">
            <span class="text-sm text-gray-600">重複候補（{{ duplicateCheckResults.length }}件）</span>
            <div class="mt-2 space-y-2">
              <div 
                v-for="(candidate, index) in duplicateCheckResults" 
                :key="candidate.receipt_id"
                class="border border-gray-200 rounded-lg p-3"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium">候補 {{ index + 1 }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-600">総合スコア</span>
                    <span class="text-sm font-medium" :class="getScoreClass(candidate.total_score)">
                      {{ (candidate.total_score * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
                <div class="border border-gray-200 rounded-lg overflow-hidden">
                  <img 
                    :src="candidate.image_url" 
                    :alt="'重複候補画像' + (index + 1)" 
                    class="w-full h-auto"
                  />
                </div>
              </div>
            </div>
          </div>
          <div v-else>
            <span class="text-sm text-gray-600">重複候補</span>
            <p class="text-sm text-gray-500 mt-2">重複候補は見つかりませんでした。</p>
          </div>
        </div>
      </div>

      <!-- Review Buttons -->
      <div v-if="duplicateCheckResults.length > 0" class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">重複判定</h3>
        <div class="flex gap-4">
          <button
            @click="handleDuplicate"
            :disabled="reviewing"
            :data-testid="'btn-duplicate'"
            class="flex-1 bg-red-600 text-white py-3 px-6 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ reviewing && reviewType === 'duplicate' ? '送信中...' : '重複' }}
          </button>
          <button
            @click="handleNotDuplicate"
            :disabled="reviewing"
            :data-testid="'btn-not-duplicate'"
            class="flex-1 bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ reviewing && reviewType === 'not-duplicate' ? '送信中...' : '重複ではない' }}
          </button>
        </div>
      </div>

      <!-- Reason Input Form (Rejected) -->
      <div v-if="rejected && showReasonForm" class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">却下理由の入力</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1" for="reasonCode">却下理由コード</label>
            <select
              id="reasonCode"
              v-model="rejectForm.reason_code"
              :data-testid="'reason-code-select'"
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
              :data-testid="'reason-text-input'"
              rows="3"
              class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 py-2 px-3"
              placeholder="具体的な理由を入力してください"
            ></textarea>
          </div>
          <button
            @click="submitRejection"
            :disabled="!isFormValid || submitting"
            :data-testid="'btn-submit-rejection'"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ submitting ? '送信中...' : '送信' }}
          </button>
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
import { DuplicateCheckService } from '@/api/services/DuplicateCheckService'
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
}

interface DuplicateCheckResult {
  receipt_id: number
  image_url: string
  total_score: number
  candidate_id?: number
  score_details?: any
  matched_fields?: string[]
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
const reviewing = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const rejected = ref(false)
const showReasonForm = ref(false)
const reviewType = ref<'duplicate' | 'not-duplicate' | null>(null)

const receiptData = ref<ReceiptData | null>(null)
const duplicateCheckResults = ref<DuplicateCheckResult[]>([])

const rejectForm = ref<RejectForm>({
  reason_code: '',
  reason_text: '',
  is_for_ai_training: true
})

// Computed
const isFormValid = computed(() => {
  return rejectForm.value.reason_code !== '' && rejectForm.value.reason_text.trim() !== ''
})

const loadReceiptData = async (receiptId: number) => {
  loading.value = true
  error.value = null
  
  try {
    // Call the actual API to get receipt details
    const response = await ReceiptsService.getReceiptApiV1ReceiptsReceiptIdGet(receiptId)
    
    receiptData.value = {
      id: response.id,
      date: response.receipt_date || '',
      store: response.store_name || '',
      amount: response.total_amount || 0,
      category: response.category_name || '',
      image_url: response.image_url || ''
    }
  } catch (err) {
    error.value = 'レシートデータの読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const loadDuplicateCheckResults = async (receiptId: number) => {
  try {
    const response = await DuplicateCheckService.getReceiptDuplicateChecksApiV1DuplicateCheckReceiptReceiptIdChecksGet(receiptId)
    duplicateCheckResults.value = response || []
  } catch (err) {
    console.error('重複チェック結果取得エラー:', err)
    duplicateCheckResults.value = []
    error.value = '重複チェック結果の取得に失敗しました'
  }
}

const handleDuplicate = async () => {
  reviewing.value = true
  reviewType.value = 'duplicate'
  error.value = null
  
  if (!receiptData.value) {
    error.value = 'レシートデータが見つかりません'
    reviewing.value = false
    return
  }
  
  try {
    // Show rejection reason form first for duplicate case
    rejected.value = true
    showReasonForm.value = true
    
  } catch (err: any) {
    error.value = '判定の送信に失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    reviewing.value = false
  }
}

const handleNotDuplicate = async () => {
  reviewing.value = true
  reviewType.value = 'not-duplicate'
  error.value = null
  
  if (!receiptData.value) {
    error.value = 'レシートデータが見つかりません'
    reviewing.value = false
    return
  }
  
  try {
    // Call the review API with user_confirmed: false
    const response = await DuplicateCheckService.reviewDuplicateCheckApiV1DuplicateCheckDuplicateCheckIdReviewPost(
      receiptData.value.id,
      {
        user_confirmed: false,
        user_note: null
      }
    )
    
    rejected.value = false
    showReasonForm.value = false
    reviewType.value = null
    
    // Navigate to FinalApproval with receipt_id and duplicate_decision
    router.push({ 
      name: 'FinalApproval', 
      params: { 
        receiptId: receiptData.value.id.toString(),
        duplicateDecision: 'not-duplicate' 
      }
    })
    
  } catch (err: any) {
    error.value = '判定の送信に失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    reviewing.value = false
  }
}

const submitRejection = async () => {
  if (!isFormValid.value) {
    error.value = '却下理由を正しく入力してください'
    return
  }
  
  submitting.value = true
  
  if (!receiptData.value) {
    submitting.value = false
    return
  }
  
  try {
    // Call the review API with user_confirmed: true and the rejection reason
    const response = await DuplicateCheckService.reviewDuplicateCheckApiV1DuplicateCheckDuplicateCheckIdReviewPost(
      receiptData.value.id,
      {
        user_confirmed: true,
        user_note: rejectForm.value.reason_text
      }
    )
    
    // After review API success, call the rejection API with reason
    const session = localStorage.getItem('session') || 'demo'
    await ReceiptApprovalService.rejectReceiptApiV1ReceiptApprovalRejectPost(
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
    
    // Navigate to dashboard after rejection
    router.push({ name: 'Dashboard' })
    
  } catch (err: any) {
    error.value = '却下理由の送信に失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    submitting.value = false
  }
}

const getScoreClass = (score: number) => {
  if (score >= 0.8) return 'text-red-600'
  if (score >= 0.5) return 'text-yellow-600'
  return 'text-green-600'
}

onMounted(() => {
  const receiptId = parseInt((route.params.id as string) || '1', 10)
  if (isNaN(receiptId)) {
    error.value = '無効なレシートIDです'
    return
  }
  loadReceiptData(receiptId)
  loadDuplicateCheckResults(receiptId)
})
</script>

<style scoped>
.duplicate-approval-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>