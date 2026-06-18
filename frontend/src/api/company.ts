import { apiClient } from './client';
import type {
  ApplicationStatus,
  CompanyApplicationStatusResponse,
  CompanyApplicantResume,
  CompanyDashboard,
  CompanyJob,
  CompanyJobPayload,
  InterviewEmailPayload,
  InterviewEmailResponse,
} from './types';

export const companyApi = {
  getDashboard: async (): Promise<CompanyDashboard> => {
    const res = await apiClient.get<CompanyDashboard>('/company/dashboard');
    return res.data;
  },

  // 지원자 이력서 열람 (첫 열람 시 백엔드에서 상태가 VIEWED로 전환됨)
  viewApplicantResume: async (applicationId: number): Promise<CompanyApplicantResume> => {
    const res = await apiClient.get<CompanyApplicantResume>(
      `/company/applications/${applicationId}/resume`,
    );
    return res.data;
  },

  getApplicantResumeFileBlob: async (
    applicationId: number,
    download = false,
  ): Promise<Blob> => {
    const res = await apiClient.get(
      `/company/applications/${applicationId}/resume/file`,
      {
        params: download ? { download: true } : undefined,
        responseType: 'blob',
      },
    );
    return res.data;
  },

  updateApplicationStatus: async (
    applicationId: number,
    status: Extract<ApplicationStatus, 'REJECTED'>,
  ): Promise<CompanyApplicationStatusResponse> => {
    const res = await apiClient.patch<CompanyApplicationStatusResponse>(
      `/company/applications/${applicationId}/status`,
      { status },
    );
    return res.data;
  },

  sendInterviewEmail: async (
    applicationId: number,
    payload: InterviewEmailPayload,
  ): Promise<InterviewEmailResponse> => {
    const res = await apiClient.post<InterviewEmailResponse>(
      `/company/applications/${applicationId}/interview-email`,
      payload,
    );
    return res.data;
  },

  // 기업 공고 관리
  listJobs: async (): Promise<CompanyJob[]> => {
    const res = await apiClient.get<CompanyJob[]>('/company/jobs');
    return res.data;
  },

  getJob: async (jobId: number): Promise<CompanyJob> => {
    const res = await apiClient.get<CompanyJob>(`/company/jobs/${jobId}`);
    return res.data;
  },

  createJob: async (payload: CompanyJobPayload): Promise<CompanyJob> => {
    const res = await apiClient.post<CompanyJob>('/company/jobs', payload);
    return res.data;
  },

  updateJob: async (jobId: number, payload: Partial<CompanyJobPayload>): Promise<CompanyJob> => {
    const res = await apiClient.patch<CompanyJob>(`/company/jobs/${jobId}`, payload);
    return res.data;
  },

  deleteJob: async (jobId: number): Promise<void> => {
    await apiClient.delete(`/company/jobs/${jobId}`);
  },
};
