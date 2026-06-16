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
export type Gender = 'MALE' | 'FEMALE';

export interface User {
  user_id: number;
  email: string;
  name: string;
  status: 'ACTIVE' | 'INACTIVE';
  role: 'USER' | 'COMPANY' | 'ADMIN';
  admin_level: 'A' | 'B' | 'C' | null;
  birth_date: string | null;
  phone: string | null;
  gender: Gender | null;
  zipcode: string | null;
  address1: string | null;
  address2: string | null;
  tech_stack: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface AdminCompanySummary {
  company_id: number;
  user_id: number;
  company_name: string | null;
  business_number: string | null;
  representative_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUser extends User {
  company: AdminCompanySummary | null;
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

export type InterviewQuestionType =
  | 'PROJECT'
  | 'TECH_STACK'
  | 'EXPERIENCE'
  | 'COVER_LETTER'
  | 'JOB_FIT';

export type InterviewQuestionSource =
  | 'parsed_data'
  | 'project'
  | 'cover_letter'
  | 'tech_stack'
  | 'experience';

export type InterviewVerdict = 'GOOD' | 'PARTIAL' | 'INSUFFICIENT' | 'UNKNOWN';
export type InterviewSessionStatus = 'IN_PROGRESS' | 'COMPLETED';

export interface InterviewReference {
  title: string;
  url: string;
  summary?: string | null;
}

export interface InterviewReferenceUsed {
  title: string;
  url: string;
}

export interface InterviewAnswerResponse {
  answer_id: number;
  question_id: number;
  user_answer: string;
  score: number;
  max_score: number;
  verdict: InterviewVerdict;
  strengths: string[];
  missing_points: string[];
  incorrect_points: string[];
  correct_points: string[];
  different_points: string[];
  feedback: string;
  reference_based_answer: string;
  official_references_used: InterviewReferenceUsed[];
  model: string;
}

export interface InterviewQuestionResponse {
  question_id: number;
  display_order: number;
  question: string;
  question_type: InterviewQuestionType;
  source: InterviewQuestionSource;
  intent: string;
  difficulty: string;
  expected_keywords: string[];
  official_references: InterviewReference[];
  max_score: number;
  answer: InterviewAnswerResponse | null;
}

export interface InterviewSessionResponse {
  session_id: number;
  resume_id: number;
  status: InterviewSessionStatus;
  model: string;
  total_score: number | null;
  max_score: number;
  questions: InterviewQuestionResponse[];
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
  raw_content?: string | null;
  status: string;
  collected_at: string;
}

export interface JobPostingListResponse {
  items: JobPostingItem[];
  total: number;
  page: number;
  size: number;
}

export interface JobFilterOptions {
  regions: string[];
  educations: string[];
  employment_types: string[];
  job_categories: string[];
}

export interface AlioCollectResponse {
  job_code: string;
  status: string;
  collected_count: number;
  inserted_count: number;
  updated_count: number;
  skipped_count: number;
  failed_count: number;
  error_code: string | null;
  error_message: string | null;
  run_id: number;
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

// 지원 현황 (mock UI용)
export interface Application {
  company: string;
  stage: string;
  date: string;
  color: string;
}

// 지원(이력서 보내기) — 백엔드 응답
export type ApplicationStatus = 'SUBMITTED' | 'VIEWED' | 'ACCEPTED' | 'REJECTED';

export interface JobApplicationResponse {
  application_id: number;
  job_id: number;
  resume_id: number;
  company_id: number | null;
  status: ApplicationStatus;
  applied_at: string;
}

export interface MyApplication {
  application_id: number;
  job_id: number;
  job_title: string;
  company_name: string | null;
  source_url: string | null;
  resume_id: number;
  resume_title: string;
  status: ApplicationStatus;
  applied_at: string;
}

// 기업회원 대시보드
export interface CompanyApplicant {
  application_id: number;
  applicant_name: string | null;
  applicant_email: string;
  job_id: number;
  job_title: string;
  resume_id: number;
  resume_title: string;
  status: ApplicationStatus;
  applied_at: string;
}

export interface CompanyDashboard {
  company_id: number;
  company_name: string | null;
  business_number: string | null;
  received_count: number;
  pending_count: number;
  posting_count: number;
  applicants: CompanyApplicant[];
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
