<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppButton from './ui/AppButton.vue'
import AppInput from './ui/AppInput.vue'
import AppSelect from './ui/AppSelect.vue'
import AppTable from './ui/AppTable.vue'
import AppLoading from './ui/AppLoading.vue'

// ストアのインスタンス化
const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()

// 検索条件
const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const amountMin = ref('')
const amountMax = ref('')
const categoryFilter = ref('')
const tagFilter = ref('')
const statusFilter = ref('')

// フィルタリング用のオプション
const categories = [
  { value: '', label: 'すべて' },
  { value: '消耗品費', label: '消耗品費' },
  { value: '旅費交通費', label: '旅費交通費' },
  { value: '新聞図書費', label: '新聞図書費' },
]

const tags = [
  { value: '', label: 'すべて' },
  { value: '業務', label: '業務' },
  { value: '個人', label: '個人' },
]

const statuses = [
  { value: '', label: 'すべて' },
  { value: '未承認', label: '未承認' },
  { value: '承認済み', label: '承認済み' },
  { value: '却下', label: '却下' },
]

// 検索結果
const searchResults = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)

// テーブルのカラム定義
const tableColumns = [
  { key: 'date', header: '日付', sortable: true, data-testid: 'table-column-date' },
  { key: 'store', header: '店舗名', sortable: true, data-testid: 'table-column-store' },
  { key: 'amount', header: '金額', sortable: true, class: 'text-right', data-testid: 'table-column-amount' },
  { key: 'category', header: '勘定科目', sortable: true, data-testid: 'table-column-category' },
  { key: 'tags', header: 'タグ', data-testid: 'table-column-tags' },
  { key: 'status', header: 'ステータス', sortable: true, data-testid: 'table-column-status' },
]

// 検索処理
const performSearch = async () => {
  try {
    loading.value = true
    
    // 検索条件の構築
    const searchParams = {
      q: searchQuery.value,
      date_from: dateFrom.value,
      date_to: dateTo.value,
      amount_min: amountMin.value ? Number(amountMin.value) : undefined,
      amount_max: amountMax.value ? Number(amountMax.value) : undefined,
      category: categoryFilter.value,
      tag: tagFilter.value,
      status: statusFilter.value,
      page: currentPage.value,
      per_page: 20
    }
    
    // API呼び出し（仮実装）
    const results = await receiptsStore.searchReceipts(searchParams)
    
    searchResults.value = results.items || []
    totalPages.value = results.total_pages || 1
    totalItems.value = results.total_items || 0
    
    uiStore.showSuccess('検索が完了しました')
  } catch (error) {
    uiStore.showError('検索に失敗しました')
    console.error('Search failed:', error)
  } finally {
    loading.value = false
  }
}

// ページング処理
const changePage = (page: number) => {
  currentPage.value = page
  performSearch()
}

// 検索条件のリセット
const resetFilters = () => {
  searchQuery.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  amountMin.value = ''
  amountMax.value = ''
  categoryFilter.value = ''
  tagFilter.value = ''
  statusFilter.value = ''
  
  currentPage.value = 1
  searchResults.value = []
  totalPages.value = 1
  totalItems.value = 0
}

// 初期化
onMounted(() => {
  // 初回検索を実行（仮）
  performSearch()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 検索条件入力 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="search-filters">
      <h3 class="text-lg font-medium text-gray-900 mb-4">検索条件</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- 全文検索 -->
        <AppInput
          v-model="searchQuery"
          label="全文検索"
          placeholder="店舗名・メモ・AIコメント"
          data-testid="full-text-search-input"
        />
        
        <!-- 期間フィルター -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">期間</label>
          <div class="grid grid-cols-2 gap-2">
            <AppInput
              v-model="dateFrom"
              label="開始日"
              type="date"
              data-testid="date-from-input"
            />
            <AppInput
              v-model="dateTo"
              label="終了日"
              type="date"
              data-testid="date-to-input"
            />
          </div>
        </div>
        
        <!-- 金額範囲 -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">金額範囲</label>
          <div class="grid grid-cols-2 gap-2">
            <AppInput
              v-model="amountMin"
              label="最小金額"
              type="number"
              placeholder="0"
              data-testid="amount-min-input"
            />
            <AppInput
              v-model="amountMax"
              label="最大金額"
              type="number"
              placeholder="999999"
              data-testid="amount-max-input"
            />
          </div>
        </div>
        
        <!-- 勘定科目フィルター -->
        <AppSelect
          v-model="categoryFilter"
          label="勘定科目"
          :options="categories"
          data-testid="category-filter-select"
        />
        
        <!-- タグフィルター -->
        <AppSelect
          v-model="tagFilter"
          label="タグ"
          :options="tags"
          data-testid="tag-filter-select"
        />
        
        <!-- 承認状態フィルター -->
        <AppSelect
          v-model="statusFilter"
          label="承認状態"
          :options="statuses"
          data-testid="status-filter-select"
        />
      </div>
      
      <div class="flex gap-3 mt-4">
        <AppButton 
          variant="primary" 
          @click="performSearch"
          data-testid="search-btn"
        >
          検索
        </AppButton>
        <AppButton 
          variant="secondary" 
          @click="resetFilters"
          data-testid="reset-filters-btn"
        >
          リセット
        </AppButton>
      </div>
    </div>

    <!-- 検索結果 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" data-testid="search-results">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">検索結果</h3>
        <p class="text-sm text-gray-500" data-testid="result-count">
          合計 {{ totalItems }} 件
        </p>
      </div>
      
      <!-- ローディング表示 -->
      <AppLoading v-if="loading" :size="'md'" :variant="'spinner'" data-testid="search-loading" />
      
      <!-- 検索結果テーブル -->
      <div v-else>
        <AppTable
          :columns="tableColumns"
          :rows="searchResults"
          row-key="id"
          :sort-by="'date'"
          :sort-order="'desc'"
          data-testid="search-results-table"
          @sort="console.log"
        />
        
        <!-- ページング -->
        <div v-if="totalPages > 1" class="flex justify-center mt-4">
          <nav class="flex items-center space-x-2" data-testid="pagination">
            <AppButton
              v-for="page in totalPages"
              :key="page"
              variant="ghost"
              size="sm"
              :class="{ 'bg-blue-100': page === currentPage }"
              @click="changePage(page)"
              data-testid="page-btn"
            >
              {{ page }}
            </AppButton>
          </nav>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for search view */
</style>