<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useUIStore } from '../stores/ui'
import { useReceiptsStore } from '../stores/receipts'
import AppLoading from './ui/AppLoading.vue'
import AppTable from './ui/AppTable.vue'
import AppButton from './ui/AppButton.vue'
import AppModal from './ui/AppModal.vue'
import ReceiptDetailView from './ReceiptDetailView.vue'

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
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0,
})
const sort = ref({
  by: 'date',
  order: 'desc' as 'asc' | 'desc'
})
const filters = ref({
  dateFrom: '',
  dateTo: '',
  category: '',
  tag: '',
  status: '',
})

// Modal for detail view
const showDetailModal = ref(false)
const selectedReceipt = ref<any>(null)

// Methods
const loadReceipts = async (page: number = 1) => {
  loading.value = true
  error.value = null
  
  try {
    const response = await receiptsStore.getReceipts({
      page,
      pageSize: pagination.value.pageSize,
      sortBy: sort.value.by,
      sortOrder: sort.value.order,
      ...filters.value,
    })
    
    tableRows.value = response.data.items
    pagination.value.total = response.data.total
    pagination.value.page = page
    
  } catch (err) {
    error.value = 'レシート一覧の読み込みに失敗しました'
    uiStore.showError('エラーが発生しました')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleSort = (key: string, order: 'asc' | 'desc') => {
  sort.value.by = key
  sort.value.order = order
  loadReceipts(pagination.value.page)
}

const handlePageChange = (page: number) => {
  loadReceipts(page)
}

const handleRowClick = (row: any) => {
  selectedReceipt.value = row
  showDetailModal.value = true
}

const handleFilterChange = (key: string, value: string) => {
  filters.value[key] = value
  // Reset to first page when filtering
  loadReceipts(1)
}

const resetFilters = () => {
  filters.value = {
    dateFrom: '',
    dateTo: '',
    category: '',
    tag: '',
    status: '',
  }
  loadReceipts(1)
}

// Watch for filter changes
watch(filters, () => {
  // Filtering is handled by the loadReceipts function when filters change
}, { deep: true })

// Lifecycle
onMounted(() => {
  loadReceipts()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-900">レシート一覧</h2>
      <AppButton variant="primary" size="sm" data-testid="receipt-list-add-button">
        新規追加
      </AppButton>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">日付(From)</label>
          <input
            type="date"
            v-model="filters.dateFrom"
            @change="handleFilterChange('dateFrom', filters.dateFrom)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            data-testid="receipt-list-filter-date-from"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">日付(To)</label>
          <input
            type="date"
            v-model="filters.dateTo"
            @change="handleFilterChange('dateTo', filters.dateTo)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            data-testid="receipt-list-filter-date-to"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">勘定科目</label>
          <select
            v-model="filters.category"
            @change="handleFilterChange('category', filters.category)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            data-testid="receipt-list-filter-category"
          >
            <option value="">すべて</option>
            <option value="消耗品費">消耗品費</option>
            <option value="旅費交通費">旅費交通費</option>
            <option value="新聞図書費">新聞図書費</option>
            <option value="通信費">通信費</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">タグ</label>
          <input
            type="text"
            v-model="filters.tag"
            @input="handleFilterChange('tag', filters.tag)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="タグを入力"
            data-testid="receipt-list-filter-tag"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
          <select
            v-model="filters.status"
            @change="handleFilterChange('status', filters.status)"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            data-testid="receipt-list-filter-status"
          >
            <option value="">すべて</option>
            <option value="承認済み">承認済み</option>
            <option value="未承認">未承認</option>
            <option value="却下">却下</option>
          </select>
        </div>
      </div>
      
      <div class="flex justify-end">
        <AppButton variant="secondary" size="sm" @click="resetFilters" data-testid="receipt-list-reset-filters">
          フィルターをリセット
        </AppButton>
      </div>
    </div>

    <!-- Receipt Table -->
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
        :sort-by="sort.by"
        :sort-order="sort.order"
        @sort="handleSort"
        @row-click="handleRowClick"
        data-testid="receipt-list-table"
      />

      <!-- Pagination -->
      <div v-if="!loading && !error && pagination.total > 0" class="mt-6 flex items-center justify-between">
        <div class="text-sm text-gray-700">
          {{ (pagination.page - 1) * pagination.pageSize + 1 }} - 
          {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }}
        </div>
        <div class="flex gap-2">
          <AppButton
            variant="secondary"
            size="sm"
            :disabled="pagination.page <= 1"
            @click="handlePageChange(pagination.page - 1)"
            data-testid="receipt-list-prev-page"
          >
            前へ
          </AppButton>
          <AppButton
            variant="secondary"
            size="sm"
            :disabled="pagination.page * pagination.pageSize >= pagination.total"
            @click="handlePageChange(pagination.page + 1)"
            data-testid="receipt-list-next-page"
          >
            次へ
          </AppButton>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <AppModal
      v-model="showDetailModal"
      title="レシート詳細"
      size="lg"
      @close="showDetailModal = false"
      data-testid="receipt-detail-modal"
    >
      <ReceiptDetailView 
        :receipt-id="selectedReceipt?.id" 
        v-if="showDetailModal && selectedReceipt"
      />
    </AppModal>
  </div>
</template>

<style scoped>
/* Additional styles for receipt list view */
</style>