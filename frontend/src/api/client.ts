import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Access Token + Refresh Token 쿠키 자동 포함
  headers: { 'Content-Type': 'application/json' },
});

// ── 401 자동 Refresh 인터셉터 ────────────────────────────────────���─────────
// Access Token 쿠키가 만료되면 /auth/refresh를 호출해 조용히 갱신한다.
let isRefreshing = false;
let pendingQueue: Array<{
  resolve: () => void;
  reject: (err: unknown) => void;
}> = [];

function flushQueue(err: unknown) {
  pendingQueue.forEach((p) => (err ? p.reject(err) : p.resolve()));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiError>) => {
    const cfg = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    const is401 = error.response?.status === 401;
    const isRefreshEndpoint = cfg?.url?.includes('/auth/refresh');
    const isLoginEndpoint = cfg?.url?.includes('/auth/login');

    if (is401 && cfg && !cfg._retry && !isRefreshEndpoint && !isLoginEndpoint) {
      if (isRefreshing) {
        // 이미 갱신 중이면 대기열에 추가
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: () => resolve(apiClient(cfg)),
            reject,
          });
        });
      }

      cfg._retry = true;
      isRefreshing = true;

      try {
        await apiClient.post('/auth/refresh');
        isRefreshing = false;
        flushQueue(null);
        return apiClient(cfg); // 원래 요청 재시도
      } catch (refreshErr) {
        isRefreshing = false;
        flushQueue(refreshErr);
        // 세션 만료 이벤트 → authStore가 수신해 로그아웃 처리
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('auth:session-expired'));
        }
      }
    }

    const apiErr: ApiError = error.response?.data ?? {
      code: 'NETWORK_ERROR',
      message: '서버에 연결할 수 없습니다.',
    };
    return Promise.reject(apiErr);
  },
);

export type { ApiError };
