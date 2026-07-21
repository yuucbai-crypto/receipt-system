<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUIStore } from './stores/ui'
import { useReceiptsStore } from './stores/receipts'

// Import components to ensure they're registered
import AppButton from './components/ui/AppButton.vue'
import AppInput from './components/ui/AppInput.vue'
import AppModal from './components/ui/AppModal.vue'
import AppToast from './components/ui/AppToast.vue'
import AppLoading from './components/ui/AppLoading.vue'
import AppTable from './components/ui/AppTable.vue'
import AppImagePreview from './components/ui/AppImagePreview.vue'
import AppBadge from './components/ui/AppBadge.vue'
import AppTabs from './components/ui/AppTabs.vue'
import ReceiptListView from './components/ReceiptListView.vue'
import ReceiptDetailView from './components/ReceiptDetailView.vue'
import DuplicateCheckView from './components/DuplicateCheckView.vue'

const uiStore = useUIStore()
const receiptsStore = useReceiptsStore()

const showModal = ref(false)
const imagePreviewOpen = ref(false)
const previewImage = ref('')
const activeTab = ref('dashboard')
const email = ref('')
const password = ref('')

const tabs = [
  { key: 'dashboard', label: 'ダッシュボード' },
  { key: 'receipts', label: 'レシート一覧', badge: 42 },
  { key: 'search', label: '検索' },
  { key: 'settings', label: '設定' },
  { key: 'duplicate-check', label: '重複チェック' },
]

const tableColumns = [
  { key: 'date', header: '日付', sortable: true },
  { key: 'store', header: '店舗名', sortable: true },
  { key: 'amount', header: '金額', sortable: true, class: 'text-right' },
  { key: 'category', header: '勘定科目' },
  { key: 'status', header: 'ステータス' },
]

const tableRows = [
  { id: 1, date: '2026-07-15', store: '○○スーパー', amount: '¥2,480', category: '消耗品費', status: '承認済み' },
  { id: 2, date: '2026-07-14', store: '△△コンビニ', amount: '¥1,200', category: '旅費交通費', status: '承認済み' },
  { id: 3, date: '2026-07-13', store: '□□書店', amount: '¥3,500', category: '新聞図書費', status: '未承認' },
  { id: 4, date: '2026-07-12', store: '★★薬局', amount: '¥890', category: '消耗品費', status: '却下' },
]

const handleTestToast = (type: 'success' | 'error' | 'warning' | 'info') => {
  const methodMap = {
    success: 'showSuccess',
    error: 'showError',
    warning: 'showWarning',
    info: 'showInfo',
  } as const
  const method = methodMap[type]
  uiStore[method](`${type} トーストのテストです`)
}

const handleOpenImagePreview = (src: string) => {
  previewImage.value = src
  imagePreviewOpen.value = true
}

interface TableRow {
  id: number
  date: string
  store: string
  amount: string
  category: string
  status: string
}

const handleTableRowClick = (row: Record<string, unknown>) => {
  const tableRow = row as unknown as TableRow
  console.log('Row clicked:', row)
  uiStore.showInfo(`${tableRow.store} を選択しました`)
}

// Tab navigation handling
const currentView = computed(() => {
  switch (activeTab.value) {
    case 'dashboard':
      return 'ダッシュボード'
    case 'receipts':
      return 'レシート一覧'
    case 'search':
      return '検索'
    case 'settings':
      return '設定'
    case 'duplicate-check':
      return '重複チェック'
    default:
      return 'ダッシュボード'
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-40">
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="メインナビゲーション">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-8">
            <h1 class="text-xl font-bold text-gray-900" data-testid="app-title">
              レシート管理システム
            </h1>
            <AppTabs v-model="activeTab" :tabs="tabs" data-testid="main-tabs" />
          </div>
          <div class="flex items-center gap-4">
            <AppBadge variant="success" dot>オンライン</AppBadge>
            <AppButton variant="ghost" size="sm" data-testid="header-info-btn" @click="handleTestToast('info')">
              情報
            </AppButton>
          </div>
        </div>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Toast Container -->
      <AppToast :toasts="uiStore.toasts" data-testid="global-toast" @remove="uiStore.removeToast" />

      <!-- Global Loading Overlay -->
      <AppLoading
        v-if="uiStore.globalLoading"
        :overlay="true"
        :message="uiStore.loadingMessage"
        data-testid="global-loading"
      />

      <!-- Main Content Area -->
      <section class="space-y-8" data-testid="main-content">
        <!-- Dashboard View -->
        <div v-if="activeTab === 'dashboard'" class="bg-white rounded-xl border border-gray-200 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">ダッシュボード</h2>
          <p>ダッシュボードの内容がここに表示されます。</p>
        </div>

        <!-- Receipt List View -->
        <div v-else-if="activeTab === 'receipts'" class="bg-white rounded-xl border border-gray-200 p-6">
          <ReceiptListView />
        </div>

        <!-- Search View -->
        <div v-else-if="activeTab === 'search'" class="bg-white rounded-xl border border-gray-200 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">検索</h2>
          <p>検索機能がここに表示されます。</p>
        </div>

        <!-- Settings View -->
        <div v-else-if="activeTab === 'settings'" class="bg-white rounded-xl border border-gray-200 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">設定</h2>
          <p>設定画面がここに表示されます。</p>
        </div>

        <!-- Duplicate Check View -->
        <div v-else-if="activeTab === 'duplicate-check'" class="bg-white rounded-xl border border-gray-200 p-6">
          <DuplicateCheckView />
        </div>

        <!-- Demo Section: Components Showcase (when no tab is selected) -->
        <div v-else class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-section">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">コンポーネントデモ</h2>
          <!-- Buttons Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-buttons">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-buttons-title">Button コンポーネント</h2>
            <div class="flex flex-wrap gap-3" data-testid="buttons-container">
              <AppButton variant="primary" size="sm" data-testid="btn-primary-sm" @click="handleTestToast('success')">
                Primary Small
              </AppButton>
              <AppButton variant="primary" size="md" data-testid="btn-primary-md" @click="handleTestToast('success')">
                Primary Medium
              </AppButton>
              <AppButton variant="primary" size="lg" data-testid="btn-primary-lg" @click="handleTestToast('success')">
                Primary Large
              </AppButton>
              <AppButton variant="secondary" data-testid="btn-secondary" @click="handleTestToast('info')">
                Secondary
              </AppButton>
              <AppButton variant="danger" data-testid="btn-danger" @click="handleTestToast('error')">
                Danger
              </AppButton>
              <AppButton variant="ghost" data-testid="btn-ghost" @click="showModal = true">
                Ghost (Modal)
              </AppButton>
              <AppButton variant="primary" :loading="true" disabled data-testid="btn-loading">
                Loading
              </AppButton>
              <AppButton variant="primary" disabled data-testid="btn-disabled">
                Disabled
              </AppButton>
            </div>
          </div>

          <!-- Input Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-inputs">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-inputs-title">Input コンポーネント</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="inputs-container">
              <AppInput
                v-model="email"
                label="メールアドレス"
                type="email"
                placeholder="example@example.com"
                data-testid="input-email"
              />
              <AppInput
                v-model="password"
                label="パスワード"
                type="password"
                placeholder="********"
                data-testid="input-password"
              />
              <AppInput
                label="数値入力"
                type="number"
                placeholder="1000"
                :model-value="''"
                data-testid="input-number"
              />
              <AppInput
                label="必須項目"
                required
                error="この項目は必須です"
                :model-value="''"
                data-testid="input-required"
              />
              <AppInput
                label="無効状態"
                disabled
                placeholder="入力できません"
                :model-value="''"
                data-testid="input-disabled"
              />
            </div>
          </div>

          <!-- Badges Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-badges">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-badges-title">Badge コンポーネント</h2>
            <div class="flex flex-wrap gap-2" data-testid="badges-container">
              <AppBadge variant="default" data-testid="badge-default">Default</AppBadge>
              <AppBadge variant="success" dot data-testid="badge-success">成功</AppBadge>
              <AppBadge variant="warning" dot data-testid="badge-warning">警告</AppBadge>
              <AppBadge variant="danger" dot data-testid="badge-danger">エラー</AppBadge>
              <AppBadge variant="info" dot data-testid="badge-info">情報</AppBadge>
              <AppBadge variant="outline" data-testid="badge-outline">Outline</AppBadge>
              <AppBadge variant="success" removable data-testid="badge-removable" @remove="uiStore.showSuccess('バッジが削除されました')">
                削除可能
              </AppBadge>
              <AppBadge variant="default" size="sm" data-testid="badge-sm">Small</AppBadge>
              <AppBadge variant="default" size="md" data-testid="badge-md">Medium</AppBadge>
              <AppBadge variant="default" size="lg" data-testid="badge-lg">Large</AppBadge>
            </div>
          </div>

          <!-- Table Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-table">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-table-title">Table コンポーネント</h2>
            <AppTable
              :columns="tableColumns"
              :rows="tableRows"
              row-key="id"
              :sort-by="'date'"
              :sort-order="'desc'"
              data-testid="demo-table"
              @sort="console.log"
              @row-click="handleTableRowClick"
            />
          </div>

          <!-- Loading Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-loading">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-loading-title">Loading コンポーネント</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6 items-center" data-testid="loadings-container">
              <div class="text-center">
                <AppLoading :size="'sm'" :variant="'spinner'" data-testid="loading-spinner-sm" />
                <p class="mt-2 text-sm text-gray-500">Spinner Small</p>
              </div>
              <div class="text-center">
                <AppLoading :size="'md'" :variant="'spinner'" data-testid="loading-spinner-md" />
                <p class="mt-2 text-sm text-gray-500">Spinner Medium</p>
              </div>
              <div class="text-center">
                <AppLoading :size="'md'" :variant="'dots'" data-testid="loading-dots" />
                <p class="mt-2 text-sm text-gray-500">Dots</p>
              </div>
              <div class="text-center">
                <AppLoading :size="'md'" :variant="'pulse'" data-testid="loading-pulse" />
                <p class="mt-2 text-sm text-gray-500">Pulse</p>
              </div>
              <div class="text-center">
                <AppLoading :size="'md'" :variant="'bars'" data-testid="loading-bars" />
                <p class="mt-2 text-sm text-gray-500">Bars</p>
              </div>
              <div class="text-center">
                <AppLoading :size="'md'" :variant="'spinner'" :overlay="true" message="オーバーレイ読み込み中..." data-testid="loading-overlay" />
                <p class="mt-2 text-sm text-gray-500">Overlay</p>
              </div>
            </div>
          </div>

          <!-- Image Preview Demo -->
          <div class="bg-white rounded-xl border border-gray-200 p-6" data-testid="demo-image-preview">
            <h2 class="text-lg font-semibold text-gray-900 mb-4" data-testid="demo-image-title">ImagePreview コンポーネント</h2>
            <div class="flex gap-4" data-testid="image-preview-triggers">
              <AppButton data-testid="btn-preview-1" @click="handleOpenImagePreview('https://picsum.photos/800/600')">
                風景画像を開く
              </AppButton>
              <AppButton data-testid="btn-preview-2" @click="handleOpenImagePreview('https://picsum.photos/600/800')">
                縦長画像を開く
              </AppButton>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <p class="text-center text-sm text-gray-500" data-testid="footer-text">
          レシート管理システム - Frontend Demo (Issue #5)
        </p>
      </div>
    </footer>

    <!-- Modal Demo -->
    <AppModal
      v-model="showModal"
      title="モーダルのデモ"
      description="これはモーダルダイアログのデモです。コンテンツをここに配置できます。"
      size="md"
      data-testid="demo-modal"
      @close="showModal = false"
    >
      <div class="space-y-4" data-testid="modal-content">
        <p class="text-gray-600">モーダルの内容がここに表示されます。</p>
        <div class="flex gap-3 justify-end">
          <AppButton variant="secondary" data-testid="modal-cancel" @click="showModal = false">
            キャンセル
          </AppButton>
          <AppButton variant="primary" data-testid="modal-confirm" @click="showModal = false">
            確認
          </AppButton>
        </div>
      </div>
    </AppModal>

    <!-- Image Preview Modal -->
    <AppImagePreview
      v-model:open="imagePreviewOpen"
      :src="previewImage"
      title="プレビュー画像"
      data-testid="demo-image-preview"
      @close="imagePreviewOpen = false"
    />
  </div>
</template>

<style scoped>
/* Additional styles for demo */
</style>