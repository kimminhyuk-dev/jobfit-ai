import { apiClient } from './client';

// 백엔드 backend/app/schemas/admin_leave.py 의 응답/요청 필드와 1:1로 맞춘다.
export type LeaveType =
    | 'ANNUAL'
    | 'AM_HALF'
    | 'PM_HALF'
    | 'SICK'
    | 'FAMILY_EVENT'
    | 'OFFICIAL'
    | 'COMPENSATORY';

export type LeaveStatus =
    | 'PENDING'
    | 'APPROVED'
    | 'REJECTED'
    | 'CANCELED'
    | 'CANCEL_REQUESTED'
    | 'CHANGE_REQUESTED';

export interface LeaveBalance {
    leave_balance_id: number;
    user_id: number;
    year: number;
    granted_days: number;
    used_days: number;
    pending_days: number;
    remaining_days: number;
}

export interface LeaveRequest {
    leave_request_id: number;
    requester_id: number;
    requester_name: string | null;
    requester_email: string | null;
    approver_id: number | null;
    approver_name: string | null;
    approver_email: string | null;
    leave_balance_id: number | null;
    leave_type: LeaveType;
    start_date: string;
    end_date: string;
    start_half_day: string | null;
    end_half_day: string | null;
    requested_days: number;
    reason: string | null;
    status: LeaveStatus;
    approved_at: string | null;
    rejected_at: string | null;
    reject_reason: string | null;
    canceled_at: string | null;
    cancel_requested_at: string | null;
    change_requested_at: string | null;
    change_request_reason: string | null;
    created_at: string;
    updated_at: string;
}

export interface LeaveRequestCreate {
    leave_type: LeaveType;
    start_date: string;
    end_date: string;
    start_half_day?: string | null;
    end_half_day?: string | null;
    reason?: string | null;
}

// 백엔드는 Numeric(Decimal) 필드를 JSON 문자열('15.00')로 직렬화한다.
// 경계에서 number로 정규화해 화면 계산/표시가 항상 숫자를 받도록 한다.
function toNum(value: unknown): number {
    return typeof value === 'number' ? value : Number(value);
}

function normalizeBalance(raw: LeaveBalance): LeaveBalance {
    return {
        ...raw,
        granted_days: toNum(raw.granted_days),
        used_days: toNum(raw.used_days),
        pending_days: toNum(raw.pending_days),
        remaining_days: toNum(raw.remaining_days),
    };
}

function normalizeRequest(raw: LeaveRequest): LeaveRequest {
    return { ...raw, requested_days: toNum(raw.requested_days) };
}

export const leaveApi = {
    // 내 연도별 잔여일 (year 미지정 시 백엔드가 올해로 처리)
    getBalance: async (year?: number): Promise<LeaveBalance> => {
        const res = await apiClient.get<LeaveBalance>('/admin/leave/balance', {
            params: year ? { year } : undefined,
        });
        return normalizeBalance(res.data);
    },

    // 휴가 신청 (LEAVE_REQUEST)
    create: async (payload: LeaveRequestCreate): Promise<LeaveRequest> => {
        const res = await apiClient.post<LeaveRequest>('/admin/leave', payload);
        return normalizeRequest(res.data);
    },

    // 내 신청 목록 (LEAVE_REQUEST)
    listMine: async (): Promise<LeaveRequest[]> => {
        const res = await apiClient.get<LeaveRequest[]>('/admin/leave/me');
        return res.data.map(normalizeRequest);
    },

    // 내가 결재할 목록: PENDING + CANCEL_REQUESTED (LEAVE_APPROVE)
    listPending: async (): Promise<LeaveRequest[]> => {
        const res = await apiClient.get<LeaveRequest[]>('/admin/leave/pending');
        return res.data.map(normalizeRequest);
    },

    // 승인 (LEAVE_APPROVE)
    approve: async (id: number): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/approve`);
        return normalizeRequest(res.data);
    },

    // 반려 (LEAVE_APPROVE)
    reject: async (id: number, rejectReason: string): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/reject`, {
            reject_reason: rejectReason,
        });
        return normalizeRequest(res.data);
    },

    // 일정 변경 요청 (LEAVE_APPROVE)
    requestChange: async (id: number, changeReason: string): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/request-change`, {
            change_reason: changeReason,
        });
        return normalizeRequest(res.data);
    },

    // 취소 / 승인 후 취소 요청 (LEAVE_REQUEST)
    cancel: async (id: number): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/cancel`);
        return normalizeRequest(res.data);
    },

    // 승인 후 취소 요청 결재 (LEAVE_APPROVE)
    approveCancel: async (id: number): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/cancel-approve`);
        return normalizeRequest(res.data);
    },

    // 승인 후 취소 요청 반려 (LEAVE_APPROVE)
    rejectCancel: async (id: number): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/cancel-reject`);
        return normalizeRequest(res.data);
    },

    // 일정 변경 요청 반영 후 재신청 (LEAVE_REQUEST)
    resubmit: async (id: number, payload: LeaveRequestCreate): Promise<LeaveRequest> => {
        const res = await apiClient.patch<LeaveRequest>(`/admin/leave/${id}/resubmit`, payload);
        return normalizeRequest(res.data);
    },
};
