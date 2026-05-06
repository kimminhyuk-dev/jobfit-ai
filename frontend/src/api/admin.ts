import { apiClient } from './client';
import type {
  AdminStats,
  Category,
  CategoryCreate,
  CategoryUpdate,
  JobPostingListResponse,
  Post,
  PostCreate,
  PostUpdate,
  Resume,
  ResumeUpdatePayload,
  User,
} from './types';
import type { GetJobsParams } from './jobs';

export interface AdminUserDetail {
  user: User;
  resumes: Resume[];
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const res = await apiClient.get<AdminStats>('/admin/stats');
    return res.data;
  },

  // 회원 관리
  listUsers: async (params: { skip?: number; limit?: number } = {}): Promise<User[]> => {
    const res = await apiClient.get<User[]>('/admin/users', { params });
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

  // 카테고리
  listCategories: async (): Promise<Category[]> => {
    const res = await apiClient.get<Category[]>('/categories');
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

  // 게시글
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
