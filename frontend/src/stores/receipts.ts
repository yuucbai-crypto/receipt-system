import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SearchResultItem } from '@/api/models/SearchResultItem'
import type { ApprovedFileListResponse } from '@/api/models/ApprovedFileListResponse'
import {
  getReceipts as apiGetReceipts,
  getReceipt as apiGetReceipt,
  approveReceipt as apiApproveReceipt,
  rejectReceipt as apiRejectReceipt,
  getDuplicateChecks as apiGetDuplicateChecks,
  approveDuplicateCheck as apiApproveDuplicateCheck,
  rejectDuplicateCheck as apiRejectDuplicateCheck,
  getApprovedFiles as apiGetApprovedFiles,
} from '@/api/services/receipts'

export interface Receipt {
  id: string
  date: string
  store: string
  amount: number
  category: string
  status: 'pending' | 'approved' | 'rejected'
  tags: string[]
  imageUrl?: string
}

export interface DuplicateReceipt {
  receipt: Receipt
  score: number
}

export interface DuplicateCheckResult {
  duplicates: DuplicateReceipt[]
  score: number
}

export interface ApprovedFileInfo {
  id: string
  fileName: string
  date: string
  store: string
  amount: number
  category: string
}

export interface ReceiptsState {
  receipts: Receipt[]
  totalCount: number
  currentPage: number
  pageSize: number
  searchQuery: string
  selectedReceipt: Receipt | null
  duplicateCheckResult: DuplicateCheckResult | null
  isLoading: boolean
  error: string | null
}

export interface SetReceiptsPayload {
  receipts: Receipt[]
  total: number
}

export interface ApproveReceiptPayload {
  receiptId: string
  comment?: string
}

export interface RejectReceiptPayload {
  receiptId: string
  reason: string
  reasonDetail?: string
}

export interface CheckDuplicatesPayload {
  receiptId: string
}

export const useReceiptsStore = defineStore('receipts', () => {
  const receipts = ref<Receipt[]>([])
  const totalCount = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const searchQuery = ref('')
  const selectedReceipt = ref<Receipt | null>(null)
  const duplicateCheckResult = ref<DuplicateCheckResult | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

  const setReceipts = (payload: SetReceiptsPayload): void => {
    receipts.value = payload.receipts
    totalCount.value = payload.total
  }

  const setSearchQuery = (query: string): void => {
    searchQuery.value = query
    currentPage.value = 1
  }

  const setPage = (page: number): void => {
    currentPage.value = page
  }

  const setPageSize = (size: number): void => {
    pageSize.value = size
    currentPage.value = 1
  }

  const setSelectedReceipt = (receipt: Receipt | null): void => {
    selectedReceipt.value = receipt
  }

  const setDuplicateCheckResult = (result: DuplicateCheckResult): void => {
    duplicateCheckResult.value = result
  }

  const setLoading = (loading: boolean): void => {
    isLoading.value = loading
  }

  const setError = (err: string | null): void => {
    error.value = err
  }

  const clearError = (): void => {
    error.value = null
  }

  // API actions
  const fetchReceipts = async (): Promise<void> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiGetReceipts()
      // Transform SearchResultItem[] to Receipt[]
      const transformedReceipts: Receipt[] = response.data.map((item: SearchResultItem) => ({
        id: String(item.receipt_id),
        date: item.receipt_date || '',
        store: item.store_name || '',
        amount: item.total_amount || 0,
        category: item.category || '',
        status: 'pending' as const, // Search result doesn't have status
        tags: item.tags || [],
        imageUrl: undefined,
      }))
      setReceipts({ receipts: transformedReceipts, total: transformedReceipts.length })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'レシート一覧の取得に失敗しました'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const fetchReceipt = async (id: string): Promise<Receipt | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiGetReceipt(parseInt(id, 10))
      const item = response.data
      return {
        id: String(item.receipt_id),
        date: item.receipt_date || '',
        store: item.store_name || '',
        amount: item.total_amount || 0,
        category: item.category || '',
        status: 'pending' as const,
        tags: item.tags || [],
        imageUrl: undefined,
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'レシート詳細の取得に失敗しました'
      setError(message)
      return null
    } finally {
      setLoading(false)
    }
  }

  const approveReceipt = async (payload: ApproveReceiptPayload): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    try {
      await apiApproveReceipt(parseInt(payload.receiptId, 10), payload.comment)
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '承認に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const rejectReceipt = async (payload: RejectReceiptPayload): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    try {
      await apiRejectReceipt(parseInt(payload.receiptId, 10), payload.reason)
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '却下に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const checkDuplicates = async (): Promise<DuplicateCheckResult> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiGetDuplicateChecks()
      const duplicates: DuplicateReceipt[] = response.data.map((item: SearchResultItem) => ({
        receipt: {
          id: String(item.receipt_id),
          date: item.receipt_date || '',
          store: item.store_name || '',
          amount: item.total_amount || 0,
          category: item.category || '',
          status: 'pending' as const,
          tags: item.tags || [],
          imageUrl: undefined,
        },
        score: item.score,
      }))
      const result: DuplicateCheckResult = { duplicates, score: duplicates.length > 0 ? duplicates[0].score : 0 }
      setDuplicateCheckResult(result)
      return result
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェックに失敗しました'
      setError(message)
      return { duplicates: [], score: 0 }
    } finally {
      setLoading(false)
    }
  }

  const approveDuplicateCheck = async (id: string, comment?: string): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    try {
      await apiApproveDuplicateCheck(parseInt(id, 10), comment)
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェック承認に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const rejectDuplicateCheck = async (id: string, reason: string): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    try {
      await apiRejectDuplicateCheck(parseInt(id, 10), reason)
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェック却下に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const fetchApprovedFiles = async (): Promise<ApprovedFileInfo[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiGetApprovedFiles()
      return response.data.map((item: ApprovedFileListResponse['items'][0]) => ({
        id: item.filepath, // Use filepath as id
        fileName: item.filename,
        date: item.modified_at.split('T')[0], // Extract date from modified_at
        store: '', // Not available in ApprovedFileInfo
        amount: 0, // Not available
        category: item.category_folder,
      }))
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'ファイル一覧の取得に失敗しました'
      setError(message)
      return []
    } finally {
      setLoading(false)
    }
  }

  return {
    receipts,
    totalCount,
    currentPage,
    pageSize,
    searchQuery,
    selectedReceipt,
    duplicateCheckResult,
    isLoading,
    error,
    totalPages,
    setReceipts,
    setSearchQuery,
    setPage,
    setPageSize,
    setSelectedReceipt,
    setDuplicateCheckResult,
    setLoading,
    setError,
    clearError,
    fetchReceipts,
    fetchReceipt,
    approveReceipt,
    rejectReceipt,
    checkDuplicates,
    approveDuplicateCheck,
    rejectDuplicateCheck,
    fetchApprovedFiles,
  }
})