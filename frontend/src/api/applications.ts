import { apiClient } from './client';
import type { JobApplicationResponse, MyApplication } from './types';

export const applicationsApi = {
  apply: async (params: {
    job_id: number;
    resume_id: number;
  }): Promise<JobApplicationResponse> => {
    const res = await apiClient.post<JobApplicationResponse>('/applications', params);
    return res.data;
  },

  getMyApplications: async (): Promise<MyApplication[]> => {
    const res = await apiClient.get<MyApplication[]>('/applications/me');
    return res.data;
  },

  cancel: async (applicationId: number): Promise<void> => {
    await apiClient.delete(`/applications/${applicationId}`);
  },
};
