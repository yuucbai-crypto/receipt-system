// Frontend API service for receipts
// Uses the generated openapi-typescript-codegen request function

import { request } from '../core/request'

// Define types locally since models directory doesn't exist
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

export interface DuplicateCheck {
  id: string
  receiptId: string
  duplicateReceiptId: string
  score: number
  status: 'pending' | 'approved' | 'rejected'
  comment?: string
}

export interface ApprovedFileInfo {
  id: string
  fileName: string
  date: string
  store: string
  amount: number
  category: string
}

// レシート一覧を取得
export const getReceipts = async (): Promise<{ data: Receipt[] }> => {
  const response = await request({
    url: '/api/v1/receipts',
    method: 'GET'
  })
  return response as { data: Receipt[] }
}

// 特定のレシートを取得
export const getReceipt = async (id: string): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipts/${id}`,
    method: 'GET'
  })
  return response as { data: Receipt }
}

// レシートを承認
export const approveReceipt = async (id: string, comment?: string): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipt-approval/approve`,
    method: 'POST',
    body: { receipt_id: id, comment }
  })
  return response as { data: Receipt }
}

// レシートを却下
export const rejectReceipt = async (id: string, reason: string): Promise<{ data: Receipt }> => {
  const response = await request({
    url: `/api/v1/receipt-approval/reject`,
    method: 'POST',
    body: { receipt_id: id, reason }
  })
  return response as { data: Receipt }
}

// 重複チェックを取得
export const getDuplicateChecks = async (): Promise<{ data: DuplicateCheck[] }> => {
  const response = await request({
    url: '/api/v1/duplicate-check',
    method: 'GET'
  })
  return response as { data: DuplicateCheck[] }
}

// 重複チェックを承認
export const approveDuplicateCheck = async (id: string, comment?: string): Promise<{ data: DuplicateCheck }> => {
  const response = await request({
    url: `/api/v1/duplicate-check/${id}/review`,
    method: 'POST',
    body: { action: 'approve', comment }
  })
  return response as { data: DuplicateCheck }
}

// 重複チェックを却下
export const rejectDuplicateCheck = async (id: string, reason: string): Promise<{ data: DuplicateCheck }> => {
  const response = await request({
    url: `/api/v1/duplicate-check/${id}/review`,
    method: 'POST',
    body: { action: 'reject', reason }
  })
  return response as { data: DuplicateCheck }
}

// レシート画像を取得
export const getReceiptImage = async (id: string): Promise<Blob> => {
  const response = await request({
    url: `/api/v1/receipts/${id}/image`,
    method: 'GET',
    responseType: 'blob'
  })
  return response as Blob
}

// 承認済みファイル一覧を取得
export const getApprovedFiles = async (): Promise<{ data: ApprovedFileInfo[] }> => {
  const response = await request({
    url: '/api/v1/approved-files',
    method: 'GET'
  })
  return response as { data: ApprovedFileInfo[] }
}