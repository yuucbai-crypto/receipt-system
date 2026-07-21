import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DuplicateCheckListResponse } from '@/api/models/DuplicateCheckListResponse'
import { ReceiptsService } from '@/api/services/ReceiptsService'
import { DuplicateCheckService } from '@/api/services/DuplicateCheckService'
import { ReceiptApprovalService } from '@/api/services/ReceiptApprovalService'
import { FileManagementService } from '@/api/services/FileManagementService'

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

export interface ApprovedFileInfoUI {
  id: string
  fileName: string
  date: string
  store: string
  amount: number
  category: string
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
      const response = await ReceiptsService.listReceiptsApiV1ReceiptsGet(
        null,
        null,
        null,
        null,
        currentPage.value,
        pageSize.value
      )
      // Transform ReceiptResponse[] to Receipt[]
      const transformedReceipts: Receipt[] = response.items.map((item) => ({
        id: item.id.toString(),
        date: item.receipt_date || '',
        store: item.store_name || '',
        amount: item.total_amount || 0,
        category: item.category_name || '',
        status: item.status as 'pending' | 'approved' | 'rejected',
        tags: item.tags || [],
        imageUrl: undefined,
      }))
      setReceipts({ receipts: transformedReceipts, total: response.total })
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
      const item = await ReceiptsService.getReceiptApiV1ReceiptsReceiptIdGet(
        parseInt(id, 10)
      )
      return {
        id: String(item.id),
        date: item.receipt_date || '',
        store: item.store_name || '',
        amount: item.total_amount || 0,
        category: item.category_name || '',
        status: item.status as 'pending' | 'approved' | 'rejected',
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
      await ReceiptApprovalService.approveReceiptApiV1ReceiptApprovalApprovePost({
        receipt_id: parseInt(payload.receiptId, 10),
        approve: true,
        user_note: payload.comment,
      })
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
      await ReceiptApprovalService.rejectReceiptApiV1ReceiptApprovalRejectPost(
        null,
        {
          receipt_id: parseInt(payload.receiptId, 10),
          reason_code: payload.reason,
          reason_text: payload.reason,
        }
      )
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '却下に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const getReceiptDuplicateChecks = async (receiptId: number): Promise<{ data: any[] }> => {
    setLoading(true)
    setError(null)
    try {
      const response = await DuplicateCheckService.getReceiptDuplicateChecksApiV1DuplicateCheckReceiptReceiptIdChecksGet(
        receiptId
      )
      return { data: response }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェックの取得に失敗しました'
      setError(message)
      return { data: [] }
    } finally {
      setLoading(false)
    }
  }

  const reviewDuplicateCheck = async (id: string, payload: { userConfirmed: boolean; userNote: string }): Promise<{ success: boolean; error?: string }> => {
    setLoading(true)
    setError(null)
    try {
      await DuplicateCheckService.reviewDuplicateCheckApiV1DuplicateCheckDuplicateCheckIdReviewPost(
        parseInt(id, 10),
        {
          user_confirmed: payload.userConfirmed,
          user_note: payload.userNote,
        }
      )
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '重複チェック処理に失敗しました'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const fetchApprovedFiles = async (): Promise<ApprovedFileInfoUI[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await FileManagementService.listApprovedFilesApiV1FileManagementListApprovedPost({
        page: 1,
        page_size: 20,
      })
      const files: ApprovedFileInfoUI[] = response.items.map((item) => ({
        id: item.filepath,
        fileName: item.filename,
        date: item.modified_at.split('T')[0],
        store: '',
        amount: 0,
        category: item.category_folder,
      }))
      return files
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
    getReceiptDuplicateChecks,
    reviewDuplicateCheck,
    fetchApprovedFiles,
  }
})