import { apiClient } from './client';
import type { AuthResponse, User } from './types';

export interface UserUpdateRequest {
  name?: string;
  current_password?: string;
  new_password?: string;
}

export const authApi = {
  login: async (body: { email: string; password: string }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/login', body);
    return res.data;
  },

  signup: async (body: { email: string; password: string; name: string }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/signup', body);
    return res.data;
  },

  refresh: async (): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/refresh');
    return res.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  updateMe: async (body: UserUpdateRequest): Promise<User> => {
    const res = await apiClient.patch<User>('/auth/me', body);
    return res.data;
  },

  deleteMe: async (): Promise<void> => {
    await apiClient.delete('/auth/me');
  },
};
