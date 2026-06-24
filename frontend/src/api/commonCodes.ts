import { apiClient } from './client';

export interface CommonCodeGroup {
    id: number;
    group_code: string;
    group_name: string;
    description: string | null;
    sort_order: number;
    use_yn: boolean;
    category_code: string;
    created_at: string;
    updated_at: string;
    reg_user_id?: number | null;
    reg_ip?: string | null;
    reg_dt?: string | null;
    mod_user_id?: number | null;
    mod_ip?: string | null;
    mod_dt?: string | null;
}

export interface CommonCodeItem {
    id: number;
    group_code: string;
    code: string;
    code_name: string;
    sort_order: number;
    use_yn: boolean;
    attr1: string | null;
    attr2: string | null;
    created_at: string;
    updated_at: string;
    reg_user_id?: number | null;
    reg_ip?: string | null;
    reg_dt?: string | null;
    mod_user_id?: number | null;
    mod_ip?: string | null;
    mod_dt?: string | null;
}

export interface CommonCodeGroupPayload {
    group_code?: string;
    group_name: string;
    description?: string | null;
    sort_order: number;
    use_yn: boolean;
    category_code?: string;
}

export interface CommonCodeItemPayload {
    code?: string;
    code_name: string;
    sort_order: number;
    use_yn: boolean;
    attr1?: string | null;
    attr2?: string | null;
}

export const commonCodeApi = {
    listGroups: async (): Promise<CommonCodeGroup[]> => {
        const res = await apiClient.get<CommonCodeGroup[]>('/admin/common-codes/groups');
        return res.data;
    },
    createGroup: async (payload: CommonCodeGroupPayload): Promise<CommonCodeGroup> => {
        const res = await apiClient.post<CommonCodeGroup>('/admin/common-codes/groups', payload);
        return res.data;
    },
    updateGroup: async (groupCode: string, payload: CommonCodeGroupPayload): Promise<CommonCodeGroup> => {
        const res = await apiClient.patch<CommonCodeGroup>(`/admin/common-codes/groups/${groupCode}`, payload);
        return res.data;
    },
    deleteGroup: async (groupCode: string): Promise<void> => {
        await apiClient.delete(`/admin/common-codes/groups/${groupCode}`);
    },
    listItems: async (groupCode: string): Promise<CommonCodeItem[]> => {
        const res = await apiClient.get<CommonCodeItem[]>(`/admin/common-codes/${groupCode}/items`);
        return res.data;
    },
    createItem: async (groupCode: string, payload: CommonCodeItemPayload): Promise<CommonCodeItem> => {
        const res = await apiClient.post<CommonCodeItem>(`/admin/common-codes/${groupCode}/items`, payload);
        return res.data;
    },
    updateItem: async (
        groupCode: string,
        code: string,
        payload: CommonCodeItemPayload,
    ): Promise<CommonCodeItem> => {
        const res = await apiClient.patch<CommonCodeItem>(`/admin/common-codes/${groupCode}/items/${code}`, payload);
        return res.data;
    },
    deleteItem: async (groupCode: string, code: string): Promise<void> => {
        await apiClient.delete(`/admin/common-codes/${groupCode}/items/${code}`);
    },
};
