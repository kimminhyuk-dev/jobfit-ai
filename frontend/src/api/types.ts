// 공통 API 에러 타입 — 백엔드 { code, message, details } 기준
export interface ApiError {
  code: string;
  message: string;
  details?: ApiValidationDetail[];
}

export interface ApiValidationDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data: T;
}

// 인증
export interface User {
  user_id: number;
  email: string;
  name: string;
  status: 'ACTIVE' | 'INACTIVE';
  role: 'USER' | 'ADMIN';
  created_at: string;
  updated_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
}

// 이력서
export interface Resume {
  id: string;
  filename: string;
  uploaded_at: string;
  score: number;
  status: 'analyzing' | 'done' | 'error';
}

// 채용공고
export interface Job {
  id: string;
  company: string;
  logo: string;
  logoColor: string;
  title: string;
  location: string;
  type: string;
  salary: string;
  score: number;
  matchedSkills: string[];
  missingSkills: string[];
  posted: string;
  applicants: number;
}

// 스킬
export interface Skill {
  name: string;
  user: number;
  market: number;
  status: 'strong' | 'gap' | 'weak';
}

// LLM 분석
export interface AnalysisItem {
  title: string;
  detail: string;
  impact?: string;
}

export interface Analysis {
  strengths: AnalysisItem[];
  weaknesses: AnalysisItem[];
  recommendations: AnalysisItem[];
}

// 지원 현황
export interface Application {
  company: string;
  stage: string;
  date: string;
  color: string;
}

// 대시보드 통계
export interface DashboardStats {
  resumeScore: number;
  matchedJobs: number;
  applied: number;
  interviews: number;
  weeklyDelta: string;
}
