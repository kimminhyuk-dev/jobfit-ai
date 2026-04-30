import { apiClient } from './client';
import type { AdminStats, JobPostingListResponse } from './types';
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
};
