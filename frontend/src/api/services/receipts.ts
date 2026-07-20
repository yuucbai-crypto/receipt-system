import { request } from '../core/request'
import { Receipt, DuplicateCheck } from '../models'

// レシート一覧を取得
export const getReceipts = async (): Promise<{ data: Receipt[] }> => {
  const response = await request({
    url: '/api/v1/receipts',
    method: 'GET'
  })
  return response.data
}

// 特定のレシートを取得
export const getReceipt = async (id: number): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipts/${id}`,
    method: 'GET'
  })
  return response.data
}

// レシートを承認
export const approveReceipt = async (id: number, comment?: string): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipt-approval/approve`,
    method: 'POST',
    body: { receipt_id: id, comment }
  })
  return response.data
}

// レシートを却下
export const rejectReceipt = async (id: number, reason: string): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipt-approval/reject`,
    method: 'POST',
    body: { receipt_id: id, reason }
  })
  return response.data
}

// 重複チェックを取得
export const getDuplicateChecks = async (): Promise<{ data: DuplicateCheck[] }> => {
  const response = await request({
    url: '/api/v1/duplicate-check',
    method: 'GET'
  })
  return response.data
}

// 重複チェックを承認
export const approveDuplicateCheck = async (id: number, comment?: string): Promise<{ data: DuplicateCheck }> => {
  const response = await request({
    url: `/api/v1/duplicate-check/${id}/review`,
    method: 'POST',
    body: { action: 'approve', comment }
  })
  return response.data
}

// 重複チェックを却下
export const rejectDuplicateCheck = async (id: number, reason: string): Promise<{ data: DuplicateCheck }> => {
  const response = await request({
    url: `/api/v1/duplicate-check/${id}/review`,
    method: 'POST',
    body: { action: 'reject', reason }
  })
  return response.data
}

// レシート画像を取得
export const getReceiptImage = async (id: number): Promise<Blob> => {
  const response = await request({
    url: `/api/v1/receipts/${id}/image`,
    method: 'GET',
    responseType: 'blob'
  })
  return response.data
}