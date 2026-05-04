import axios, { AxiosError } from 'axios';
import type { ApiError } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // HttpOnly cookie (refresh_token) 포함
  headers: { 'Content-Type': 'application/json' },
});

// Access Token 주입
apiClient.interceptors.request.use((config) => {
  if (typeof window === 'undefined') return config;

  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 에러 응답 정규화 → { code, message, details }
apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError<ApiError>) => {
    const apiErr: ApiError = error.response?.data ?? {
      code: 'NETWORK_ERROR',
      message: '서버에 연결할 수 없습니다.',
    };
    return Promise.reject(apiErr);
  },
);

export type { ApiError };
