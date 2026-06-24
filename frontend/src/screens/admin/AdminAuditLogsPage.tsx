'use client';

import { useMemo, useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditLogApi, type AuditAction, type AuditLogListParams } from '../../api/auditLogs';
import Icon from '../../components/ui/Icon';

interface FilterState {
    table_name: string;
    actor: string;
    action: '' | AuditAction;
    start_date: string;
    end_date: string;
}

const initialFilters: FilterState = {
    table_name: '',
    actor: '',
    action: '',
    start_date: '',
    end_date: '',
};

function buildParams(filters: FilterState, page: number): AuditLogListParams {
    const actor = Number(filters.actor);
    return {
        table_name: filters.table_name.trim() || undefined,
        actor: Number.isFinite(actor) && actor > 0 ? actor : undefined,
        action: filters.action || undefined,
        start_at: filters.start_date ? `${filters.start_date}T00:00:00` : undefined,
        end_at: filters.end_date ? `${filters.end_date}T23:59:59` : undefined,
        page,
        page_size: 20,
    };
}

function formatDateTime(value: string): string {
    return new Date(value).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function actionLabel(action: AuditAction): string {
    if (action === 'CREATE') return '생성';
    if (action === 'DELETE') return '삭제';
    return '수정';
}

function JsonBlock({ title, data }: { title: string; data: Record<string, unknown> | null }) {
    return (
        <div className="min-w-0 rounded-xl border border-m-border bg-m-surface-alt p-3">
            <p className="mb-2 text-[12px] font-semibold text-m-muted">{title}</p>
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-[12px] leading-5 text-m-text">
                {data ? JSON.stringify(data, null, 2) : '-'}
            </pre>
        </div>
    );
}

export default function AdminAuditLogsPage() {
    const [filters, setFilters] = useState<FilterState>(initialFilters);
    const [appliedFilters, setAppliedFilters] = useState<FilterState>(initialFilters);
    const [page, setPage] = useState(1);
    const [selectedId, setSelectedId] = useState<number | null>(null);

    const params = useMemo(() => buildParams(appliedFilters, page), [appliedFilters, page]);

    const {
        data,
        isLoading,
        isError,
        error,
    } = useQuery({
        queryKey: ['admin', 'audit-logs', params],
        queryFn: () => auditLogApi.list(params),
    });

    const logs = data?.items ?? [];
    const selected = logs.find((item) => item.id === selectedId) ?? logs[0] ?? null;
    const total = data?.total ?? 0;
    const pageSize = data?.page_size ?? 20;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));

    function applyFilters(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setSelectedId(null);
        setPage(1);
        setAppliedFilters(filters);
    }

    function resetFilters() {
        setFilters(initialFilters);
        setAppliedFilters(initialFilters);
        setSelectedId(null);
        setPage(1);
    }

    return (
        <div className="mx-auto flex h-full max-w-7xl flex-col p-6">
            <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                    <h1 className="text-[22px] font-bold text-m-text">감사 로그</h1>
                    <p className="mt-1 text-[13px] text-m-muted">권한과 휴가 결재 변경 이력을 조회합니다.</p>
                </div>
                <div className="flex h-10 items-center gap-2 rounded-full border border-m-border bg-m-surface px-4 text-[13px] font-semibold text-m-muted">
                    <Icon name="shield" size={16} />
                    {total.toLocaleString('ko-KR')}건
                </div>
            </div>

            {isError && (
                <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
                    {error instanceof Error ? error.message : '감사 로그를 불러오지 못했습니다.'}
                </div>
            )}

            <form
                onSubmit={applyFilters}
                className="mb-5 grid grid-cols-1 gap-2 rounded-2xl border border-m-border bg-m-surface p-4 lg:grid-cols-[minmax(140px,1fr)_120px_130px_140px_140px_96px_96px]"
            >
                <input
                    value={filters.table_name}
                    onChange={(e) => setFilters((prev) => ({ ...prev, table_name: e.target.value }))}
                    placeholder="대상 테이블"
                    className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                />
                <input
                    value={filters.actor}
                    onChange={(e) => setFilters((prev) => ({ ...prev, actor: e.target.value }))}
                    placeholder="행위자 ID"
                    inputMode="numeric"
                    className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                />
                <select
                    value={filters.action}
                    onChange={(e) => setFilters((prev) => ({ ...prev, action: e.target.value as FilterState['action'] }))}
                    className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                >
                    <option value="">전체 액션</option>
                    <option value="CREATE">생성</option>
                    <option value="UPDATE">수정</option>
                    <option value="DELETE">삭제</option>
                </select>
                <input
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => setFilters((prev) => ({ ...prev, start_date: e.target.value }))}
                    className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                />
                <input
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => setFilters((prev) => ({ ...prev, end_date: e.target.value }))}
                    className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                />
                <button type="submit" className="h-10 rounded-lg bg-m-primary text-[13px] font-semibold text-white">
                    검색
                </button>
                <button
                    type="button"
                    onClick={resetFilters}
                    className="h-10 rounded-lg border border-m-border px-3 text-[13px] font-semibold text-m-muted"
                >
                    초기화
                </button>
            </form>

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
                <section className="min-h-0 overflow-x-auto overflow-y-hidden rounded-2xl border border-m-border bg-m-surface">
                    <div className="grid h-10 min-w-[620px] grid-cols-[150px_90px_1fr_90px_110px] items-center border-b border-m-border px-4 text-[12px] font-semibold text-m-muted">
                        <span>일시</span>
                        <span>액션</span>
                        <span>대상</span>
                        <span>행위자</span>
                        <span>IP</span>
                    </div>

                    <div className="max-h-[calc(100vh-312px)] min-h-[320px] min-w-[620px] overflow-y-auto p-2">
                        {isLoading ? (
                            <div className="flex h-72 items-center justify-center text-[13px] text-m-subtle">
                                불러오는 중...
                            </div>
                        ) : logs.length === 0 ? (
                            <div className="flex h-72 items-center justify-center text-[13px] text-m-subtle">
                                조회 결과가 없습니다.
                            </div>
                        ) : (
                            logs.map((log) => (
                                <button
                                    key={log.id}
                                    type="button"
                                    onClick={() => setSelectedId(log.id)}
                                    className={`grid w-full grid-cols-[150px_90px_1fr_90px_110px] items-center gap-0 rounded-xl px-2 py-3 text-left text-[12px] transition-colors ${
                                        selected?.id === log.id ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                                    }`}
                                >
                                    <span className="truncate text-m-muted">{formatDateTime(log.created_at)}</span>
                                    <span className="font-semibold text-m-text">{actionLabel(log.action)}</span>
                                    <span className="min-w-0">
                                        <span className="block truncate font-semibold text-m-text">{log.table_name}</span>
                                        <span className="block truncate text-m-subtle">#{log.record_id} · {log.summary ?? '-'}</span>
                                    </span>
                                    <span className="truncate text-m-muted">{log.actor_user_id ?? '-'}</span>
                                    <span className="truncate text-m-muted">{log.actor_ip ?? '-'}</span>
                                </button>
                            ))
                        )}
                    </div>

                    <div className="flex h-12 min-w-[620px] items-center justify-between border-t border-m-border px-4 text-[12px] text-m-muted">
                        <span>{page} / {totalPages}</span>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                disabled={page <= 1}
                                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                                className="h-8 rounded-lg border border-m-border px-3 font-semibold disabled:opacity-50"
                            >
                                이전
                            </button>
                            <button
                                type="button"
                                disabled={page >= totalPages}
                                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                                className="h-8 rounded-lg border border-m-border px-3 font-semibold disabled:opacity-50"
                            >
                                다음
                            </button>
                        </div>
                    </div>
                </section>

                <aside className="min-h-0 overflow-y-auto rounded-2xl border border-m-border bg-m-surface p-5">
                    {selected ? (
                        <div className="space-y-4">
                            <div>
                                <div className="mb-2 flex items-center justify-between gap-3">
                                    <h2 className="truncate text-[17px] font-bold text-m-text">{selected.summary ?? '감사 로그'}</h2>
                                    <span className="rounded-full bg-m-surface-alt px-2 py-1 text-[11px] font-semibold text-m-muted">
                                        {actionLabel(selected.action)}
                                    </span>
                                </div>
                                <div className="space-y-1 text-[12px] text-m-muted">
                                    <p>{formatDateTime(selected.created_at)}</p>
                                    <p>{selected.table_name} #{selected.record_id}</p>
                                    <p>행위자 {selected.actor_user_id ?? '-'} · {selected.actor_ip ?? '-'}</p>
                                </div>
                            </div>

                            <JsonBlock title="변경 전" data={selected.before_data} />
                            <JsonBlock title="변경 후" data={selected.after_data} />
                        </div>
                    ) : (
                        <div className="flex h-72 flex-col items-center justify-center text-center text-m-subtle">
                            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-m-surface-alt">
                                <Icon name="shield" size={28} />
                            </div>
                            <p className="text-[13px]">감사 로그가 없습니다.</p>
                        </div>
                    )}
                </aside>
            </div>
        </div>
    );
}
