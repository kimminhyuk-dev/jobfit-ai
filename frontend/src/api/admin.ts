import { apiClient } from './client';
import type {
  AdminStats,
  AdminUser,
  AlioCollectResponse,
  Category,
  CategoryCreate,
  CategoryUpdate,
  JobPostingListResponse,
  Post,
  PostCreate,
  PostUpdate,
  Resume,
  ResumeUpdatePayload,
} from './types';
import type { GetJobsParams } from './jobs';

export interface AdminUserDetail {
  user: AdminUser;
  resumes: Resume[];
}

export interface AdminUserListParams {
  skip?: number;
  limit?: number;
  role?: 'USER' | 'COMPANY' | 'ADMIN';
  q?: string;
  admin_identifier?: string;
  admin_level?: 'A' | 'B' | 'C' | '';
  name?: string;
  birth_date?: string;
  company_name?: string;
  business_number?: string;
  representative_name?: string;
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const res = await apiClient.get<AdminStats>('/admin/stats');
    return res.data;
  },

  listUsers: async (params: AdminUserListParams = {}): Promise<AdminUser[]> => {
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== '' && value !== undefined),
    );
    const res = await apiClient.get<AdminUser[]>('/admin/users', { params: cleanParams });
    return res.data;
  },

  getUserDetail: async (userId: number): Promise<AdminUserDetail> => {
    const res = await apiClient.get<AdminUserDetail>(`/admin/users/${userId}`);
    return res.data;
  },

  getResumeDetail: async (resumeId: number): Promise<Resume> => {
    const res = await apiClient.get<Resume>(`/admin/users/resumes/${resumeId}`);
    return res.data;
  },

  updateResumeDetail: async (resumeId: number, data: ResumeUpdatePayload): Promise<Resume> => {
    const res = await apiClient.patch<Resume>(`/admin/users/resumes/${resumeId}`, data);
    return res.data;
  },

  getResumeFileUrl: (resumeId: number): string => {
    return `${apiClient.defaults.baseURL}/admin/users/resumes/${resumeId}/file`;
  },

  getResumeFileBlob: async (resumeId: number): Promise<Blob> => {
    const res = await apiClient.get(`/admin/users/resumes/${resumeId}/file`, {
      responseType: 'blob',
    });
    return res.data;
  },

  getJobs: async (params: GetJobsParams = {}): Promise<JobPostingListResponse> => {
    const res = await apiClient.get<JobPostingListResponse>('/jobs', { params });
    return res.data;
  },

  collectAlioJobs: async (data: {
    keyword?: string;
    start_page?: number;
    max_pages?: number;
    display?: number;
    idempotency_key?: string;
  } = {}): Promise<AlioCollectResponse> => {
    const res = await apiClient.post<AlioCollectResponse>('/admin/job-sources/alio/collect', data);
    return res.data;
  },

  listCategories: async (): Promise<Category[]> => {
    const res = await apiClient.get<Category[]>('/admin/categories');
    return res.data;
  },

  createCategory: async (data: CategoryCreate): Promise<Category> => {
    const res = await apiClient.post<Category>('/categories', data);
    return res.data;
  },

  updateCategory: async (id: number, data: CategoryUpdate): Promise<Category> => {
    const res = await apiClient.patch<Category>(`/categories/${id}`, data);
    return res.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`);
  },

  listPosts: async (params: { offset?: number; limit?: number; category_id?: number } = {}): Promise<Post[]> => {
    const res = await apiClient.get<Post[]>('/posts', { params });
    return res.data;
  },

  createPost: async (data: PostCreate): Promise<Post> => {
    const res = await apiClient.post<Post>('/posts', data);
    return res.data;
  },

  updatePost: async (id: number, data: PostUpdate): Promise<Post> => {
    const res = await apiClient.patch<Post>(`/posts/${id}`, data);
    return res.data;
  },

  deletePost: async (id: number): Promise<void> => {
    await apiClient.delete(`/posts/${id}`);
  },
};
