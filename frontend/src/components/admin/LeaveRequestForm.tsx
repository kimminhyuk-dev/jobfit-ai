'use client';

import { useEffect, useState } from 'react';
import type { LeaveBalance, LeaveRequestCreate, LeaveType } from '../../api/leave';
import {
    ApprovalStepper,
    BalanceSummary,
    LEAVE_TYPE_LABELS,
    LEAVE_TYPE_OPTIONS,
    calcRequestedDays,
    formatDays,
    isHalfType,
    type ApprovalStep,
} from './leaveShared';

export interface LeaveFormInitial {
    leave_type?: LeaveType;
    start_date?: string;
    end_date?: string;
    reason?: string;
}

interface LeaveRequestFormProps {
    balance: LeaveBalance | undefined;
    approvalSteps: ApprovalStep[];
    submitting: boolean;
    submitLabel: string;
    error?: string | null;
    initial?: LeaveFormInitial;
    onSubmit: (payload: LeaveRequestCreate) => void;
    onYearChange?: (year: number) => void;
    onCancel?: () => void;
}

function yearOf(date: string): number | null {
    const y = Number.parseInt(date.slice(0, 4), 10);
    return Number.isNaN(y) ? null : y;
}

export default function LeaveRequestForm({
    balance,
    approvalSteps,
    submitting,
    submitLabel,
    error,
    initial,
    onSubmit,
    onYearChange,
    onCancel,
}: LeaveRequestFormProps) {
    const [leaveType, setLeaveType] = useState<LeaveType>(initial?.leave_type ?? 'ANNUAL');
    const [startDate, setStartDate] = useState(initial?.start_date ?? '');
    const [endDate, setEndDate] = useState(initial?.end_date ?? '');
    const [startHalf, setStartHalf] = useState(false);
    const [endHalf, setEndHalf] = useState(false);
    const [singleHalf, setSingleHalf] = useState(false);
    const [reason, setReason] = useState(initial?.reason ?? '');
    const [localError, setLocalError] = useState<string | null>(null);

    const half = isHalfType(leaveType);
    const singleDay = startDate !== '' && startDate === endDate;
    // 반차 종류는 종료일을 시작일에 고정한다(표시/계산/페이로드 모두 startDate 기준).

    // 시작일 연도가 바뀌면 해당 연도 잔여를 다시 불러오도록 알린다.
    useEffect(() => {
        if (!startDate || !onYearChange) return;
        const y = yearOf(startDate);
        if (y) onYearChange(y);
    }, [startDate, onYearChange]);

    const effStartHalf = half ? false : singleDay ? singleHalf : startHalf;
    const effEndHalf = half ? false : singleDay ? false : endHalf;
    const days = half ? 0.5 : calcRequestedDays(leaveType, startDate, endDate, effStartHalf, effEndHalf);

    const remaining = balance?.remaining_days ?? 0;
    const insufficient = days > 0 && days > remaining;
    const canSubmit =
        !submitting &&
        balance !== undefined &&
        startDate !== '' &&
        (half || endDate !== '') &&
        days > 0 &&
        !insufficient;

    function buildPayload(): LeaveRequestCreate | null {
        if (!startDate) return null;
        const trimmedReason = reason.trim();
        const base = { leave_type: leaveType, reason: trimmedReason ? trimmedReason : null };
        if (half) {
            return { ...base, start_date: startDate, end_date: startDate };
        }
        if (!endDate || startDate > endDate) return null;
        if (startDate === endDate) {
            return {
                ...base,
                start_date: startDate,
                end_date: endDate,
                start_half_day: singleHalf ? 'PM' : null,
            };
        }
        return {
            ...base,
            start_date: startDate,
            end_date: endDate,
            start_half_day: startHalf ? 'PM' : null,
            end_half_day: endHalf ? 'AM' : null,
        };
    }

    function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLocalError(null);
        if (!half && startDate && endDate && startDate > endDate) {
            setLocalError('휴가 시작일은 종료일보다 늦을 수 없습니다.');
            return;
        }
        const payload = buildPayload();
        if (!payload || days <= 0) {
            setLocalError('신청 기간을 다시 확인해주세요.');
            return;
        }
        if (insufficient) {
            setLocalError('잔여 휴가일이 부족합니다.');
            return;
        }
        onSubmit(payload);
    }

    const inputCls =
        'h-10 w-full rounded-lg border border-m-border bg-m-surface px-3 text-[13px] text-m-text outline-none focus:border-m-primary';

    return (
        <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div className="space-y-4">
                <div>
                    <label className="mb-1.5 block text-[12px] font-semibold text-m-muted">휴가 종류</label>
                    <div className="grid grid-cols-4 gap-1.5">
                        {LEAVE_TYPE_OPTIONS.map((type) => (
                            <button
                                key={type}
                                type="button"
                                onClick={() => setLeaveType(type)}
                                className={`h-9 rounded-lg text-[12px] font-semibold transition-colors ${
                                    leaveType === type
                                        ? 'bg-m-primary text-white'
                                        : 'bg-m-surface-alt text-m-muted hover:text-m-text'
                                }`}
                            >
                                {LEAVE_TYPE_LABELS[type]}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="mb-1.5 block text-[12px] font-semibold text-m-muted">시작일</label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => {
                                setStartDate(e.target.value);
                                if (half || (endDate && e.target.value > endDate)) setEndDate(e.target.value);
                            }}
                            className={inputCls}
                        />
                    </div>
                    <div>
                        <label className="mb-1.5 block text-[12px] font-semibold text-m-muted">
                            종료일{half && <span className="ml-1 text-[11px] font-normal text-m-subtle">반차는 하루</span>}
                        </label>
                        <input
                            type="date"
                            value={half ? startDate : endDate}
                            min={startDate || undefined}
                            disabled={half}
                            onChange={(e) => setEndDate(e.target.value)}
                            className={`${inputCls} disabled:cursor-not-allowed disabled:opacity-60`}
                        />
                    </div>
                </div>

                {!half && singleDay && (
                    <label className="flex items-center gap-2 text-[13px] text-m-text">
                        <input type="checkbox" checked={singleHalf} onChange={(e) => setSingleHalf(e.target.checked)} />
                        반차로 신청 (0.5일)
                    </label>
                )}
                {!half && !singleDay && startDate !== '' && endDate !== '' && (
                    <div className="flex flex-wrap gap-4">
                        <label className="flex items-center gap-2 text-[13px] text-m-text">
                            <input type="checkbox" checked={startHalf} onChange={(e) => setStartHalf(e.target.checked)} />
                            시작일 반차 (-0.5)
                        </label>
                        <label className="flex items-center gap-2 text-[13px] text-m-text">
                            <input type="checkbox" checked={endHalf} onChange={(e) => setEndHalf(e.target.checked)} />
                            종료일 반차 (-0.5)
                        </label>
                    </div>
                )}

                <div className="flex items-center justify-between rounded-xl bg-m-surface-alt px-4 py-3">
                    <span className="text-[13px] font-semibold text-m-muted">신청 일수</span>
                    <span className="text-[18px] font-bold text-m-primary">{formatDays(days)}</span>
                </div>

                <div>
                    <label className="mb-1.5 block text-[12px] font-semibold text-m-muted">사유 (선택)</label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        rows={3}
                        maxLength={1000}
                        placeholder="휴가 사유를 입력하세요."
                        className="w-full rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] text-m-text outline-none focus:border-m-primary"
                    />
                </div>

                {(localError || error) && (
                    <div className="rounded-lg border border-m-danger/20 bg-m-danger-soft px-3 py-2 text-[13px] text-m-danger">
                        {localError || error}
                    </div>
                )}

                <div className="flex gap-2">
                    <button
                        type="submit"
                        disabled={!canSubmit}
                        className="h-11 flex-1 rounded-lg bg-m-primary text-[14px] font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {submitting ? '처리 중...' : submitLabel}
                    </button>
                    {onCancel && (
                        <button
                            type="button"
                            onClick={onCancel}
                            className="h-11 rounded-lg border border-m-border px-4 text-[14px] font-semibold text-m-muted"
                        >
                            닫기
                        </button>
                    )}
                </div>
            </div>

            <div className="space-y-5">
                <BalanceSummary balance={balance} requestedDays={days} />
                <div className="rounded-2xl border border-m-border bg-m-surface p-5">
                    <p className="mb-3 text-[12px] font-semibold text-m-subtle">결재선 미리보기</p>
                    <ApprovalStepper steps={approvalSteps} />
                    <p className="mt-3 text-[11px] text-m-subtle">실제 결재자는 신청 후 결재선에 따라 배정됩니다.</p>
                </div>
            </div>
        </form>
    );
}
