import { apiClient } from './client';

export interface AdminMenu {
    id: number;
    parent_id: number | null;
    menu_name: string;
    menu_url: string | null;
    icon: string | null;
    sort_order: number;
    use_yn: boolean;
    required_permission: string | null;
    created_at: string;
    updated_at: string;
    reg_user_id?: number | null;
    reg_ip?: string | null;
    reg_dt?: string | null;
    mod_user_id?: number | null;
    mod_ip?: string | null;
    mod_dt?: string | null;
}

export interface AdminMenuTree extends AdminMenu {
    children: AdminMenuTree[];
}

export interface AdminMenuPayload {
    parent_id?: number | null;
    menu_name: string;
    menu_url?: string | null;
    icon?: string | null;
    sort_order: number;
    use_yn: boolean;
    required_permission?: string | null;
}

export const adminMenuApi = {
    tree: async (): Promise<AdminMenuTree[]> => {
        const res = await apiClient.get<AdminMenuTree[]>('/admin/menus/tree');
        return res.data;
    },
    list: async (): Promise<AdminMenu[]> => {
        const res = await apiClient.get<AdminMenu[]>('/admin/menus');
        return res.data;
    },
    create: async (payload: AdminMenuPayload): Promise<AdminMenu> => {
        const res = await apiClient.post<AdminMenu>('/admin/menus', payload);
        return res.data;
    },
    update: async (menuId: number, payload: AdminMenuPayload): Promise<AdminMenu> => {
        const res = await apiClient.patch<AdminMenu>(`/admin/menus/${menuId}`, payload);
        return res.data;
    },
    delete: async (menuId: number): Promise<void> => {
        await apiClient.delete(`/admin/menus/${menuId}`);
    },
};
