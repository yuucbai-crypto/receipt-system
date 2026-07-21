<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'
import AppModal from './ui/AppModal.vue'

// Store
const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()
const route = useRoute()

// Data
const loading = ref(false)
const error = ref<string | null>(null)
const currentCheck = ref<any>(null)
const showRejectReasonModal = ref(false)
const rejectReason = ref('')
const isSubmitting = ref(false)

// Methods
const loadDuplicateCheck = async (checkId: number) => {
  loading.value = true
  error.value = null
  
  try {
    const response = await receiptsStore.getReceiptDuplicateChecks(checkId)
    
    // Assuming the first item in the array is the check we're interested in
    if (response.data && response.data.length > 0) {
      currentCheck.value = response.data[0]
      
      // Also fetch the related receipts
      if (currentCheck.value.sourceReceiptId) {
        const sourceReceipt = await receiptsStore.getReceipt(currentCheck.value.sourceReceiptId)
        currentCheck.value.sourceReceipt = sourceReceipt.data
      }
      
      if (currentCheck.value.targetReceiptId) {
        const targetReceipt = await receiptsStore.getReceipt(currentCheck.value.targetReceiptId)
        currentCheck.value.targetReceipt = targetReceipt.data
      }
    } else {
      error.value = 'データが見つかりません'
      uiStore.showError('エラーが発生しました')
    }
  } catch (err) {
    error.value = 'データの読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleFinalDecision = (isApproved: boolean) => {
  if (isApproved) {
    // For approval, just show confirmation
    submitApproval()
  } else {
    // For rejection, show reason input
    showRejectReasonModal.value = true
    rejectReason.value = ''
  }
}

const submitApproval = async () => {
  if (!currentCheck.value) return
  
  isSubmitting.value = true
  try {
    await receiptsStore.reviewDuplicateCheck(currentCheck.value.id, {
      userConfirmed: true,
      userNote: ''
    })
    
    uiStore.showSuccess('承認が完了しました')
    // Reload data or redirect to dashboard
  } catch (err) {
    uiStore.showError('承認処理に失敗しました')
    console.error(err)
  } finally {
    isSubmitting.value = false
  }
}

const submitReject = async () => {
  if (!currentCheck.value || !rejectReason.value.trim()) return
  
  isSubmitting.value = true
  try {
    await receiptsStore.reviewDuplicateCheck(currentCheck.value.id, {
      userConfirmed: false,
      userNote: rejectReason.value.trim()
    })
    
    uiStore.showSuccess('却下が完了しました')
    showRejectReasonModal.value = false
    rejectReason.value = ''
    // Reload data or redirect to dashboard
  } catch (err) {
    uiStore.showError('却下処理に失敗しました')
    console.error(err)
  } finally {
    isSubmitting.value = false
  }
}

// Lifecycle
onMounted(() => {
  // Get check ID from route parameters
  const checkId = parseInt(useRoute().params.id as string, 10)
  loadDuplicateCheck(checkId)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">合格・不合格判定画面</h2>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading v-if="loading" :overlay="true" message="データを読み込み中..." />
      
      <div v-if="error" class="text-red-500 mb-4">
        {{ error }}
      </div>

      <div v-if="!loading && !error && currentCheck" class="space-y-6">
        <!-- Receipt Images -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Current Receipt -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="font-medium text-gray-900 mb-3">レシート画像</h3>
            <div v-if="currentCheck.source_receipt?.image_path" class="mb-3">
              <img 
                :src="currentCheck.source_receipt.image_path" 
                alt="Current Receipt"
                class="w-full h-64 object-contain rounded border"
              >
            </div>
            <div v-else class="bg-gray-100 border border-dashed rounded-lg w-full h-64 flex items-center justify-center text-gray-500">
              画像なし
            </div>
            
            <div class="mt-3 space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">店舗名:</span>
                <span class="font-medium">{{ currentCheck.sourceReceipt?.store_name }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">日付:</span>
                <span class="font-medium">{{ currentCheck.sourceReceipt?.date }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">金額:</span>
                <span class="font-medium">{{ currentCheck.sourceReceipt?.amount }}</span>
              </div>
            </div>
          </div>
          
          <!-- Duplicate Candidate -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="font-medium text-gray-900 mb-3">重複候補</h3>
            <div v-if="currentCheck.target_receipt?.image_path" class="mb-3">
              <img 
                :src="currentCheck.target_receipt.image_path" 
                alt="Duplicate Receipt"
                class="w-full h-64 object-contain rounded border"
              >
            </div>
            <div v-else class="bg-gray-100 border border-dashed rounded-lg w-full h-64 flex items-center justify-center text-gray-500">
              画像なし
            </div>
            
            <div class="mt-3 space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">店舗名:</span>
                <span class="font-medium">{{ currentCheck.targetReceipt?.store_name }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">日付:</span>
                <span class="font-medium">{{ currentCheck.targetReceipt?.date }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">金額:</span>
                <span class="font-medium">{{ currentCheck.targetReceipt?.amount }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- AI Comments -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h3 class="font-medium text-gray-900 mb-3">AIコメント</h3>
          <div class="bg-blue-50 rounded-lg p-4">
            <p>このレシートは既存のレシートと比較して、店舗名・金額・日付が類似しており、重複の可能性が高いです。ただし、詳細な確認が必要なため、最終的な判断はユーザーに委ねます。</p>
          </div>
        </div>
        
        <!-- Duplicate Decision Result -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h3 class="font-medium text-gray-900 mb-3">重複判定結果</h3>
          <div class="flex items-center gap-4">
            <div class="text-xl font-bold" :class="currentCheck.isDuplicate ? 'text-red-600' : 'text-green-600'">
              {{ currentCheck.isDuplicate ? '重複' : '重複ではない' }}
            </div>
            <div class="bg-gray-100 rounded-lg px-3 py-1 text-sm">
              総合スコア: {{ currentCheck.compositeScore }}
            </div>
          </div>
        </div>
        
        <!-- Final Decision Section -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">最終判定</h3>
          
          <div class="flex gap-4">
            <AppButton 
              variant="primary" 
              size="lg"
              @click="handleFinalDecision(true)"
              data-testid="final-approve-button"
            >
              合格
            </AppButton>
            <AppButton 
              variant="danger" 
              size="lg"
              @click="handleFinalDecision(false)"
              data-testid="final-reject-button"
            >
              不合格
            </AppButton>
          </div>
        </div>
      </div>
      
      <div v-if="!loading && !error && !currentCheck" class="text-center py-8 text-gray-500">
        データが見つかりません
      </div>
    </div>

    <!-- Reject Reason Modal -->
    <AppModal
      v-model="showRejectReasonModal"
      title="却下理由入力"
      size="md"
      @close="showRejectReasonModal = false"
    >
      <div class="space-y-4">
        <p>レシートを不合格にする理由を入力してください</p>
        
        <textarea
          v-model="rejectReason"
          placeholder="例: 重複していないため"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows="4"
          data-testid="final-reject-reason-input"
        />

        <div class="flex gap-3 justify-end">
          <AppButton 
            variant="secondary" 
            @click="showRejectReasonModal = false"
            data-testid="reject-reason-cancel-button"
          >
            キャンセル
          </AppButton>
          <AppButton 
            variant="danger" 
            @click="submitReject"
            :disabled="!rejectReason.trim() || isSubmitting"
            data-testid="reject-reason-confirm-button"
          >
            {{ isSubmitting ? '処理中...' : '不合格にする' }}
          </AppButton>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<style scoped>
/* Additional styles for duplicate result view */
</style>