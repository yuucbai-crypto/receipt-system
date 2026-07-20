import { apiClient } from '@/api/client';

// ダッシュボードデータの型定義
export interface DashboardData {
  current_month_total: number;
  yearly_total: number;
  category_totals: Record<string, number>;
  monthly_trend: MonthlyTrendItem[];
}

export interface MonthlyTrendItem {
  month: string;
  total: number;
}

/**
 * ダッシュボードデータを取得
 */
export const getDashboardData = async (): Promise<DashboardData> => {
  try {
    const response = await apiClient.get('/api/v1/dashboard');
    return response.data;
  } catch (error) {
    console.error('ダッシュボードデータ取得エラー:', error);
    throw error;
  }
};