'use client';

import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import { userRoleApi, type AssignableRole } from '../../api/userRoles';
import type { ApiError, AdminUser } from '../../api/types';
import { useAuth } from '../../stores/authContext';
import { showToast } from '../../components/ui/Toast';
import Icon from '../../components/ui/Icon';

const SUPER_ADMIN = 'SUPER_ADMIN';

function userLabel(user: AdminUser): string {
    if (user.role === 'COMPANY') return user.company?.company_name ?? user.name ?? '기업회원';
    return user.name ?? user.email;
}

export default function AdminUserRolesPage() {
    const { user: currentUser } = useAuth();
    const queryClient = useQueryClient();

    const [keyword, setKeyword] = useState('');
    const [appliedKeyword, setAppliedKeyword] = useState('');
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
    const [confirmRole, setConfirmRole] = useState<AssignableRole | null>(null);

    const { data: users = [], isLoading: usersLoading } = useQuery({
        queryKey: ['admin', 'user-roles', 'search', appliedKeyword],
        queryFn: () => adminApi.listUsers({ q: appliedKeyword || undefined, limit: 30 }),
    });

    const {
        data: rolesData,
        isLoading: rolesLoading,
        isError: rolesError,
    } = useQuery({
        queryKey: ['admin', 'user-roles', 'detail', selectedUserId],
        queryFn: () => userRoleApi.get(selectedUserId as number),
        enabled: selectedUserId !== null,
    });

    const assignedSet = new Set(rolesData?.assigned_role_codes ?? []);

    function refreshRoles() {
        queryClient.invalidateQueries({ queryKey: ['admin', 'user-roles', 'detail', selectedUserId] });
    }

    const assignMutation = useMutation({
        mutationFn: (roleCode: string) => userRoleApi.assign(selectedUserId as number, roleCode),
        onSuccess: (_data, roleCode) => {
            showToast(`${roleCode} 역할을 부여했습니다.`, 'success');
            refreshRoles();
        },
        onError: (err: ApiError) => showToast(err.message || '역할 부여에 실패했습니다.', 'error'),
    });

    const revokeMutation = useMutation({
        mutationFn: (roleCode: string) => userRoleApi.revoke(selectedUserId as number, roleCode),
        onSuccess: (_data, roleCode) => {
            showToast(`${roleCode} 역할을 회수했습니다.`, 'success');
            refreshRoles();
        },
        onError: (err: ApiError) => showToast(err.message || '역할 회수에 실패했습니다.', 'error'),
    });

    const busy = assignMutation.isPending || revokeMutation.isPending;

    function applySearch(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setAppliedKeyword(keyword.trim());
    }

    function handleAssign(role: AssignableRole) {
        if (role.code === SUPER_ADMIN) {
            setConfirmRole(role);
            return;
        }
        assignMutation.mutate(role.code);
    }

    function confirmAssign() {
        if (!confirmRole) return;
        assignMutation.mutate(confirmRole.code);
        setConfirmRole(null);
    }

    /** 안전장치: 회수가 막혀야 하면 사유 문자열을, 가능하면 null을 반환한다. */
    function revokeBlockReason(roleCode: string): string | null {
        if (roleCode !== SUPER_ADMIN || !rolesData) return null;
        if (currentUser && rolesData.user_id === currentUser.user_id) {
            return '본인 계정의 최고관리자 역할은 회수할 수 없습니다.';
        }
        if (rolesData.super_admin_count <= 1) {
            return '시스템 최고관리자가 1명뿐이라 회수할 수 없습니다.';
        }
        return null;
    }

    return (
        <div className="mx-auto flex h-full max-w-7xl flex-col p-6">
            <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                    <h1 className="text-[22px] font-bold text-m-text">역할 관리</h1>
                    <p className="mt-1 text-[13px] text-m-muted">사용자를 검색해 RBAC 역할을 부여하거나 회수합니다.</p>
                </div>
                <div className="flex h-10 items-center gap-2 rounded-full border border-m-border bg-m-surface px-4 text-[13px] font-semibold text-m-muted">
                    <Icon name="lock" size={16} />
                    권한 부여/회수
                </div>
            </div>

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(360px,1.1fr)]">
                {/* 좌측: 검색 + 사용자 목록 */}
                <section className="flex min-h-0 flex-col rounded-2xl border border-m-border bg-m-surface">
                    <form onSubmit={applySearch} className="flex gap-2 border-b border-m-border p-4">
                        <input
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            placeholder="이름 · user_id · 이메일 검색"
                            className="h-10 flex-1 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                        />
                        <button type="submit" className="h-10 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white">
                            검색
                        </button>
                    </form>

                    <div className="min-h-0 flex-1 overflow-y-auto p-2">
                        {usersLoading ? (
                            <div className="flex h-72 items-center justify-center text-[13px] text-m-subtle">불러오는 중...</div>
                        ) : users.length === 0 ? (
                            <div className="flex h-72 items-center justify-center text-[13px] text-m-subtle">조회 결과가 없습니다.</div>
                        ) : (
                            users.map((user) => (
                                <button
                                    key={user.user_id}
                                    type="button"
                                    onClick={() => setSelectedUserId(user.user_id)}
                                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${
                                        selectedUserId === user.user_id ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                                    }`}
                                >
                                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-m-surface-alt">
                                        <Icon name={user.role === 'COMPANY' ? 'building' : user.role === 'ADMIN' ? 'shield' : 'user'} size={18} />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-[13px] font-semibold text-m-text">{userLabel(user)}</p>
                                        <p className="truncate text-[12px] text-m-subtle">#{user.user_id} · {user.email}</p>
                                    </div>
                                    {user.role === 'ADMIN' && (
                                        <span className="shrink-0 rounded-full bg-m-surface-alt px-2 py-0.5 text-[11px] font-semibold text-m-muted">
                                            {user.admin_level ? `ADMIN ${user.admin_level}` : 'ADMIN'}
                                        </span>
                                    )}
                                </button>
                            ))
                        )}
                    </div>
                </section>

                {/* 우측: 선택 사용자 역할 상세 */}
                <aside className="min-h-0 overflow-y-auto rounded-2xl border border-m-border bg-m-surface p-5">
                    {selectedUserId === null ? (
                        <div className="flex h-full min-h-72 flex-col items-center justify-center text-center text-m-subtle">
                            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-m-surface-alt">
                                <Icon name="lock" size={28} />
                            </div>
                            <p className="text-[13px]">좌측에서 사용자를 선택하세요.</p>
                        </div>
                    ) : rolesLoading ? (
                        <div className="flex h-72 items-center justify-center text-[13px] text-m-subtle">불러오는 중...</div>
                    ) : rolesError || !rolesData ? (
                        <div className="flex h-72 items-center justify-center text-[13px] text-m-danger">역할 정보를 불러오지 못했습니다.</div>
                    ) : (
                        <div className="space-y-5">
                            <div>
                                <h2 className="truncate text-[17px] font-bold text-m-text">{rolesData.name}</h2>
                                <p className="mt-0.5 text-[12px] text-m-muted">#{rolesData.user_id} · {rolesData.email}</p>
                                <div className="mt-3 flex flex-wrap gap-1.5">
                                    {rolesData.assigned_role_codes.length === 0 ? (
                                        <span className="text-[12px] text-m-subtle">보유한 역할이 없습니다.</span>
                                    ) : (
                                        rolesData.assigned_role_codes.map((code) => (
                                            <span key={code} className="rounded-full bg-m-primary-soft px-2.5 py-1 text-[11px] font-semibold text-m-primary">
                                                {code}
                                            </span>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div className="space-y-3">
                                {rolesData.available_roles.map((role) => {
                                    const assigned = assignedSet.has(role.code);
                                    const blockReason = assigned ? revokeBlockReason(role.code) : null;
                                    return (
                                        <div key={role.code} className="rounded-xl border border-m-border bg-m-surface-alt p-4">
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-[14px] font-bold text-m-text">{role.name}</p>
                                                        <span className="rounded bg-m-surface px-1.5 py-0.5 text-[10px] font-semibold text-m-muted">{role.code}</span>
                                                        {assigned && (
                                                            <span className="inline-flex items-center gap-1 rounded-full bg-m-success-soft px-2 py-0.5 text-[10px] font-semibold text-m-success">
                                                                <Icon name="check" size={11} /> 보유
                                                            </span>
                                                        )}
                                                    </div>
                                                    {role.description && (
                                                        <p className="mt-1 text-[12px] text-m-muted">{role.description}</p>
                                                    )}
                                                </div>
                                                {assigned ? (
                                                    <button
                                                        type="button"
                                                        disabled={busy || blockReason !== null}
                                                        onClick={() => revokeMutation.mutate(role.code)}
                                                        className="h-9 shrink-0 rounded-lg border border-m-danger px-3 text-[12px] font-semibold text-m-danger transition-colors hover:bg-m-danger-soft disabled:cursor-not-allowed disabled:opacity-40"
                                                    >
                                                        회수
                                                    </button>
                                                ) : (
                                                    <button
                                                        type="button"
                                                        disabled={busy}
                                                        onClick={() => handleAssign(role)}
                                                        className={`h-9 shrink-0 rounded-lg px-3 text-[12px] font-semibold text-white transition-opacity disabled:opacity-40 ${
                                                            role.code === SUPER_ADMIN ? 'bg-m-danger' : 'bg-m-primary'
                                                        }`}
                                                    >
                                                        부여
                                                    </button>
                                                )}
                                            </div>

                                            {role.permissions.length > 0 && (
                                                <div className="mt-3 flex flex-wrap gap-1.5">
                                                    {role.permissions.map((perm) => (
                                                        <span
                                                            key={perm.code}
                                                            title={perm.code}
                                                            className="rounded-md bg-m-surface px-2 py-0.5 text-[11px] font-medium text-m-muted"
                                                        >
                                                            {perm.name}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {blockReason && (
                                                <p className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-m-danger">
                                                    <Icon name="lock" size={12} /> {blockReason}
                                                </p>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </aside>
            </div>

            {/* SUPER_ADMIN 부여 확인 다이얼로그 */}
            {confirmRole && (
                <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/40 p-4">
                    <div className="w-full max-w-md rounded-2xl border border-m-border bg-m-surface p-6 shadow-xl">
                        <div className="mb-3 flex items-center gap-2.5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-m-danger-soft">
                                <Icon name="shield" size={20} className="text-m-danger" />
                            </div>
                            <h3 className="text-[16px] font-bold text-m-text">최고관리자 권한 부여</h3>
                        </div>
                        <p className="text-[13px] leading-relaxed text-m-muted">
                            <span className="font-semibold text-m-text">{rolesData?.name}</span> 님에게{' '}
                            <span className="font-semibold text-m-danger">{confirmRole.code}</span> 역할을 부여합니다.
                            모든 관리 권한이 포함되며 시스템 전체에 영향을 줍니다. 계속하시겠습니까?
                        </p>
                        <div className="mt-5 flex justify-end gap-2">
                            <button
                                type="button"
                                onClick={() => setConfirmRole(null)}
                                className="h-10 rounded-lg border border-m-border px-4 text-[13px] font-semibold text-m-muted"
                            >
                                취소
                            </button>
                            <button
                                type="button"
                                disabled={busy}
                                onClick={confirmAssign}
                                className="h-10 rounded-lg bg-m-danger px-4 text-[13px] font-semibold text-white disabled:opacity-40"
                            >
                                부여 확정
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
