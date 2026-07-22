<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useUIStore } from '../stores/ui'
import { ReceiptsService } from '@/api/services/ReceiptsService';
import AppTable from './ui/AppTable.vue'
import AppLoading from './ui/AppLoading.vue'
import AppButton from './ui/AppButton.vue'

// Store
const uiStore = useUIStore()

// Data
const loading = ref(false)
const error = ref<string | null>(null)
const tableColumns = ref([
  { key: 'id', header: 'ID', sortable: true, data-testid: 'receipt-id-column' },
  { key: 'date', header: '日付', sortable: true, data-testid: 'receipt-date-column' },
  { key: 'store', header: '店舗名', sortable: true, data-testid: 'receipt-store-column' },
  { key: 'amount', header: '金額', sortable: true, class: 'text-right', data-testid: 'receipt-amount-column' },
  { key: 'category', header: '勘定科目', data-testid: 'receipt-category-column' },
  { key: 'status', header: 'ステータス', data-testid: 'receipt-status-column' },
])
const tableRows = ref<any[]>([])

// Filters and pagination
const filters = ref({
  status: null as string | null,
  categoryId: null as number | null,
  dateFrom: null as string | null,
  dateTo: null as string | null,
  search: ''
})
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// Methods
const loadReceipts = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await ReceiptsService.listReceiptsApiV1ReceiptsGet(
      filters.value.status,
      filters.value.categoryId,
      filters.value.dateFrom,
      filters.value.dateTo,
      pagination.value.page,
      pagination.value.pageSize
    )
    
    tableRows.value = response.receipts || []
    pagination.value.total = response.total || 0
    
  } catch (err) {
    error.value = 'レシート一覧の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleRowClick = (row: any) => {
  // Navigate to receipt detail page
  console.log('Row clicked:', row)
  // In a real implementation, this would use router.push
}

const handleFilterChange = (filterName: string, value: any) => {
  filters.value[filterName] = value
  pagination.value.page = 1 // Reset to first page when filtering
  loadReceipts()
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadReceipts()
}

// Lifecycle
onMounted(() => {
  loadReceipts()
})

// Reload when filters or pagination change
watch([() => filters.value, () => pagination.value], () => {
  // This will be handled by the individual filter/page change functions
}, { deep: true })
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900" data-testid="receipt-list-title">レシート一覧</h2>
      <AppButton variant="primary" size="sm" data-testid="add-receipt-button">
        新規追加
      </AppButton>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <!-- Filters -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1" data-testid="status-filter-label">ステータス</label>
          <select 
            v-model="filters.status"
            @change="handleFilterChange('status', $event.target.value)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            data-testid="status-filter-select"
          >
            <option value="">すべて</option>
            <option value="approved">承認済み</option>
            <option value="rejected">却下</option>
            <option value="pending">未承認</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1" data-testid="category-filter-label">勘定科目</label>
          <select 
            v-model="filters.categoryId"
            @change="handleFilterChange('categoryId', $event.target.value ? parseInt($event.target.value) : null)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            data-testid="category-filter-select"
          >
            <option value="">すべて</option>
            <option value="1">消耗品費</option>
            <option value="2">旅費交通費</option>
            <option value="3">新聞図書費</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1" data-testid="date-from-filter-label">開始日</label>
          <input 
            type="date"
            v-model="filters.dateFrom"
            @change="handleFilterChange('dateFrom', $event.target.value)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            data-testid="date-from-filter-input"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1" data-testid="date-to-filter-label">終了日</label>
          <input 
            type="date"
            v-model="filters.dateTo"
            @change="handleFilterChange('dateTo', $event.target.value)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            data-testid="date-to-filter-input"
          />
        </div>
      </div>

      <!-- Search -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1" data-testid="search-label">検索</label>
        <input 
          type="text"
          v-model="filters.search"
          @input="handleFilterChange('search', $event.target.value)"
          placeholder="店舗名や金額で検索..."
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          data-testid="search-input"
        />
      </div>

      <AppLoading v-if="loading" :overlay="true" message="レシート一覧を読み込み中..." />
      
      <div v-if="error" class="text-red-500 mb-4" data-testid="receipt-list-error">
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
        data-testid="receipt-table"
      />

      <!-- Pagination -->
      <div v-if="!loading && !error && tableRows.length > 0" class="mt-6 flex justify-center">
        <nav class="flex items-center space-x-2">
          <button 
            v-for="page in Math.ceil(pagination.total / pagination.pageSize)"
            :key="page"
            @click="handlePageChange(page)"
            :class="[
              'px-3 py-1 rounded-md text-sm font-medium',
              page === pagination.page 
                ? 'bg-indigo-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            ]"
            :data-testid="`page-${page}-button`"
          >
            {{ page }}
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for receipt list view */
</style>