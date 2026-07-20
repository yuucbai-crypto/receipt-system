import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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
}

export interface RejectReceiptPayload {
  receiptId: string
  reason: string
  reasonDetail?: string
}

export type CheckDuplicatesPayload = Record<string, unknown>

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

  // API actions - will be implemented with actual API calls
  const approveReceipt = async (_payload: ApproveReceiptPayload): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    let result: { success: boolean; error?: string }
    try {
      // const response = await api.receiptApproval.approve(payload)
      // return response
      result = { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '承認に失敗しました'
      setError(message)
      result = { success: false, error: message }
    } finally {
      setLoading(false)
    }
    return result
  }

  const rejectReceipt = async (_payload: RejectReceiptPayload): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    let result: { success: boolean; error?: string }
    try {
      // const response = await api.receiptApproval.reject(payload)
      // return response
      result = { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '却下に失敗しました'
      setError(message)
      result = { success: false, error: message }
    } finally {
      setLoading(false)
    }
    return result
  }

  const checkDuplicates = async (_payload: CheckDuplicatesPayload): Promise<DuplicateCheckResult> => {
    setLoading(true)
    setError(null)
    let result: DuplicateCheckResult
    try {
      // const response = await api.duplicateCheck.check(payload)
      // setDuplicateCheckResult(response)
      // return response
      result = { duplicates: [], score: 0 }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェックに失敗しました'
      setError(message)
      result = { duplicates: [], score: 0 }
    } finally {
      setLoading(false)
    }
    return result
  }

  const fetchApprovedFiles = async (): Promise<ApprovedFileInfo[]> => {
    setLoading(true)
    setError(null)
    let result: ApprovedFileInfo[]
    try {
      // const response = await api.fileManagement.listApproved()
      // return response.files
      result = []
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'ファイル一覧の取得に失敗しました'
      setError(message)
      result = []
    } finally {
      setLoading(false)
    }
    return result
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
    approveReceipt,
    rejectReceipt,
    checkDuplicates,
    fetchApprovedFiles,
  }
})