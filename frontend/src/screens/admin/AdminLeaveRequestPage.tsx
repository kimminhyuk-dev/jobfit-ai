'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { leaveApi, type LeaveRequestCreate } from '../../api/leave';
import type { ApiError } from '../../api/types';
import { useAuth } from '../../stores/authContext';
import LeaveRequestForm from '../../components/admin/LeaveRequestForm';
import { LeaveTabs, previewApprovalSteps } from '../../components/admin/leaveShared';

export default function AdminLeaveRequestPage() {
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [year, setYear] = useState<number>(new Date().getFullYear());
    const [done, setDone] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const { data: balance } = useQuery({
        queryKey: ['leave', 'balance', year],
        queryFn: () => leaveApi.getBalance(year),
    });

    const createMutation = useMutation({
        mutationFn: (payload: LeaveRequestCreate) => leaveApi.create(payload),
        onSuccess: (req) => {
            setError(null);
            setDone(
                `${req.requested_days}일 휴가 신청이 접수되었습니다.${
                    req.approver_name ? ` 결재자: ${req.approver_name}` : ''
                }`,
            );
            queryClient.invalidateQueries({ queryKey: ['leave', 'balance'] });
            queryClient.invalidateQueries({ queryKey: ['leave', 'mine'] });
        },
        onError: (err: ApiError) => {
            setDone(null);
            setError(err.message || '휴가 신청에 실패했습니다.');
        },
    });

    return (
        <div className="mx-auto max-w-5xl p-6">
            <div className="mb-5">
                <h1 className="text-[22px] font-bold text-m-text">휴가 신청</h1>
                <p className="mt-1 text-[13px] text-m-muted">휴가 종류와 기간을 선택하면 결재선에 따라 결재가 요청됩니다.</p>
            </div>

            <LeaveTabs />

            {done && (
                <div className="mb-4 rounded-lg border border-m-success/20 bg-m-success-soft px-3 py-2 text-[13px] text-m-success">
                    {done}
                </div>
            )}

            <LeaveRequestForm
                balance={balance}
                approvalSteps={previewApprovalSteps(user)}
                submitting={createMutation.isPending}
                submitLabel="휴가 신청"
                error={error}
                onSubmit={(payload) => {
                    setDone(null);
                    createMutation.mutate(payload);
                }}
                onYearChange={setYear}
            />
        </div>
    );
}
