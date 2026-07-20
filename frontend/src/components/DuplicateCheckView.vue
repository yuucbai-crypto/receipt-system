<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'
import AppTable from './ui/AppTable.vue'
import AppModal from './ui/AppModal.vue'

// Store
const uiStore = useUIStore()
// Data
const loading = ref(false)
const error = ref<string | null>(null)
const duplicateChecks = ref<any[]>([])
const showApprovalModal = ref(false)
const selectedCheck = ref<any>(null)

// Table columns
const tableColumns = ref([
  { key: 'id', header: 'ID', sortable: true },
  { key: 'date', header: '日付', sortable: true },
  { key: 'store', header: '店舗名', sortable: true },
  { key: 'amount', header: '金額', sortable: true, class: 'text-right' },
  { key: 'category', header: '勘定科目' },
  { key: 'score', header: 'スコア' },
])

// Methods
const loadDuplicateChecks = async () => {
  loading.value = true
  error.value = null
  
  try {
    // TODO: API呼び出しを実装
    // const response = await receiptsStore.getDuplicateChecks()
    // duplicateChecks.value = response.data
    
    console.log('Loading duplicate checks...')
    
    // デモ用のダミーデータ
    duplicateChecks.value = [
      { 
        id: 1, 
        date: '2026-07-15', 
        store: '○○スーパー', 
        amount: '¥2,480', 
        category: '消耗品費', 
        score: 95 
      },
      { 
        id: 2, 
        date: '2026-07-14', 
        store: '△△コンビニ', 
        amount: '¥1,200', 
        category: '旅費交通費', 
        score: 87 
      },
      { 
        id: 3, 
        date: '2026-07-13', 
        store: '□□書店', 
        amount: '¥3,500', 
        category: '新聞図書費', 
        score: 92 
      },
    ]
    
  } catch (err) {
    error.value = '重複候補の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleApprove = (check: any) => {
  selectedCheck.value = check
  showApprovalModal.value = true
}

const handleReject = (check: any) => {
  selectedCheck.value = check
  // TODO: 却下処理を実装
  console.log('Reject:', check)
}

const confirmApproval = () => {
  // TODO: 承認処理を実装
  console.log('Approve:', selectedCheck.value)
  showApprovalModal.value = false
  uiStore.showSuccess('承認が完了しました')
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

      <AppTable
        v-if="!loading && !error"
        :columns="tableColumns"
        :rows="duplicateChecks"
        row-key="id"
        :sort-by="'score'"
        :sort-order="'desc'"
        class="mb-6"
      />

      <div v-if="!loading && !error && duplicateChecks.length > 0" class="space-y-4">
        <h3 class="text-lg font-medium text-gray-900">承認・却下操作</h3>
        <p class="text-gray-600">選択した重複候補に対して承認または却下の処理を行います。</p>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="check in duplicateChecks" 
            :key="check.id"
            class="border border-gray-200 rounded-lg p-4 flex justify-between items-center"
          >
            <div>
              <p class="font-medium">{{ check.store }}</p>
              <p class="text-sm text-gray-600">{{ check.date }} - {{ check.amount }}</p>
            </div>
            <div class="flex gap-2">
              <AppButton 
                variant="secondary" 
                size="sm" 
                @click="handleApprove(check)"
              >
                承認
              </AppButton>
              <AppButton 
                variant="danger" 
                size="sm" 
                @click="handleReject(check)"
              >
                却下
              </AppButton>
            </div>
          </div>
        </div>
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
            <div><span class="font-medium">店舗名:</span> {{ selectedCheck?.store }}</div>
            <div><span class="font-medium">日付:</span> {{ selectedCheck?.date }}</div>
            <div><span class="font-medium">金額:</span> {{ selectedCheck?.amount }}</div>
            <div><span class="font-medium">勘定科目:</span> {{ selectedCheck?.category }}</div>
          </div>
        </div>

        <div class="flex gap-3 justify-end">
          <AppButton 
            variant="secondary" 
            @click="showApprovalModal = false"
          >
            キャンセル
          </AppButton>
          <AppButton 
            variant="primary" 
            @click="confirmApproval"
          >
            承認する
          </AppButton>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<style scoped>
/* Additional styles for duplicate check view */
</style>