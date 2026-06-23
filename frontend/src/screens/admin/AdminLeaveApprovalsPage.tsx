'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { leaveApi, type LeaveRequest } from '../../api/leave';
import type { ApiError } from '../../api/types';
import { useAuth } from '../../stores/authContext';
import Icon from '../../components/ui/Icon';
import { showToast } from '../../components/ui/Toast';
import {
    ApprovalStepper,
    LEAVE_TYPE_LABELS,
    LeaveTabs,
    StatusBadge,
    formatDate,
    formatDays,
} from '../../components/admin/leaveShared';

type ActionMode = null | 'reject' | 'change';

export default function AdminLeaveApprovalsPage() {
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const canApprove = user?.admin_level === 'A' || user?.admin_level === 'B';

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [actionMode, setActionMode] = useState<ActionMode>(null);
    const [reasonText, setReasonText] = useState('');
    const [error, setError] = useState<string | null>(null);

    const {
        data: requests = [],
        isLoading,
        isError,
    } = useQuery({
        queryKey: ['leave', 'pending'],
        queryFn: () => leaveApi.listPending(),
        enabled: canApprove,
    });

    const selected = requests.find((r) => r.leave_request_id === selectedId) ?? null;

    function resetAction() {
        setActionMode(null);
        setReasonText('');
    }

    function afterMutate(message: string) {
        setError(null);
        resetAction();
        setSelectedId(null);
        showToast(message, 'success');
        queryClient.invalidateQueries({ queryKey: ['leave', 'pending'] });
        queryClient.invalidateQueries({ queryKey: ['leave', 'mine'] });
    }

    const onError = (err: ApiError) => setError(err.message || '처리에 실패했습니다.');

    const approveMutation = useMutation({
        mutationFn: (id: number) => leaveApi.approve(id),
        onSuccess: () => afterMutate('휴가 신청을 승인했습니다.'),
        onError,
    });
    const rejectMutation = useMutation({
        mutationFn: ({ id, reason }: { id: number; reason: string }) => leaveApi.reject(id, reason),
        onSuccess: () => afterMutate('휴가 신청을 반려했습니다.'),
        onError,
    });
    const changeMutation = useMutation({
        mutationFn: ({ id, reason }: { id: number; reason: string }) => leaveApi.requestChange(id, reason),
        onSuccess: () => afterMutate('일정 변경 요청을 보냈습니다.'),
        onError,
    });
    const cancelApproveMutation = useMutation({
        mutationFn: (id: number) => leaveApi.approveCancel(id),
        onSuccess: () => afterMutate('휴가 취소 요청을 승인했습니다.'),
        onError,
    });
    const cancelRejectMutation = useMutation({
        mutationFn: (id: number) => leaveApi.rejectCancel(id),
        onSuccess: () => afterMutate('휴가 취소 요청을 반려했습니다.'),
        onError,
    });

    const busy =
        approveMutation.isPending ||
        rejectMutation.isPending ||
        changeMutation.isPending ||
        cancelApproveMutation.isPending ||
        cancelRejectMutation.isPending;

    function submitReason() {
        if (!selected) return;
        const reason = reasonText.trim();
        if (!reason) {
            setError(actionMode === 'reject' ? '반려 사유를 입력하세요.' : '변경 요청 사유를 입력하세요.');
            return;
        }
        if (actionMode === 'reject') rejectMutation.mutate({ id: selected.leave_request_id, reason });
        else changeMutation.mutate({ id: selected.leave_request_id, reason });
    }

    if (!canApprove) {
        return (
            <div className="mx-auto max-w-6xl p-6">
                <div className="mb-5">
                    <h1 className="text-[22px] font-bold text-m-text">휴가 결재함</h1>
                </div>
                <LeaveTabs />
                <div className="rounded-2xl border border-m-border bg-m-surface p-10 text-center text-[13px] text-m-subtle">
                    결재 권한(LEAVE_APPROVE)이 있는 관리자만 결재함을 사용할 수 있습니다.
                </div>
            </div>
        );
    }

    return (
        <div className="mx-auto flex h-full max-w-6xl flex-col p-6">
            <div className="mb-5">
                <h1 className="text-[22px] font-bold text-m-text">휴가 결재함</h1>
                <p className="mt-1 text-[13px] text-m-muted">내가 결재할 휴가 신청과 취소 요청을 처리합니다.</p>
            </div>

            <LeaveTabs />

            {error && (
                <div className="mb-4 rounded-lg border border-m-danger/20 bg-m-danger-soft px-3 py-2 text-[13px] text-m-danger">
                    {error}
                </div>
            )}

            <div className="grid min-h-0 flex-1 grid-cols-12 gap-6">
                {/* Master list */}
                <aside className="col-span-5 flex min-h-0 flex-col overflow-hidden rounded-2xl border border-m-border bg-m-surface">
                    <div className="border-b border-m-border px-4 py-2.5 text-[12px] text-m-muted">
                        {isLoading ? '불러오는 중...' : `결재 대기 ${requests.length}건`}
                    </div>
                    <div className="flex-1 space-y-1 overflow-y-auto p-2">
                        {isError ? (
                            <div className="p-4 text-center text-[13px] text-m-subtle">목록을 불러오지 못했습니다.</div>
                        ) : requests.length === 0 ? (
                            <div className="p-6 text-center text-[13px] text-m-subtle">결재할 휴가 신청이 없습니다.</div>
                        ) : (
                            requests.map((req) => (
                                <button
                                    key={req.leave_request_id}
                                    type="button"
                                    onClick={() => {
                                        setSelectedId(req.leave_request_id);
                                        resetAction();
                                        setError(null);
                                    }}
                                    className={`w-full rounded-xl p-3 text-left transition-colors ${
                                        selectedId === req.leave_request_id ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                                    }`}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="truncate text-[13px] font-semibold text-m-text">
                                            {req.requester_name ?? req.requester_email ?? `#${req.requester_id}`}
                                        </p>
                                        <StatusBadge status={req.status} />
                                    </div>
                                    <p className="mt-1 text-[12px] text-m-muted">
                                        {LEAVE_TYPE_LABELS[req.leave_type]} · {formatDays(req.requested_days)}
                                    </p>
                                    <p className="text-[11px] text-m-subtle">
                                        {formatDate(req.start_date)} ~ {formatDate(req.end_date)}
                                    </p>
                                </button>
                            ))
                        )}
                    </div>
                </aside>

                {/* Detail */}
                <section className="col-span-7 min-h-0 overflow-y-auto">
                    {selected ? (
                        <LeaveApprovalDetail
                            request={selected}
                            isOwn={selected.requester_id === user?.user_id}
                            busy={busy}
                            actionMode={actionMode}
                            reasonText={reasonText}
                            onReasonChange={setReasonText}
                            onStartAction={(mode) => {
                                setActionMode(mode);
                                setReasonText('');
                                setError(null);
                            }}
                            onCancelAction={resetAction}
                            onApprove={() => approveMutation.mutate(selected.leave_request_id)}
                            onApproveCancel={() => cancelApproveMutation.mutate(selected.leave_request_id)}
                            onRejectCancel={() => cancelRejectMutation.mutate(selected.leave_request_id)}
                            onSubmitReason={submitReason}
                        />
                    ) : (
                        <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-m-border bg-m-surface text-m-subtle">
                            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-m-surface-alt">
                                <Icon name="calendar" size={32} />
                            </div>
                            <p className="text-[14px]">왼쪽 목록에서 휴가 신청을 선택하세요.</p>
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

function LeaveApprovalDetail({
    request,
    isOwn,
    busy,
    actionMode,
    reasonText,
    onReasonChange,
    onStartAction,
    onCancelAction,
    onApprove,
    onApproveCancel,
    onRejectCancel,
    onSubmitReason,
}: {
    request: LeaveRequest;
    isOwn: boolean;
    busy: boolean;
    actionMode: ActionMode;
    reasonText: string;
    onReasonChange: (v: string) => void;
    onStartAction: (mode: 'reject' | 'change') => void;
    onCancelAction: () => void;
    onApprove: () => void;
    onApproveCancel: () => void;
    onRejectCancel: () => void;
    onSubmitReason: () => void;
}) {
    const isCancelRequest = request.status === 'CANCEL_REQUESTED';

    return (
        <div className="space-y-5">
            <div className="rounded-2xl border border-m-border bg-m-surface p-6">
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h2 className="text-[18px] font-bold text-m-text">{LEAVE_TYPE_LABELS[request.leave_type]}</h2>
                        <p className="mt-0.5 text-[13px] text-m-muted">
                            {formatDate(request.start_date)} ~ {formatDate(request.end_date)} · {formatDays(request.requested_days)}
                        </p>
                    </div>
                    <StatusBadge status={request.status} />
                </div>

                <div className="mb-5">
                    <ApprovalStepper
                        steps={[
                            {
                                label: '신청',
                                name: request.requester_name ?? request.requester_email ?? `#${request.requester_id}`,
                                state: 'done',
                            },
                            {
                                label: '결재',
                                name: request.approver_name ?? '나',
                                state: 'current',
                            },
                        ]}
                    />
                </div>

                <div className="grid grid-cols-2 gap-3 text-[13px]">
                    <div className="rounded-xl bg-m-surface-alt p-3">
                        <p className="mb-1 text-[11px] font-semibold text-m-subtle">신청자</p>
                        <p className="text-m-text">{request.requester_name ?? '-'}</p>
                        <p className="text-[11px] text-m-subtle">{request.requester_email ?? ''}</p>
                    </div>
                    <div className="rounded-xl bg-m-surface-alt p-3">
                        <p className="mb-1 text-[11px] font-semibold text-m-subtle">신청 사유</p>
                        <p className="text-m-text">{request.reason || '-'}</p>
                    </div>
                </div>

                {request.status === 'CANCEL_REQUESTED' && (
                    <div className="mt-3 rounded-xl border border-m-primary/20 bg-m-primary-soft px-3 py-2 text-[12px] text-m-primary">
                        승인된 휴가에 대한 취소 요청입니다. 취소를 승인하면 사용 일수가 복구됩니다.
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="rounded-2xl border border-m-border bg-m-surface p-5">
                {isOwn ? (
                    <div className="rounded-lg bg-m-surface-alt px-3 py-3 text-center text-[13px] font-medium text-m-subtle">
                        본인 신청은 본인이 결재할 수 없습니다 (직무 분리).
                    </div>
                ) : actionMode ? (
                    <div className="space-y-3">
                        <label className="block text-[12px] font-semibold text-m-muted">
                            {actionMode === 'reject' ? '반려 사유' : '일정 변경 요청 사유'}
                        </label>
                        <textarea
                            value={reasonText}
                            onChange={(e) => onReasonChange(e.target.value)}
                            rows={3}
                            maxLength={1000}
                            placeholder={actionMode === 'reject' ? '반려 사유를 입력하세요.' : '변경이 필요한 내용을 입력하세요.'}
                            className="w-full rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] text-m-text outline-none focus:border-m-primary"
                        />
                        <div className="flex gap-2">
                            <button
                                type="button"
                                disabled={busy}
                                onClick={onSubmitReason}
                                className={`h-10 flex-1 rounded-lg text-[13px] font-semibold text-white disabled:opacity-60 ${
                                    actionMode === 'reject' ? 'bg-m-danger' : 'bg-m-primary'
                                }`}
                            >
                                {actionMode === 'reject' ? '반려하기' : '변경 요청 보내기'}
                            </button>
                            <button
                                type="button"
                                onClick={onCancelAction}
                                className="h-10 rounded-lg border border-m-border px-4 text-[13px] font-semibold text-m-muted"
                            >
                                취소
                            </button>
                        </div>
                    </div>
                ) : isCancelRequest ? (
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            type="button"
                            disabled={busy}
                            onClick={onApproveCancel}
                            className="h-11 rounded-lg bg-m-primary text-[14px] font-semibold text-white disabled:opacity-60"
                        >
                            취소 승인
                        </button>
                        <button
                            type="button"
                            disabled={busy}
                            onClick={onRejectCancel}
                            className="h-11 rounded-lg border border-m-danger/30 bg-m-danger-soft text-[14px] font-semibold text-m-danger disabled:opacity-60"
                        >
                            취소 반려
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            type="button"
                            disabled={busy}
                            onClick={onApprove}
                            className="h-11 rounded-lg bg-m-success text-[13px] font-semibold text-white disabled:opacity-60"
                        >
                            승인
                        </button>
                        <button
                            type="button"
                            disabled={busy}
                            onClick={() => onStartAction('change')}
                            className="h-11 rounded-lg border border-m-primary bg-m-primary-soft text-[13px] font-semibold text-m-primary disabled:opacity-60"
                        >
                            일정 변경 요청
                        </button>
                        <button
                            type="button"
                            disabled={busy}
                            onClick={() => onStartAction('reject')}
                            className="h-11 rounded-lg border border-m-danger/30 bg-m-danger-soft text-[13px] font-semibold text-m-danger disabled:opacity-60"
                        >
                            반려
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
