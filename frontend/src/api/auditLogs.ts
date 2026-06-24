import { apiClient } from './client';

export type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE';

export interface AuditLog {
    id: number;
    table_name: string;
    record_id: string;
    action: AuditAction;
    actor_user_id: number | null;
    actor_ip: string | null;
    before_data: Record<string, unknown> | null;
    after_data: Record<string, unknown> | null;
    summary: string | null;
    created_at: string;
}

export interface AuditLogListResponse {
    items: AuditLog[];
    total: number;
    page: number;
    page_size: number;
}

export interface AuditLogListParams {
    table_name?: string;
    actor?: number;
    action?: AuditAction;
    start_at?: string;
    end_at?: string;
    page?: number;
    page_size?: number;
}

export const auditLogApi = {
    list: async (params: AuditLogListParams): Promise<AuditLogListResponse> => {
        const res = await apiClient.get<AuditLogListResponse>('/admin/audit-logs', { params });
        return res.data;
    },
};
