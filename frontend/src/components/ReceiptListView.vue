<template>
  <div class="receipt-list-view">
    <h1>レシート一覧</h1>
    
    <!-- フィルター -->
    <div class="filters" data-testid="receipt-list-filters">
      <AppInput 
        v-model="filters.searchTerm"
        placeholder="検索..."
        data-testid="search-input"
      />
      
      <AppInput 
        v-model="filters.category"
        placeholder="勘定科目"
        data-testid="category-filter"
      />
      
      <AppInput 
        v-model="filters.tag"
        placeholder="タグ"
        data-testid="tag-filter"
      />
      
      <div class="date-filters">
        <AppInput 
          v-model="filters.startDate"
          type="text"
          data-testid="start-date-filter"
        />
        <AppInput 
          v-model="filters.endDate"
          type="text"
          data-testid="end-date-filter"
        />
      </div>
      
      <AppButton data-testid="apply-filters-button" @click="applyFilters">
        適用
      </AppButton>
      
      <AppButton data-testid="reset-filters-button" @click="resetFilters">
        リセット
      </AppButton>
    </div>

    <!-- ローディング表示 -->
    <AppLoading v-if="loading" data-testid="receipt-list-loading" />

    <!-- エラーメッセージ -->
    <div v-if="error" class="error-message" data-testid="receipt-list-error">
      {{ error }}
    </div>

    <!-- レシート一覧 -->
    <AppTable 
      :columns="tableHeaders"
      :rows="receipts"
      :row-key="'id'"
      :loading="loading"
      data-testid="receipt-list-table"
      @row-click="handleRowClick"
    >
      <template #cell-date="{ item }">
        {{ formatDate(item.date) }}
      </template>
      
      <template #cell-amount="{ item }">
        {{ formatCurrency(item.amount) }}
      </template>
      
      <template #cell-category="{ item }">
        {{ item.category }}
      </template>
      
      <template #cell-tags="{ item }">
        <span 
          v-for="tag in item.tags" 
          :key="tag"
          class="tag-badge"
          data-testid="receipt-tag-badge"
        >
          {{ tag }}
        </span>
      </template>
      
      <template #cell-status="{ item }">
        <AppBadge 
          :status="item.status" 
          :text="getStatusText(item.status)"
        />
      </template>
    </AppTable>

    <!-- ページネーション -->
    <div class="pagination" data-testid="receipt-list-pagination">
      <AppButton 
        :disabled="currentPage <= 1" 
        data-testid="prev-page-button"
        @click="prevPage"
      >
        前へ
      </AppButton>
      
      <span>{{ currentPage }} / {{ totalPages }}</span>
      
      <AppButton 
        :disabled="currentPage >= totalPages" 
        data-testid="next-page-button"
        @click="nextPage"
      >
        次へ
      </AppButton>
    </div>

    <!-- 詳細モーダル -->
    <AppModal 
      v-if="selectedReceipt"
      :model-value="!!selectedReceipt"
      data-testid="receipt-detail-modal"
      @close="closeDetailModal"
    >
      <template #header>
        <h2>レシート詳細</h2>
      </template>
      
      <template #body>
        <ReceiptDetailView 
          :receipt="selectedReceipt" 
          @close="closeDetailModal"
        />
      </template>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { formatDate, formatCurrency } from '@/utils/currency';
import { getReceipts } from '@/api/receipts';
import AppInput from '@/components/ui/AppInput.vue';
import AppButton from '@/components/ui/AppButton.vue';
import AppTable from '@/components/ui/AppTable.vue';
import AppLoading from '@/components/ui/AppLoading.vue';
import AppBadge from '@/components/ui/AppBadge.vue';
import AppModal from '@/components/ui/AppModal.vue';
import ReceiptDetailView from '@/components/ReceiptDetailView.vue';

// フィルター条件
const filters = ref({
  searchTerm: '',
  category: '',
  tag: '',
  startDate: '',
  endDate: ''
});

// レシート一覧
const receipts = ref<any[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const currentPage = ref(1);
const totalPages = ref(1);

// 選択されたレシート（詳細表示用）
const selectedReceipt = ref<any>(null);

// テーブルヘッダー
const tableHeaders = [
  { key: 'date', header: '日付', sortable: false },
  { key: 'amount', header: '金額', sortable: true },
  { key: 'category', header: '勘定科目', sortable: true },
  { key: 'tags', header: 'タグ', sortable: false },
  { key: 'status', header: 'ステータス', sortable: false }
];

// レシート一覧取得
const fetchReceipts = async (page: number = 1) => {
  loading.value = true;
  error.value = null;
  
  try {
    const response = await getReceipts({
      page,
      limit: 20,
      ...filters.value
    });
    
    receipts.value = response.items;
    currentPage.value = response.page;
    totalPages.value = response.total_pages;
  } catch (err) {
    error.value = 'レシート一覧の取得に失敗しました';
    console.error('レシート一覧取得エラー:', err);
  } finally {
    loading.value = false;
  }
};

// フィルター適用
const applyFilters = () => {
  fetchReceipts(1); // 最初のページから再取得
};

// フィルターリセット
const resetFilters = () => {
  filters.value = {
    searchTerm: '',
    category: '',
    tag: '',
    startDate: '',
    endDate: ''
  };
  fetchReceipts(1);
};

// 前のページ
const prevPage = () => {
  if (currentPage.value > 1) {
    fetchReceipts(currentPage.value - 1);
  }
};

// 次のページ
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    fetchReceipts(currentPage.value + 1);
  }
};

// 行クリック時の処理（詳細モーダル表示）
const handleRowClick = (receipt: any) => {
  selectedReceipt.value = receipt;
};

// 詳細モーダルを閉じる
const closeDetailModal = () => {
  selectedReceipt.value = null;
};

// ステータスのテキスト取得
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '承認待ち',
    approved: '承認済み',
    rejected: '却下済み'
  };
  
  return statusMap[status] || status;
};

// 初期データ取得
onMounted(() => {
  fetchReceipts();
});

// ページ変更時の処理
watch(currentPage, (newPage) => {
  if (newPage !== currentPage.value) {
    fetchReceipts(newPage);
  }
});
</script>

<style scoped>
.receipt-list-view {
  padding: 20px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.date-filters {
  display: flex;
  gap: 10px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.tag-badge {
  background-color: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  margin-right: 5px;
}

.error-message {
  color: #f44336;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 4px;
  margin-bottom: 20px;
}
</style>