import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Access Token + Refresh Token 쿠키 자동 포함
  headers: { 'Content-Type': 'application/json' },
});

// ── 401 자동 Refresh 인터셉터 ─────────────────────────────────────────────
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

function getLoginPortal(error: AxiosError<ApiError>): string | null {
  const data = error.config?.data;
  if (!data) return null;
  if (typeof data === 'object' && 'portal' in data) {
    return String(data.portal);
  }
  if (typeof data !== 'string') return null;

  try {
    const parsed = JSON.parse(data) as { portal?: unknown };
    return typeof parsed.portal === 'string' ? parsed.portal : null;
  } catch {
    return null;
  }
}

function getUserMessage(error: AxiosError<ApiError>, fallback: ApiError): string {
  const status = error.response?.status;
  const code = fallback.code;
  const url = error.config?.url ?? '';

  if (url.includes('/auth/login')) {
    return getLoginPortal(error) === 'company'
      ? '사업자등록번호 또는 이메일을 확인해주세요.'
      : '아이디 또는 비밀번호를 확인해주세요.';
  }
  if (!error.response || status === undefined || status >= 500) {
    return '요청을 처리하지 못했습니다. 잠시 후 다시 시도해주세요.';
  }
  if (code === 'RESUME_003') {
    return '등록 가능한 파일 형식 및 확장자 : PDF,PNG,JPG,JPEG,GIF';
  }
  if (status === 401) return '로그인이 필요합니다.';
  if (status === 403) return '접근 권한이 없습니다.';
  if (status === 404) return '요청한 정보를 찾을 수 없습니다.';
  if (status === 409 && fallback.message) return fallback.message;
  if (status === 413 || code === 'RESUME_002') {
    return '파일은 최대 10MB까지 업로드할 수 있습니다.';
  }
  if (status === 422) return '입력한 내용을 다시 확인해주세요.';
  return fallback.message || '요청을 처리하지 못했습니다.';
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiError>) => {
    const cfg = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    const is401 = error.response?.status === 401;
    const isRefreshEndpoint = cfg?.url?.includes('/auth/refresh');
    const isLoginEndpoint = cfg?.url?.includes('/auth/login');
    const isMeEndpoint = cfg?.url?.includes('/auth/me');

    if (is401 && cfg && !cfg._retry && !isRefreshEndpoint && !isLoginEndpoint && !isMeEndpoint) {
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
      message: '요청을 처리하지 못했습니다. 잠시 후 다시 시도해주세요.',
    };
    return Promise.reject({
      ...apiErr,
      message: getUserMessage(error, apiErr),
    });
  },
);

export type { ApiError };
