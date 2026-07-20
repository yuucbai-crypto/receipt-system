import axios, { AxiosInstance } from 'axios';

// APIクライアントのインスタンスを作成
export const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// レスポンスの共通処理
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('APIエラー:', error);
    return Promise.reject(error);
  }
);