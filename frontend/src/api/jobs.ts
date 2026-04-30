import { apiClient } from './client';
import type { JobPostingListResponse } from './types';

export interface GetJobsParams {
  source?: string;
  keyword?: string;
  location_code?: string;
  employment_type_code?: string;
  education_code?: string;
  career_level_code?: string;
  status?: string;
  page?: number;
  size?: number;
}

export const jobsApi = {
  getJobs: async (params: GetJobsParams = {}): Promise<JobPostingListResponse> => {
    const res = await apiClient.get<JobPostingListResponse>('/jobs', { params });
    return res.data;
  },
};
