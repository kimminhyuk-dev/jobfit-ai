import { apiClient } from './client';
import type { JobFilterOptions, JobPostingItem, JobPostingListResponse } from './types';

export interface GetJobsParams {
  source?: string;
  keyword?: string;
  region?: string;
  education?: string;
  employment_type?: string;
  ncs_category?: string;
  location_code?: string;
  employment_type_code?: string;
  education_code?: string;
  career_level_code?: string;
  status?: string;
  data_source?: string;
  page?: number;
  size?: number;
}

export const jobsApi = {
  getJobs: async (params: GetJobsParams = {}): Promise<JobPostingListResponse> => {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== undefined && v !== null),
    );
    const res = await apiClient.get<JobPostingListResponse>('/jobs', { params: clean });
    return res.data;
  },

  getJob: async (jobId: number): Promise<JobPostingItem> => {
    const res = await apiClient.get<JobPostingItem>(`/jobs/${jobId}`);
    return res.data;
  },

  getFilterOptions: async (): Promise<JobFilterOptions> => {
    const res = await apiClient.get<JobFilterOptions>('/jobs/filter-options');
    return res.data;
  },
};
