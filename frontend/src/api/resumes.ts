import { apiClient } from './client';
import type { InterviewAnswerResponse, InterviewSessionResponse, Resume } from './types';

export interface UploadResumeParams {
  file: File;
  title?: string;
  isDefault?: boolean;
}

export const resumesApi = {
  getResumes: async (): Promise<Resume[]> => {
    const res = await apiClient.get<Resume[]>('/resumes');
    return res.data;
  },

  getResume: async (resumeId: number): Promise<Resume> => {
    const res = await apiClient.get<Resume>(`/resumes/${resumeId}`);
    return res.data;
  },

  uploadResume: async ({ file, title, isDefault }: UploadResumeParams): Promise<Resume> => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    formData.append('is_default', String(Boolean(isDefault)));

    const res = await apiClient.post<Resume>('/resumes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  deleteResume: async (resumeId: number): Promise<void> => {
    await apiClient.delete(`/resumes/${resumeId}`);
  },

  createInterviewSession: async (
    resumeId: number,
  ): Promise<InterviewSessionResponse> => {
    const res = await apiClient.post<InterviewSessionResponse>(
      `/resumes/${resumeId}/interview-sessions`,
    );
    return res.data;
  },

  getInterviewSession: async (
    resumeId: number,
    sessionId: number,
  ): Promise<InterviewSessionResponse> => {
    const res = await apiClient.get<InterviewSessionResponse>(
      `/resumes/${resumeId}/interview-sessions/${sessionId}`,
    );
    return res.data;
  },

  submitInterviewAnswer: async ({
    resumeId,
    questionId,
    answer,
  }: {
    resumeId: number;
    questionId: number;
    answer: string;
  }): Promise<InterviewAnswerResponse> => {
    const res = await apiClient.post<InterviewAnswerResponse>(
      `/resumes/${resumeId}/interview-questions/${questionId}/answer`,
      { answer },
    );
    return res.data;
  },

  getResumeFileUrl: (resumeId: number): string => {
    return `${apiClient.defaults.baseURL}/resumes/${resumeId}/file`;
  },

  getResumeFileBlob: async (resumeId: number): Promise<Blob> => {
    const res = await apiClient.get(`/resumes/${resumeId}/file`, {
      responseType: 'blob',
    });
    return res.data;
  },
};
