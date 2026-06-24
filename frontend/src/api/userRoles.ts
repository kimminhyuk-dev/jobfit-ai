import { apiClient } from './client';

export interface RolePermissionItem {
    code: string;
    name: string;
}

export interface AssignableRole {
    code: string;
    name: string;
    description: string | null;
    permissions: RolePermissionItem[];
}

export interface UserRolesResponse {
    user_id: number;
    name: string;
    email: string;
    assigned_role_codes: string[];
    super_admin_count: number;
    available_roles: AssignableRole[];
}

export const userRoleApi = {
    get: async (userId: number): Promise<UserRolesResponse> => {
        const res = await apiClient.get<UserRolesResponse>(`/admin/users/${userId}/roles`);
        return res.data;
    },

    assign: async (userId: number, roleCode: string): Promise<UserRolesResponse> => {
        const res = await apiClient.post<UserRolesResponse>(`/admin/users/${userId}/roles`, {
            role_code: roleCode,
        });
        return res.data;
    },

    revoke: async (userId: number, roleCode: string): Promise<UserRolesResponse> => {
        const res = await apiClient.delete<UserRolesResponse>(
            `/admin/users/${userId}/roles/${roleCode}`,
        );
        return res.data;
    },
};
