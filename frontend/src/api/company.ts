import { apiClient } from './client';
import type { CompanyDashboard } from './types';

export const companyApi = {
  getDashboard: async (): Promise<CompanyDashboard> => {
    const res = await apiClient.get<CompanyDashboard>('/company/dashboard');
    return res.data;
  },
};
