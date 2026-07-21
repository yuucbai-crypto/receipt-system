<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'
import AppModal from './ui/AppModal.vue'
import AppInput from './ui/AppInput.vue'

// Store
const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()
const route = useRoute()

// Data
const loading = ref(false)
const error = ref<string | null>(null)
const duplicateChecks = ref<any[]>([])
const showApprovalModal = ref(false)
const showRejectReasonModal = ref(false)
const selectedCheck = ref<any>(null)
const rejectReason = ref('')
const isSubmitting = ref(false)

// Methods
const loadDuplicateChecks = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Get potential duplicates for the current receipt
    const receiptId = parseInt(useRoute().params.id as string, 10)
    const response = await receiptsStore.getReceiptDuplicateChecks(receiptId)
    
    // Format data for display
    duplicateChecks.value = response.data.map((check: any) => ({
      id: check.id,
      sourceReceiptId: check.source_receipt_id,
      targetReceiptId: check.target_receipt_id,
      isDuplicate: check.is_duplicate,
      compositeScore: check.composite_score,
      scoreComponents: check.score_components,
      sourceReceipt: check.source_receipt, // This will need to be fetched separately
      targetReceipt: check.target_receipt, // This will need to be fetched separately
    }))
    
  } catch (err) {
    error.value = '重複候補の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleDuplicateDecision = (check: any, isDuplicate: boolean) => {
  selectedCheck.value = check
  // For duplicate decision, we'll show the approval modal first
  if (isDuplicate) {
    showApprovalModal.value = true
  } else {
    // For non-duplicate, we show reason input
    showRejectReasonModal.value = true
    rejectReason.value = ''
  }
}

const submitApproval = async () => {
  if (!selectedCheck.value) return
  
  isSubmitting.value = true
  try {
    await receiptsStore.reviewDuplicateCheck(selectedCheck.value.id, {
      userConfirmed: true,
      userNote: ''
    })
    
    uiStore.showSuccess('承認が完了しました')
    showApprovalModal.value = false
    // Reload data
    await loadDuplicateChecks()
  } catch (err) {
    uiStore.showError('承認処理に失敗しました')
    console.error(err)
  } finally {
    isSubmitting.value = false
  }
}

const submitReject = async () => {
  if (!selectedCheck.value || !rejectReason.value.trim()) return
  
  isSubmitting.value = true
  try {
    await receiptsStore.reviewDuplicateCheck(selectedCheck.value.id, {
      userConfirmed: false,
      userNote: rejectReason.value.trim()
    })
    
    uiStore.showSuccess('却下が完了しました')
    showRejectReasonModal.value = false
    rejectReason.value = ''
    // Reload data
    await loadDuplicateChecks()
  } catch (err) {
    uiStore.showError('却下処理に失敗しました')
    console.error(err)
  } finally {
    isSubmitting.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadDuplicateChecks()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">重複候補比較・承認</h2>
      <AppButton variant="primary" size="sm">
        レシート追加
      </AppButton>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading v-if="loading" :overlay="true" message="重複候補を読み込み中..." />
      
      <div v-if="error" class="text-red-500 mb-4">
        {{ error }}
      </div>

      <div v-if="!loading && !error && duplicateChecks.length > 0" class="space-y-6">
        <!-- Duplicate Candidate Comparison Section -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-4">重複候補比較</h3>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Current Receipt -->
            <div class="border border-gray-200 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-3">今回レシート</h4>
              <div class="space-y-3">
                <div v-for="(value, key) in selectedCheck?.sourceReceipt" :key="key" class="flex justify-between text-sm">
                  <span class="text-gray-600">{{ key }}:</span>
                  <span class="font-medium">{{ value }}</span>
                </div>
              </div>
              
              <!-- Receipt Image -->
              <div class="mt-4">
                <img 
                  v-if="selectedCheck?.source_receipt?.image_path" 
                  :src="selectedCheck.source_receipt.image_path" 
                  alt="Receipt"
                  class="w-full h-48 object-contain rounded border"
                >
                <div v-else class="bg-gray-100 border border-dashed rounded-lg w-full h-48 flex items-center justify-center text-gray-500">
                  画像なし
                </div>
              </div>
            </div>
            
            <!-- Duplicate Candidate -->
            <div class="border border-gray-200 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-3">重複候補レシート</h4>
              <div class="space-y-3">
                <div v-for="(value, key) in selectedCheck?.targetReceipt" :key="key" class="flex justify-between text-sm">
                  <span class="text-gray-600">{{ key }}:</span>
                  <span class="font-medium">{{ value }}</span>
                </div>
              </div>
              
              <!-- Receipt Image -->
              <div class="mt-4">
                <img 
                  v-if="selectedCheck?.target_receipt?.image_path" 
                  :src="selectedCheck.target_receipt.image_path" 
                  alt="Receipt"
                  class="w-full h-48 object-contain rounded border"
                >
                <div v-else class="bg-gray-100 border border-dashed rounded-lg w-full h-48 flex items-center justify-center text-gray-500">
                  画像なし
                </div>
              </div>
            </div>
          </div>
          
          <!-- Score Components -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">スコア構成要素</h4>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div 
                v-for="(score, key) in selectedCheck?.scoreComponents" 
                :key="key"
                class="bg-gray-50 rounded-lg p-3 text-center"
              >
                <div class="text-sm text-gray-600 mb-1">{{ key.replace('_score', '') }}</div>
                <div class="font-medium">{{ score }}</div>
              </div>
            </div>
          </div>
          
          <!-- Total Score -->
          <div class="mt-4 bg-blue-50 rounded-lg p-4">
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-900">総合スコア</span>
              <span class="text-xl font-bold text-blue-600">{{ selectedCheck?.compositeScore }}</span>
            </div>
          </div>
        </div>
        
        <!-- Decision Section -->
        <div class="border-t border-gray-200 pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">判定</h3>
          
          <div class="flex gap-4">
            <AppButton 
              variant="secondary" 
              size="lg"
              @click="handleDuplicateDecision(selectedCheck, true)"
              data-testid="duplicate-approve-button"
            >
              重複
            </AppButton>
            <AppButton 
              variant="danger" 
              size="lg"
              @click="handleDuplicateDecision(selectedCheck, false)"
              data-testid="duplicate-reject-button"
            >
              重複ではない
            </AppButton>
          </div>
        </div>
      </div>
      
      <div v-if="!loading && !error && duplicateChecks.length === 0" class="text-center py-8 text-gray-500">
        重複候補が見つかりません
      </div>
    </div>

    <!-- Approval Modal -->
    <AppModal
      v-model="showApprovalModal"
      title="レシート承認確認"
      size="md"
      @close="showApprovalModal = false"
    >
      <div class="space-y-4">
        <p>以下のレシートを承認しますか？</p>
        
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div><span class="font-medium">店舗名:</span> {{ selectedCheck?.target_receipt?.store_name }}</div>
            <div><span class="font-medium">日付:</span> {{ selectedCheck?.target_receipt?.date }}</div>
            <div><span class="font-medium">金額:</span> {{ selectedCheck?.target_receipt?.amount }}</div>
            <div><span class="font-medium">勘定科目:</span> {{ selectedCheck?.target_receipt?.category }}</div>
          </div>
        </div>

        <div class="flex gap-3 justify-end">
          <AppButton 
            variant="secondary" 
            @click="showApprovalModal = false"
            data-testid="approval-cancel-button"
          >
            キャンセル
          </AppButton>
          <AppButton 
            variant="primary" 
            @click="submitApproval"
            :disabled="isSubmitting"
            data-testid="approval-confirm-button"
          >
            {{ isSubmitting ? '処理中...' : '承認する' }}
          </AppButton>
        </div>
      </div>
    </AppModal>

    <!-- Reject Reason Modal -->
    <AppModal
      v-model="showRejectReasonModal"
      title="却下理由入力"
      size="md"
      @close="showRejectReasonModal = false"
    >
      <div class="space-y-4">
        <p>レシートを却下する理由を入力してください</p>
        
        <AppInput
          v-model="rejectReason"
          label="却下理由"
          placeholder="例: 重複していないため"
          :rows="3"
          data-testid="reject-reason-input"
        />

        <div class="flex gap-3 justify-end">
          <AppButton 
            variant="secondary" 
            @click="showRejectReasonModal = false"
            data-testid="reject-cancel-button"
          >
            キャンセル
          </AppButton>
          <AppButton 
            variant="danger" 
            @click="submitReject"
            :disabled="!rejectReason.trim() || isSubmitting"
            data-testid="reject-confirm-button"
          >
            {{ isSubmitting ? '処理中...' : '却下する' }}
          </AppButton>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<style scoped>
/* Additional styles for duplicate approval view */
</style>