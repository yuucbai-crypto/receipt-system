import { apiClient } from '@/api/client';

// レシート一覧の型定義
export interface ReceiptListResponse {
  items: Receipt[];
  page: number;
  total_pages: number;
  total_items: number;
}

// レシートの型定義
export interface Receipt {
  id: number;
  date: string;
  amount: number;
  category: string;
  tags: string[];
  status: 'pending' | 'approved' | 'rejected';
  description: string;
  image_url: string;
  ocr_content: string;
  ai_comment: string;
}

// レシートフィルターの型定義
export interface ReceiptFilters {
  page?: number;
  limit?: number;
  searchTerm?: string;
  category?: string;
  tag?: string;
  startDate?: string;
  endDate?: string;
}

// 承認リクエストの型定義
export interface ReceiptApprovalRequest {
  approve: boolean;
  receipt_id: number;
}

// 却下リクエストの型定義
export interface ReceiptRejectRequest {
  receipt_id: number;
  rejection_reason?: {
    reason_code: string;
    reason_text: string;
  };
}

/**
 * レシート一覧を取得
 */
export const getReceipts = async (filters: ReceiptFilters): Promise<ReceiptListResponse> => {
  try {
    // フィルター条件をクエリパラメータに変換
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.searchTerm) params.append('search_term', filters.searchTerm);
    if (filters.category) params.append('category', filters.category);
    if (filters.tag) params.append('tag', filters.tag);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    
    const response = await apiClient.get(`/api/v1/receipts?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('レシート一覧取得エラー:', error);
    throw error;
  }
};

/**
 * レシートを承認
 */
export const approveReceipt = async (receiptId: number): Promise<void> => {
  try {
    await apiClient.post('/api/v1/receipt-approval/approve', {
      receipt_id: receiptId,
      approve: true
    });
  } catch (error) {
    console.error('レシート承認エラー:', error);
    throw error;
  }
};

/**
 * レシートを却下
 */
export const rejectReceipt = async (receiptId: number, rejectionReason?: { reason_code: string; reason_text: string }): Promise<void> => {
  try {
    await apiClient.post('/api/v1/receipt-approval/reject', {
      receipt_id: receiptId,
      approve: false,
      rejection_reason: rejectionReason
    });
  } catch (error) {
    console.error('レシート却下エラー:', error);
    throw error;
  }
};