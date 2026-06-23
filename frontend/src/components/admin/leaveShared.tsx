'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Badge from '../ui/Badge';
import Gauge from '../ui/Gauge';
import type { LeaveBalance, LeaveStatus, LeaveType } from '../../api/leave';
import type { User } from '../../api/types';

export const LEAVE_TYPE_LABELS: Record<LeaveType, string> = {
    ANNUAL: '연차',
    AM_HALF: '오전반차',
    PM_HALF: '오후반차',
    SICK: '병가',
    FAMILY_EVENT: '경조휴가',
    OFFICIAL: '공가',
    COMPENSATORY: '대체휴무',
};

export const LEAVE_TYPE_OPTIONS: LeaveType[] = [
    'ANNUAL',
    'AM_HALF',
    'PM_HALF',
    'SICK',
    'FAMILY_EVENT',
    'OFFICIAL',
    'COMPENSATORY',
];

export const LEAVE_STATUS_LABELS: Record<LeaveStatus, string> = {
    PENDING: '신청 대기',
    APPROVED: '승인',
    REJECTED: '반려',
    CANCELED: '취소',
    CANCEL_REQUESTED: '취소 요청',
    CHANGE_REQUESTED: '일정 변경 요청',
};

type BadgeVariant = 'default' | 'success' | 'warn' | 'danger' | 'muted' | 'primary';

const STATUS_VARIANT: Record<LeaveStatus, BadgeVariant> = {
    PENDING: 'warn',
    APPROVED: 'success',
    REJECTED: 'danger',
    CANCELED: 'muted',
    CANCEL_REQUESTED: 'primary',
    CHANGE_REQUESTED: 'primary',
};

export function StatusBadge({ status }: { status: LeaveStatus }) {
    return <Badge variant={STATUS_VARIANT[status]}>{LEAVE_STATUS_LABELS[status]}</Badge>;
}

export function isHalfType(type: LeaveType): boolean {
    return type === 'AM_HALF' || type === 'PM_HALF';
}

/** 'YYYY-MM-DD' 두 날짜의 포함 일수(end - start + 1)를 계산한다. */
function inclusiveDays(start: string, end: string): number {
    const s = Date.parse(`${start}T00:00:00Z`);
    const e = Date.parse(`${end}T00:00:00Z`);
    if (Number.isNaN(s) || Number.isNaN(e)) return 0;
    return Math.round((e - s) / 86_400_000) + 1;
}

/**
 * 백엔드 _calculate_requested_days 와 동일한 규칙으로 신청 일수를 계산한다.
 * 반차 종류는 0.5일, 그 외에는 양 끝 반차를 0.5씩 차감한다.
 */
export function calcRequestedDays(
    type: LeaveType,
    start: string,
    end: string,
    startHalf: boolean,
    endHalf: boolean,
): number {
    if (isHalfType(type)) return 0.5;
    if (!start || !end) return 0;
    if (start > end) return 0;
    let days = inclusiveDays(start, end);
    if (start === end) {
        if (startHalf || endHalf) days = 0.5;
    } else {
        if (startHalf) days -= 0.5;
        if (endHalf) days -= 0.5;
    }
    return days > 0 ? days : 0;
}

export function formatDays(value: number): string {
    return Number.isInteger(value) ? `${value}일` : `${value.toFixed(1)}일`;
}

export function formatDate(value: string | null): string {
    if (!value) return '-';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString('ko-KR');
}

// ───────────────────── 서브 네비게이션 탭 ─────────────────────
const LEAVE_TABS = [
    { to: '/admin/leave/request', label: '휴가 신청' },
    { to: '/admin/leave/approvals', label: '결재함' },
    { to: '/admin/leave/my', label: '내 신청내역' },
];

export function LeaveTabs() {
    const pathname = usePathname();
    return (
        <div className="mb-5 flex gap-1 border-b border-m-border">
            {LEAVE_TABS.map((tab) => {
                const active = pathname === tab.to;
                return (
                    <Link
                        key={tab.to}
                        href={tab.to}
                        className={`-mb-px border-b-2 px-4 py-2.5 text-[13px] font-semibold transition-colors ${
                            active
                                ? 'border-m-primary text-m-primary'
                                : 'border-transparent text-m-muted hover:text-m-text'
                        }`}
                    >
                        {tab.label}
                    </Link>
                );
            })}
        </div>
    );
}

// ───────────────────── 결재선 stepper ─────────────────────
export interface ApprovalStep {
    label: string;
    name: string;
    sub?: string;
    state: 'done' | 'current' | 'pending';
}

export function ApprovalStepper({ steps }: { steps: ApprovalStep[] }) {
    return (
        <div className="flex items-center gap-2">
            {steps.map((step, i) => (
                <div key={`${step.label}-${i}`} className="flex items-center gap-2">
                    <div className="flex flex-col items-center gap-1">
                        <div
                            className={`flex h-8 w-8 items-center justify-center rounded-full border text-[12px] font-bold ${
                                step.state === 'done'
                                    ? 'border-m-success bg-m-success-soft text-m-success'
                                    : step.state === 'current'
                                      ? 'border-m-primary bg-m-primary-soft text-m-primary'
                                      : 'border-m-border bg-m-surface-alt text-m-subtle'
                            }`}
                        >
                            {i + 1}
                        </div>
                        <div className="text-center">
                            <p className="text-[12px] font-semibold text-m-text">{step.name}</p>
                            <p className="text-[10px] text-m-subtle">{step.label}{step.sub ? ` · ${step.sub}` : ''}</p>
                        </div>
                    </div>
                    {i < steps.length - 1 && <div className="mb-5 h-px w-8 bg-m-border-strong" />}
                </div>
            ))}
        </div>
    );
}

/** 신청 전 결재선 미리보기를 현재 사용자 등급으로 근사한다(실제 결재자는 신청 후 응답에 포함). */
export function previewApprovalSteps(user: User | null): ApprovalStep[] {
    const me = user?.name ?? '나';
    if (user?.admin_level === 'A') {
        return [
            { label: '신청', name: me, sub: '최고관리자', state: 'current' },
            { label: '결재', name: '다른 최고관리자', sub: 'A등급', state: 'pending' },
        ];
    }
    if (user?.admin_level === 'B') {
        return [
            { label: '신청', name: me, sub: '팀장', state: 'current' },
            { label: '결재', name: '최고관리자', sub: 'A등급', state: 'pending' },
        ];
    }
    return [
        { label: '신청', name: me, sub: '팀원', state: 'current' },
        { label: '결재', name: '소속 팀장', sub: '팀 LEAD', state: 'pending' },
    ];
}

// ───────────────────── 잔여 요약(게이지 + 타일) ─────────────────────
export function BalanceSummary({
    balance,
    requestedDays = 0,
}: {
    balance: LeaveBalance | undefined;
    requestedDays?: number;
}) {
    const granted = balance?.granted_days ?? 0;
    const used = balance?.used_days ?? 0;
    const pending = balance?.pending_days ?? 0;
    const remaining = balance?.remaining_days ?? 0;
    const ratio = granted > 0 ? Math.round((remaining / granted) * 100) : 0;
    const afterRemaining = remaining - requestedDays;
    const insufficient = requestedDays > 0 && requestedDays > remaining;

    const tiles: { label: string; value: number; tone: string }[] = [
        { label: '부여', value: granted, tone: 'text-m-text' },
        { label: '사용', value: used, tone: 'text-m-text' },
        { label: '대기', value: pending, tone: 'text-m-warn' },
        { label: '잔여', value: remaining, tone: 'text-m-primary' },
    ];

    return (
        <div className="rounded-2xl border border-m-border bg-m-surface p-5">
            <div className="flex items-center gap-5">
                <Gauge score={ratio} size={104} stroke={9} label="잔여율" />
                <div className="flex-1">
                    <p className="text-[12px] font-semibold text-m-subtle">{balance?.year ?? new Date().getFullYear()}년 연차</p>
                    <p className="mt-0.5 text-[20px] font-bold text-m-text">
                        잔여 {formatDays(remaining)}
                        <span className="text-[13px] font-medium text-m-subtle"> / 부여 {formatDays(granted)}</span>
                    </p>
                    {requestedDays > 0 && (
                        <p className={`mt-1 text-[12px] font-medium ${insufficient ? 'text-m-danger' : 'text-m-muted'}`}>
                            {insufficient
                                ? `신청 ${formatDays(requestedDays)} · 잔여일 부족`
                                : `신청 ${formatDays(requestedDays)} 후 잔여 ${formatDays(afterRemaining)}`}
                        </p>
                    )}
                </div>
            </div>
            <div className="mt-4 grid grid-cols-4 gap-2">
                {tiles.map((tile) => (
                    <div key={tile.label} className="rounded-xl bg-m-surface-alt p-3 text-center">
                        <p className="text-[11px] font-semibold text-m-subtle">{tile.label}</p>
                        <p className={`mt-0.5 text-[16px] font-bold ${tile.tone}`}>{formatDays(tile.value)}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
