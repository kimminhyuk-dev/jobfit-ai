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

// 채용공고 (mock UI용)
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

// 채용공고 (백엔드 GET /jobs 응답)
export interface JobPostingItem {
  job_id: number;
  source: string;
  source_job_id: string | null;
  source_url: string | null;
  company_name: string | null;
  title: string;
  location: string | null;
  location_code: string | null;
  career_level: string | null;
  career_level_code: string | null;
  education: string | null;
  education_code: string | null;
  employment_type: string | null;
  employment_type_code: string | null;
  ncs_category: string | null;
  ncs_category_code: string | null;
  organization_type: string | null;
  organization_type_code: string | null;
  organization_category: string | null;
  organization_category_code: string | null;
  ministry: string | null;
  ministry_code: string | null;
  posted_at: string | null;
  deadline: string | null;
  status: string;
  collected_at: string;
}

export interface JobPostingListResponse {
  items: JobPostingItem[];
  total: number;
  page: number;
  size: number;
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
