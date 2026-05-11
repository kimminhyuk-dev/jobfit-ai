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

export interface AuthResponse {
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
export interface ResumeProjectData {
  name?: string | null;
  period?: string | null;
  role?: string | null;
  description?: string | null;
  review?: string | null;
  tech_stack?: string[];
  raw_text?: string | null;
}

export interface ResumeProjectResponse extends ResumeProjectData {
  project_id: number;
  resume_id: number;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface ResumeCoverLetterSectionResponse {
  section_id: number;
  resume_id: number;
  order_index: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeParsedData {
  profile?: {
    name?: string | null;
    birth_date?: string | null;
    email?: string | null;
    phone?: string | null;
    urls?: string[];
    address?: string | null;
  };
  emails: string[];
  phones: string[];
  urls: string[];
  skills: string[];
  sections?: Record<string, string>;
  schools?: Record<string, unknown>[];
  education?: string[];
  training?: string[];
  experiences?: string[];
  // projects는 구조화 객체 또는 구버전 문자열 배열 모두 허용
  projects?: (ResumeProjectData | string)[];
  certifications?: string[];
  cover_letter?: string | null;
  cover_letter_sections?: Record<string, string>;
  awards?: string[];
  languages?: string[];
  highlights?: Record<string, string[]>;
  text_length: number;
  parsed_by?: string | null;
}

export interface Resume {
  resume_id: number;
  user_id: number;
  title: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  parse_status: 'PENDING' | 'COMPLETED' | 'FAILED';
  parse_error: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  raw_text?: string | null;
  parsed_data?: ResumeParsedData | null;
  // 구조화 서브테이블 (관리자 상세 조회 시 포함)
  structured_projects?: ResumeProjectResponse[];
  structured_cover_letter_sections?: ResumeCoverLetterSectionResponse[];
}

export interface ResumeUpdatePayload {
  title?: string;
  raw_text?: string | null;
  parsed_data?: ResumeParsedData | null;
  structured_projects?: ResumeProjectData[] | null;
  structured_cover_letter_sections?: { title: string; content: string }[] | null;
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

// 카테고리
export interface Category {
  category_id: number;
  name: string;
  slug: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  slug: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface CategoryUpdate {
  name?: string;
  slug?: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

// 게시글
export interface Post {
  post_id: number;
  author_id: number;
  category_id: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface PostCreate {
  category_id: number;
  title: string;
  content: string;
}

export interface PostUpdate {
  category_id?: number;
  title?: string;
  content?: string;
}

// 관리자 대시보드 통계
export interface AdminStats {
  total_users: number;
  active_categories: number;
  total_posts: number;
  today_signups: number;
  total_jobs: number;
}

// 사용자 대시보드 통계
export interface DashboardStats {
  resumeScore: number;
  matchedJobs: number;
  applied: number;
  interviews: number;
  weeklyDelta: string;
}
