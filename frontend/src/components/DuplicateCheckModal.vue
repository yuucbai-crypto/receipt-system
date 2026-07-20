<template>
  <AppModal 
    :model-value="showModal" 
    title="重複チェック結果"
    @update:model-value="$emit('update:showModal', $event)"
  >
    <div class="duplicate-check-modal">
      <div v-if="isLoading" class="loading">
        <AppLoading />
        <p>重複チェック中...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <p class="text-red-600">{{ error }}</p>
      </div>
      
      <div v-else-if="result && result.duplicates.length > 0" class="results">
        <h3 class="text-lg font-semibold mb-4">重複候補が見つかりました</h3>
        <div class="duplicate-list">
          <div 
            v-for="duplicate in result.duplicates" 
            :key="duplicate.receipt.id"
            class="duplicate-item p-4 border rounded-lg mb-3"
          >
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-medium">{{ duplicate.receipt.store }}</h4>
                <p class="text-sm text-gray-600">金額: ¥{{ duplicate.receipt.amount }}</p>
                <p class="text-sm text-gray-600">日付: {{ duplicate.receipt.date }}</p>
              </div>
              <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
                スコア: {{ Math.round(duplicate.score * 100) }}%
              </span>
            </div>
          </div>
        </div>
        <div class="mt-4 p-3 bg-yellow-50 rounded">
          <p class="text-sm text-yellow-800">
            <strong>注意:</strong> この結果はAIによる推定です。確認の上、承認または却下してください。
          </p>
        </div>
      </div>
      
      <div v-else-if="result" class="no-results">
        <p class="text-center text-gray-600">重複候補は見つかりませんでした。</p>
      </div>
      
      <div class="modal-actions mt-6 flex justify-end space-x-3">
        <AppButton 
          variant="secondary" 
          @click="$emit('update:showModal', false)"
        >
          閉じる
        </AppButton>
        <AppButton 
          v-if="result && result.duplicates.length > 0"
          @click="onApprove"
        >
          承認
        </AppButton>
      </div>
    </div>
  </AppModal>
</template>

<script setup lang="ts">
import AppModal from './ui/AppModal.vue'
import AppButton from './ui/AppButton.vue'
import AppLoading from './ui/AppLoading.vue'

interface DuplicateReceipt {
  receipt: {
    id: string
    date: string
    store: string
    amount: number
    category: string
    status: 'pending' | 'approved' | 'rejected'
    tags: string[]
    imageUrl?: string
  }
  score: number
}

interface DuplicateCheckResult {
  duplicates: DuplicateReceipt[]
  score: number
}

const props = defineProps<{
  showModal: boolean
  result: DuplicateCheckResult | null
  isLoading: boolean
  error: string | null
}>()

const emit = defineEmits<{
  'update:showModal': [value: boolean]
  'approve': []
}>()

const onApprove = () => {
  emit('approve')
}
</script>

<style scoped>
.duplicate-check-modal {
  min-width: 500px;
}

.loading, .error, .no-results {
  text-align: center;
  padding: 2rem;
}

.duplicate-item {
  transition: all 0.2s ease;
}

.duplicate-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>