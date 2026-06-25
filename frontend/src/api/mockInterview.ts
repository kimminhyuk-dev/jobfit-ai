import { apiClient } from './client';
import type {
  MockInterviewAnswerResponse,
  MockInterviewFinishResponse,
  MockInterviewSession,
  MockInterviewStartResponse,
} from './types';

export const mockInterviewApi = {
  start: async (params: {
    resume_id: number;
    job_id?: number | null;
  }): Promise<MockInterviewStartResponse> => {
    const res = await apiClient.post<MockInterviewStartResponse>(
      '/mock-interview/start',
      params.job_id ? params : { resume_id: params.resume_id },
    );
    return res.data;
  },

  answer: async ({
    sessionId,
    answer,
  }: {
    sessionId: number;
    answer: string;
  }): Promise<MockInterviewAnswerResponse> => {
    const res = await apiClient.post<MockInterviewAnswerResponse>(
      `/mock-interview/${sessionId}/answer`,
      { answer },
    );
    return res.data;
  },

  finish: async (sessionId: number): Promise<MockInterviewFinishResponse> => {
    const res = await apiClient.post<MockInterviewFinishResponse>(
      `/mock-interview/${sessionId}/finish`,
    );
    return res.data;
  },

  get: async (sessionId: number): Promise<MockInterviewSession> => {
    const res = await apiClient.get<MockInterviewSession>(
      `/mock-interview/${sessionId}`,
    );
    return res.data;
  },
};
