'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { leaveApi, type LeaveRequest, type LeaveRequestCreate } from '../../api/leave';
import type { ApiError } from '../../api/types';
import { useAuth } from '../../stores/authContext';
import Icon from '../../components/ui/Icon';
import LeaveRequestForm from '../../components/admin/LeaveRequestForm';
import {
    ApprovalStepper,
    BalanceSummary,
    LEAVE_TYPE_LABELS,
    LeaveTabs,
    StatusBadge,
    formatDate,
    formatDays,
    previewApprovalSteps,
    type ApprovalStep,
} from '../../components/admin/leaveShared';

function mySteps(req: LeaveRequest): ApprovalStep[] {
    const approverState: ApprovalStep['state'] = req.status === 'APPROVED' ? 'done' : 'current';
    return [
        {
            label: '신청',
            name: req.requester_name ?? '나',
            state: 'done',
        },
        {
            label: '결재',
            name: req.approver_name ?? '결재자',
            state: approverState,
        },
    ];
}

export default function AdminLeaveMyPage() {
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [year, setYear] = useState<number>(new Date().getFullYear());
    const [resubmitId, setResubmitId] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);

    const { data: requests = [], isLoading } = useQuery({
        queryKey: ['leave', 'mine'],
        queryFn: () => leaveApi.listMine(),
    });

    const { data: balance } = useQuery({
        queryKey: ['leave', 'balance', year],
        queryFn: () => leaveApi.getBalance(year),
    });

    const onError = (err: ApiError) => setError(err.message || '처리에 실패했습니다.');
    function afterMutate() {
        setError(null);
        setResubmitId(null);
        queryClient.invalidateQueries({ queryKey: ['leave', 'mine'] });
        queryClient.invalidateQueries({ queryKey: ['leave', 'balance'] });
    }

    const cancelMutation = useMutation({
        mutationFn: (id: number) => leaveApi.cancel(id),
        onSuccess: afterMutate,
        onError,
    });
    const resubmitMutation = useMutation({
        mutationFn: ({ id, payload }: { id: number; payload: LeaveRequestCreate }) => leaveApi.resubmit(id, payload),
        onSuccess: afterMutate,
        onError,
    });

    return (
        <div className="mx-auto max-w-5xl p-6">
            <div className="mb-5">
                <h1 className="text-[22px] font-bold text-m-text">내 휴가 신청내역</h1>
                <p className="mt-1 text-[13px] text-m-muted">신청한 휴가의 결재 상태를 확인하고 취소·재신청합니다.</p>
            </div>

            <LeaveTabs />

            <div className="mb-5">
                <BalanceSummary balance={balance} />
            </div>

            {error && (
                <div className="mb-4 rounded-lg border border-m-danger/20 bg-m-danger-soft px-3 py-2 text-[13px] text-m-danger">
                    {error}
                </div>
            )}

            {isLoading ? (
                <div className="rounded-2xl border border-m-border bg-m-surface p-10 text-center text-[13px] text-m-subtle">
                    불러오는 중입니다.
                </div>
            ) : requests.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-2xl border border-m-border bg-m-surface p-12 text-m-subtle">
                    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-m-surface-alt">
                        <Icon name="calendar" size={32} />
                    </div>
                    <p className="text-[14px]">아직 신청한 휴가가 없습니다.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {requests.map((req) => {
                        const busy = cancelMutation.isPending || resubmitMutation.isPending;
                        const isResubmitting = resubmitId === req.leave_request_id;
                        return (
                            <div key={req.leave_request_id} className="rounded-2xl border border-m-border bg-m-surface p-5">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-[15px] font-bold text-m-text">
                                                {LEAVE_TYPE_LABELS[req.leave_type]}
                                            </h3>
                                            <StatusBadge status={req.status} />
                                        </div>
                                        <p className="mt-1 text-[13px] text-m-muted">
                                            {formatDate(req.start_date)} ~ {formatDate(req.end_date)} · {formatDays(req.requested_days)}
                                        </p>
                                        {req.reason && <p className="mt-1 text-[12px] text-m-subtle">사유: {req.reason}</p>}
                                    </div>
                                    <ApprovalStepper steps={mySteps(req)} />
                                </div>

                                {req.status === 'REJECTED' && req.reject_reason && (
                                    <div className="mt-3 rounded-lg border border-m-danger/20 bg-m-danger-soft px-3 py-2 text-[12px] text-m-danger">
                                        반려 사유: {req.reject_reason}
                                    </div>
                                )}
                                {req.status === 'CHANGE_REQUESTED' && req.change_request_reason && (
                                    <div className="mt-3 rounded-lg border border-m-primary/20 bg-m-primary-soft px-3 py-2 text-[12px] text-m-primary">
                                        결재자 변경 요청: {req.change_request_reason}
                                    </div>
                                )}
                                {req.status === 'CANCEL_REQUESTED' && (
                                    <div className="mt-3 rounded-lg bg-m-surface-alt px-3 py-2 text-[12px] text-m-muted">
                                        취소 요청이 접수되어 결재자의 승인을 기다리고 있습니다.
                                    </div>
                                )}

                                {/* 상태별 액션 */}
                                {(req.status === 'PENDING' ||
                                    req.status === 'APPROVED' ||
                                    req.status === 'CHANGE_REQUESTED') && (
                                    <div className="mt-4 flex gap-2">
                                        {req.status === 'CHANGE_REQUESTED' && (
                                            <button
                                                type="button"
                                                disabled={busy}
                                                onClick={() =>
                                                    setResubmitId(isResubmitting ? null : req.leave_request_id)
                                                }
                                                className="h-9 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white disabled:opacity-60"
                                            >
                                                {isResubmitting ? '재신청 닫기' : '재신청'}
                                            </button>
                                        )}
                                        <button
                                            type="button"
                                            disabled={busy}
                                            onClick={() => cancelMutation.mutate(req.leave_request_id)}
                                            className="h-9 rounded-lg border border-m-border px-4 text-[13px] font-semibold text-m-muted disabled:opacity-60"
                                        >
                                            {req.status === 'APPROVED' ? '취소 요청' : '신청 취소'}
                                        </button>
                                    </div>
                                )}

                                {isResubmitting && (
                                    <div className="mt-4 border-t border-m-border pt-4">
                                        <p className="mb-3 text-[13px] font-semibold text-m-text">일정을 수정해 다시 신청</p>
                                        <LeaveRequestForm
                                            balance={balance}
                                            approvalSteps={previewApprovalSteps(user)}
                                            submitting={resubmitMutation.isPending}
                                            submitLabel="재신청"
                                            initial={{
                                                leave_type: req.leave_type,
                                                start_date: req.start_date,
                                                end_date: req.end_date,
                                                reason: req.reason ?? '',
                                            }}
                                            onSubmit={(payload) =>
                                                resubmitMutation.mutate({ id: req.leave_request_id, payload })
                                            }
                                            onYearChange={setYear}
                                            onCancel={() => setResubmitId(null)}
                                        />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
