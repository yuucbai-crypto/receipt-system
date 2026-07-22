<template>
  <div v-if="open" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="reject-modal">
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
      <div class="p-6 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">却下理由の入力</h3>
          <button
            @click="handleClose"
            :data-testid="'close-reject-modal'"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">却下理由コード</label>
          <select
            v-model="form.reason_code"
            :data-testid="'reject-reason-code-select'"
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
          <label class="block text-sm font-medium text-gray-700 mb-1">却下理由テキスト</label>
          <textarea
            v-model="form.reason_text"
            :data-testid="'reject-reason-text-input'"
            rows="3"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 py-2 px-3"
            placeholder="具体的な理由を入力してください"
          ></textarea>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            <input
              type="checkbox"
              v-model="form.is_for_ai_training"
              :data-testid="'reject-ai-training-checkbox'"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            AI学習用データとして使用
          </label>
        </div>
      </div>
      
      <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3">
        <button
          @click="handleClose"
          :data-testid="'btn-cancel-reject'"
          class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 transition-colors"
        >
          キャンセル
        </button>
        <button
          @click="handleSubmit"
          :disabled="!isFormValid || submitting"
          :data-testid="'btn-submit-reject'"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ submitting ? '送信中...' : '送信' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ReceiptApprovalService } from '@/api/services/ReceiptApprovalService'

// Types
interface ReceiptInfo {
  date: string
  store: string
  amount: number
  category: string
}

interface RejectForm {
  reason_code: string
  reason_text: string
  is_for_ai_training: boolean
}

// Props
interface Props {
  modelValue: boolean
  receiptId: number
  receiptInfo?: ReceiptInfo
}

const props = withDefaults(defineProps<Props>(), {
  receiptInfo: () => ({})
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  approved: []
  rejected: []
}>()

// Data
const form = ref<RejectForm>({
  reason_code: '',
  reason_text: '',
  is_for_ai_training: true
})
const submitting = ref(false)
const error = ref<string | null>(null)

// Computed
const isFormValid = computed(() => {
  return form.value.reason_code !== '' && form.value.reason_text.trim() !== ''
})

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleClose = () => {
  open.value = false
  error.value = null
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    error.value = '却下理由を正しく入力してください'
    return
  }
  
  submitting.value = true
  error.value = null
  
  try {
    const session = localStorage.getItem('session') || 'demo'
    await ReceiptApprovalService.rejectReceiptApiV1ReceiptApprovalRejectPost(
      session,
      {
        receipt_id: props.receiptId,
        reason_code: form.value.reason_code,
        reason_text: form.value.reason_text,
        is_for_ai_training: form.value.is_for_ai_training
      }
    )
    
    submitting.value = false
    emit('rejected')
    router.push({ name: 'Dashboard' })
    
  } catch (err: any) {
    error.value = '却下処理に失敗しました'
    console.error('却下処理エラー:', err)
    submitting.value = false
  }
}
</script>