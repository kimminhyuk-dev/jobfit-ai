// 로그인 화면 환경설정(아이디 저장 · 자동 로그인) — 클라이언트 localStorage 헬퍼.
// 자동 로그인 플래그는 authStore의 세션 복원 여부를 결정한다.

const SAVED_ID_KEY = 'jobfit:saved-id'; // 포털(user/company)별 접미사를 붙여 사용
const AUTO_LOGIN_KEY = 'jobfit:auto-login';

function safeStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function readSavedId(portal: string): string {
  return safeStorage()?.getItem(`${SAVED_ID_KEY}:${portal}`) ?? '';
}

export function hasSavedId(portal: string): boolean {
  return readSavedId(portal) !== '';
}

export function writeSavedId(portal: string, value: string | null): void {
  const storage = safeStorage();
  if (!storage) return;
  const key = `${SAVED_ID_KEY}:${portal}`;
  if (value) storage.setItem(key, value);
  else storage.removeItem(key);
}

// 사용자가 명시적으로 켠 경우에만 쿠키 기반 세션 복원을 허용한다.
export function readAutoLogin(): boolean {
  return safeStorage()?.getItem(AUTO_LOGIN_KEY) === '1';
}

export function writeAutoLogin(enabled: boolean): void {
  safeStorage()?.setItem(AUTO_LOGIN_KEY, enabled ? '1' : '0');
}
