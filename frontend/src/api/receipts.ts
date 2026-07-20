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