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
} from './types';
import type { GetJobsParams } from './jobs';

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const res = await apiClient.get<AdminStats>('/admin/stats');
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
