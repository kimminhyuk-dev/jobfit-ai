import { apiClient } from './client';
import type { AuthTokenResponse, LoginRequest, SignupRequest, User } from './types';

export const authApi = {
  login: async (body: LoginRequest): Promise<AuthTokenResponse> => {
    const res = await apiClient.post<AuthTokenResponse>('/auth/login', body);
    return res.data;
  },

  signup: async (body: SignupRequest): Promise<AuthTokenResponse> => {
    const res = await apiClient.post<AuthTokenResponse>('/auth/signup', body);
    return res.data;
  },

  refresh: async (): Promise<AuthTokenResponse> => {
    const res = await apiClient.post<AuthTokenResponse>('/auth/refresh');
    return res.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
};
