<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppTable from './ui/AppTable.vue'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'

// Store
const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()

// Data
const loading = ref(false)
const error = ref<string | null>(null)
const tableColumns = ref([
  { key: 'id', header: 'ID', sortable: true },
  { key: 'date', header: '日付', sortable: true },
  { key: 'store', header: '店舗名', sortable: true },
  { key: 'amount', header: '金額', sortable: true, class: 'text-right' },
  { key: 'category', header: '勘定科目' },
  { key: 'status', header: 'ステータス' },
])
const tableRows = ref<any[]>([])

// Methods
const loadReceipts = async () => {
  loading.value = true
  error.value = null
  
  try {
    // TODO: API呼び出しを実装
    // const response = await receiptsStore.getReceipts()
    // tableRows.value = response.data
    console.log('Receipt list loading...')
    
    // デモ用のダミーデータ
    tableRows.value = [
      { id: 1, date: '2026-07-15', store: '○○スーパー', amount: '¥2,480', category: '消耗品費', status: '承認済み' },
      { id: 2, date: '2026-07-14', store: '△△コンビニ', amount: '¥1,200', category: '旅費交通費', status: '承認済み' },
      { id: 3, date: '2026-07-13', store: '□□書店', amount: '¥3,500', category: '新聞図書費', status: '未承認' },
      { id: 4, date: '2026-07-12', store: '★★薬局', amount: '¥890', category: '消耗品費', status: '却下' },
    ]
    
  } catch (err) {
    error.value = 'レシート一覧の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleRowClick = (row: any) => {
  console.log('Row clicked:', row)
  // TODO: 詳細画面へのナビゲーションを実装
}

// Lifecycle
onMounted(() => {
  loadReceipts()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">レシート一覧</h2>
      <AppButton variant="primary" size="sm">
        新規追加
      </AppButton>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <AppLoading v-if="loading" :overlay="true" message="レシート一覧を読み込み中..." />
      
      <div v-if="error" class="text-red-500 mb-4">
        {{ error }}
      </div>

      <AppTable
        v-if="!loading && !error"
        :columns="tableColumns"
        :rows="tableRows"
        row-key="id"
        :sort-by="'date'"
        :sort-order="'desc'"
        @row-click="handleRowClick"
      />
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for receipt list view */
</style>