import { apiClient } from './client';
import type { AuthResponse, Gender, User } from './types';

export interface ProfileFields {
  birth_date?: string | null;
  phone?: string | null;
  gender?: Gender | null;
  zipcode?: string | null;
  address1?: string | null;
  address2?: string | null;
  tech_stack?: string[] | null;
}

export interface UserUpdateRequest extends ProfileFields {
  name?: string;
  current_password?: string;
  new_password?: string;
}

export interface SignupRequest extends ProfileFields {
  email: string;
  password: string;
  name: string;
}

export interface MessageResponse {
  message: string;
}

export interface FindEmailResponse extends MessageResponse {
  masked_email?: string | null;
}

export const authApi = {
  login: async (body: {
    email: string;
    password: string;
    portal?: 'user' | 'company';
  }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/login', body);
    return res.data;
  },

  signup: async (body: SignupRequest): Promise<AuthResponse> => {
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

  findEmail: async (body: { name: string; phone: string }): Promise<FindEmailResponse> => {
    const res = await apiClient.post<FindEmailResponse>('/auth/find-email', body);
    return res.data;
  },

  findCompanyEmail: async (body: {
    name: string;
    business_number: string;
  }): Promise<FindEmailResponse> => {
    const res = await apiClient.post<FindEmailResponse>('/auth/company/find-email', body);
    return res.data;
  },

  requestPasswordReset: async (body: { email: string }): Promise<MessageResponse> => {
    const res = await apiClient.post<MessageResponse>('/auth/password/reset-request', body);
    return res.data;
  },

  requestCompanyPasswordReset: async (body: {
    name: string;
    business_number: string;
    email: string;
  }): Promise<MessageResponse> => {
    const res = await apiClient.post<MessageResponse>('/auth/company/password/reset-request', body);
    return res.data;
  },

  confirmPasswordReset: async (body: { email: string; code: string }): Promise<MessageResponse> => {
    const res = await apiClient.post<MessageResponse>('/auth/password/reset-confirm', body);
    return res.data;
  },
};
