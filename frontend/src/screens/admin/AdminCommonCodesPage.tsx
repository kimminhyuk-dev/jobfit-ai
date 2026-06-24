'use client';

import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    commonCodeApi,
    type CommonCodeGroup,
    type CommonCodeGroupPayload,
    type CommonCodeItem,
    type CommonCodeItemPayload,
} from '../../api/commonCodes';
import type { ApiError } from '../../api/types';
import Icon from '../../components/ui/Icon';

const emptyGroupForm = {
    group_code: '',
    group_name: '',
    description: '',
    sort_order: 0,
    use_yn: true,
    category_code: 'ADM',
};

const emptyItemForm = {
    code: '',
    code_name: '',
    sort_order: 0,
    use_yn: true,
    attr1: '',
    attr2: '',
};

export default function AdminCommonCodesPage() {
    const queryClient = useQueryClient();
    const [selectedGroupCode, setSelectedGroupCode] = useState<string | null>(null);
    const [editingGroup, setEditingGroup] = useState<CommonCodeGroup | null>(null);
    const [editingItem, setEditingItem] = useState<CommonCodeItem | null>(null);
    const [groupForm, setGroupForm] = useState(emptyGroupForm);
    const [itemForm, setItemForm] = useState(emptyItemForm);
    const [error, setError] = useState<string | null>(null);

    const { data: groups = [], isLoading: groupsLoading } = useQuery({
        queryKey: ['admin', 'common-code-groups'],
        queryFn: commonCodeApi.listGroups,
    });

    const activeGroup = useMemo(
        () => groups.find((group) => group.group_code === selectedGroupCode) ?? groups[0] ?? null,
        [groups, selectedGroupCode],
    );

    const { data: items = [], isLoading: itemsLoading } = useQuery({
        queryKey: ['admin', 'common-code-items', activeGroup?.group_code],
        queryFn: () => commonCodeApi.listItems(activeGroup?.group_code ?? ''),
        enabled: Boolean(activeGroup),
    });

    const invalidateGroups = () => queryClient.invalidateQueries({ queryKey: ['admin', 'common-code-groups'] });
    const invalidateItems = () => queryClient.invalidateQueries({ queryKey: ['admin', 'common-code-items'] });
    const onError = (err: ApiError) => setError(err.message || '처리에 실패했습니다.');

    const createGroupMutation = useMutation({
        mutationFn: (payload: CommonCodeGroupPayload) => commonCodeApi.createGroup(payload),
        onSuccess: (group) => {
            setError(null);
            setGroupForm(emptyGroupForm);
            setEditingGroup(null);
            setSelectedGroupCode(group.group_code);
            invalidateGroups();
        },
        onError,
    });

    const updateGroupMutation = useMutation({
        mutationFn: ({ groupCode, payload }: { groupCode: string; payload: CommonCodeGroupPayload }) =>
            commonCodeApi.updateGroup(groupCode, payload),
        onSuccess: () => {
            setError(null);
            setGroupForm(emptyGroupForm);
            setEditingGroup(null);
            invalidateGroups();
        },
        onError,
    });

    const deleteGroupMutation = useMutation({
        mutationFn: (groupCode: string) => commonCodeApi.deleteGroup(groupCode),
        onSuccess: () => {
            setError(null);
            setSelectedGroupCode(null);
            invalidateGroups();
        },
        onError,
    });

    const createItemMutation = useMutation({
        mutationFn: ({ groupCode, payload }: { groupCode: string; payload: CommonCodeItemPayload }) =>
            commonCodeApi.createItem(groupCode, payload),
        onSuccess: () => {
            setError(null);
            setItemForm(emptyItemForm);
            setEditingItem(null);
            invalidateItems();
        },
        onError,
    });

    const updateItemMutation = useMutation({
        mutationFn: ({ groupCode, code, payload }: { groupCode: string; code: string; payload: CommonCodeItemPayload }) =>
            commonCodeApi.updateItem(groupCode, code, payload),
        onSuccess: () => {
            setError(null);
            setItemForm(emptyItemForm);
            setEditingItem(null);
            invalidateItems();
        },
        onError,
    });

    const deleteItemMutation = useMutation({
        mutationFn: ({ groupCode, code }: { groupCode: string; code: string }) => commonCodeApi.deleteItem(groupCode, code),
        onSuccess: () => {
            setError(null);
            invalidateItems();
        },
        onError,
    });

    function startEditGroup(group: CommonCodeGroup) {
        setEditingGroup(group);
        setGroupForm({
            group_code: group.group_code,
            group_name: group.group_name,
            description: group.description ?? '',
            sort_order: group.sort_order,
            use_yn: group.use_yn,
            category_code: group.category_code,
        });
    }

    function startEditItem(item: CommonCodeItem) {
        setEditingItem(item);
        setItemForm({
            code: item.code,
            code_name: item.code_name,
            sort_order: item.sort_order,
            use_yn: item.use_yn,
            attr1: item.attr1 ?? '',
            attr2: item.attr2 ?? '',
        });
    }

    function submitGroup(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const payload: CommonCodeGroupPayload = {
            group_name: groupForm.group_name,
            description: groupForm.description || null,
            sort_order: Number(groupForm.sort_order),
            use_yn: groupForm.use_yn,
            category_code: groupForm.category_code || 'ADM',
        };
        if (editingGroup) {
            updateGroupMutation.mutate({ groupCode: editingGroup.group_code, payload });
        } else {
            createGroupMutation.mutate({ ...payload, group_code: groupForm.group_code });
        }
    }

    function submitItem(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        if (!activeGroup) return;
        const payload: CommonCodeItemPayload = {
            code_name: itemForm.code_name,
            sort_order: Number(itemForm.sort_order),
            use_yn: itemForm.use_yn,
            attr1: itemForm.attr1 || null,
            attr2: itemForm.attr2 || null,
        };
        if (editingItem) {
            updateItemMutation.mutate({ groupCode: activeGroup.group_code, code: editingItem.code, payload });
        } else {
            createItemMutation.mutate({ groupCode: activeGroup.group_code, payload: { ...payload, code: itemForm.code } });
        }
    }

    return (
        <div className="mx-auto flex h-full max-w-7xl flex-col p-6">
            <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                    <h1 className="text-[22px] font-bold text-m-text">공통코드 관리</h1>
                    <p className="mt-1 text-[13px] text-m-muted">업무 구분값을 그룹과 상세 코드로 관리합니다.</p>
                </div>
                <div className="flex h-10 items-center gap-2 rounded-full border border-m-border bg-m-surface px-4 text-[13px] font-semibold text-m-muted">
                    <Icon name="layers" size={16} />
                    {groups.length.toLocaleString('ko-KR')}개 그룹
                </div>
            </div>

            {error && (
                <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
                    {error}
                </div>
            )}

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 xl:grid-cols-[minmax(320px,0.75fr)_minmax(0,1.25fr)]">
                <section className="min-h-0 overflow-hidden rounded-2xl border border-m-border bg-m-surface">
                    <div className="flex h-11 items-center justify-between border-b border-m-border px-4">
                        <p className="text-[13px] font-semibold text-m-text">그룹</p>
                        <button
                            type="button"
                            onClick={() => {
                                setEditingGroup(null);
                                setGroupForm(emptyGroupForm);
                            }}
                            className="flex h-8 items-center gap-1 rounded-lg border border-m-border px-2 text-[12px] font-semibold text-m-muted"
                        >
                            <Icon name="plus" size={14} />
                            신규
                        </button>
                    </div>
                    <div className="max-h-[calc(100vh-238px)] min-h-[260px] overflow-y-auto p-2">
                        {groupsLoading ? (
                            <div className="flex h-48 items-center justify-center text-[13px] text-m-subtle">불러오는 중...</div>
                        ) : groups.length === 0 ? (
                            <div className="flex h-48 items-center justify-center text-[13px] text-m-subtle">그룹이 없습니다.</div>
                        ) : (
                            groups.map((group) => (
                                <button
                                    key={group.group_code}
                                    type="button"
                                    onClick={() => {
                                        setSelectedGroupCode(group.group_code);
                                        setEditingItem(null);
                                        setItemForm(emptyItemForm);
                                    }}
                                    className={`mb-1 w-full rounded-xl p-3 text-left transition-colors ${
                                        activeGroup?.group_code === group.group_code ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                                    }`}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="truncate text-[13px] font-semibold text-m-text">{group.group_name}</p>
                                        <span className={`text-[11px] font-semibold ${group.use_yn ? 'text-m-primary' : 'text-m-subtle'}`}>
                                            {group.use_yn ? '사용' : '중지'}
                                        </span>
                                    </div>
                                    <p className="mt-1 text-[12px] text-m-muted">{group.group_code}</p>
                                    <p className="truncate text-[11px] text-m-subtle">{group.description ?? '-'}</p>
                                </button>
                            ))
                        )}
                    </div>
                </section>

                <section className="grid min-h-0 grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_330px]">
                    <div className="min-h-0 overflow-hidden rounded-2xl border border-m-border bg-m-surface">
                        <div className="flex h-11 items-center justify-between border-b border-m-border px-4">
                            <p className="text-[13px] font-semibold text-m-text">
                                {activeGroup ? `${activeGroup.group_name} 상세 코드` : '상세 코드'}
                            </p>
                            {activeGroup && (
                                <button
                                    type="button"
                                    onClick={() => {
                                        setEditingItem(null);
                                        setItemForm(emptyItemForm);
                                    }}
                                    className="flex h-8 items-center gap-1 rounded-lg border border-m-border px-2 text-[12px] font-semibold text-m-muted"
                                >
                                    <Icon name="plus" size={14} />
                                    코드
                                </button>
                            )}
                        </div>
                        <div className="max-h-[calc(100vh-238px)] min-h-[260px] overflow-x-auto p-2">
                            <div className="min-w-[620px]">
                                <div className="grid h-9 grid-cols-[110px_1fr_70px_70px_90px] items-center px-2 text-[12px] font-semibold text-m-muted">
                                    <span>코드</span>
                                    <span>코드명</span>
                                    <span>순서</span>
                                    <span>사용</span>
                                    <span>관리</span>
                                </div>
                                {itemsLoading ? (
                                    <div className="flex h-48 items-center justify-center text-[13px] text-m-subtle">불러오는 중...</div>
                                ) : items.length === 0 ? (
                                    <div className="flex h-48 items-center justify-center text-[13px] text-m-subtle">상세 코드가 없습니다.</div>
                                ) : (
                                    items.map((item) => (
                                        <div
                                            key={item.id}
                                            className="grid grid-cols-[110px_1fr_70px_70px_90px] items-center rounded-xl px-2 py-2 text-[12px] hover:bg-m-surface-alt"
                                        >
                                            <span className="font-semibold text-m-text">{item.code}</span>
                                            <span className="truncate text-m-muted">{item.code_name}</span>
                                            <span className="text-m-muted">{item.sort_order}</span>
                                            <span className={item.use_yn ? 'text-m-primary' : 'text-m-subtle'}>{item.use_yn ? '사용' : '중지'}</span>
                                            <span className="flex gap-1">
                                                <button
                                                    type="button"
                                                    onClick={() => startEditItem(item)}
                                                    className="h-7 rounded-lg border border-m-border px-2 font-semibold text-m-muted"
                                                >
                                                    수정
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        if (window.confirm('상세 코드를 삭제할까요?') && activeGroup) {
                                                            deleteItemMutation.mutate({ groupCode: activeGroup.group_code, code: item.code });
                                                        }
                                                    }}
                                                    className="h-7 rounded-lg border border-m-danger/30 px-2 font-semibold text-m-danger"
                                                >
                                                    삭제
                                                </button>
                                            </span>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                    <aside className="space-y-4">
                        <CodeGroupForm
                            form={groupForm}
                            editingGroup={editingGroup}
                            onChange={setGroupForm}
                            onSubmit={submitGroup}
                            onCancel={() => {
                                setEditingGroup(null);
                                setGroupForm(emptyGroupForm);
                            }}
                            onEditActive={() => activeGroup && startEditGroup(activeGroup)}
                            onDeleteActive={() => {
                                if (activeGroup && window.confirm('그룹을 삭제할까요?')) {
                                    deleteGroupMutation.mutate(activeGroup.group_code);
                                }
                            }}
                            hasActiveGroup={Boolean(activeGroup)}
                        />
                        <CodeItemForm
                            form={itemForm}
                            editingItem={editingItem}
                            disabled={!activeGroup}
                            onChange={setItemForm}
                            onSubmit={submitItem}
                            onCancel={() => {
                                setEditingItem(null);
                                setItemForm(emptyItemForm);
                            }}
                        />
                    </aside>
                </section>
            </div>
        </div>
    );
}

function CodeGroupForm({
    form,
    editingGroup,
    hasActiveGroup,
    onChange,
    onSubmit,
    onCancel,
    onEditActive,
    onDeleteActive,
}: {
    form: typeof emptyGroupForm;
    editingGroup: CommonCodeGroup | null;
    hasActiveGroup: boolean;
    onChange: (form: typeof emptyGroupForm) => void;
    onSubmit: (e: FormEvent<HTMLFormElement>) => void;
    onCancel: () => void;
    onEditActive: () => void;
    onDeleteActive: () => void;
}) {
    return (
        <form onSubmit={onSubmit} className="rounded-2xl border border-m-border bg-m-surface p-4">
            <div className="mb-3 flex items-center justify-between gap-2">
                <h2 className="text-[15px] font-bold text-m-text">{editingGroup ? '그룹 수정' : '그룹 생성'}</h2>
                <div className="flex gap-1">
                    <button type="button" disabled={!hasActiveGroup} onClick={onEditActive} className="h-7 rounded-lg border border-m-border px-2 text-[12px] font-semibold text-m-muted disabled:opacity-50">
                        선택 수정
                    </button>
                    <button type="button" disabled={!hasActiveGroup} onClick={onDeleteActive} className="h-7 rounded-lg border border-m-danger/30 px-2 text-[12px] font-semibold text-m-danger disabled:opacity-50">
                        삭제
                    </button>
                </div>
            </div>
            <div className="space-y-2">
                <input value={form.group_code} disabled={Boolean(editingGroup)} onChange={(e) => onChange({ ...form, group_code: e.target.value.toUpperCase() })} placeholder="그룹 코드" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
                <input value={form.group_name} onChange={(e) => onChange({ ...form, group_name: e.target.value })} placeholder="그룹명" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary" />
                <input value={form.description} onChange={(e) => onChange({ ...form, description: e.target.value })} placeholder="설명" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary" />
                <div className="grid grid-cols-2 gap-2">
                    <input type="number" value={form.sort_order} onChange={(e) => onChange({ ...form, sort_order: Number(e.target.value) })} placeholder="정렬" className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary" />
                    <label className="flex h-10 items-center gap-2 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] text-m-muted">
                        <input type="checkbox" checked={form.use_yn} onChange={(e) => onChange({ ...form, use_yn: e.target.checked })} />
                        사용
                    </label>
                </div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
                <button type="submit" className="h-10 rounded-lg bg-m-primary text-[13px] font-semibold text-white">
                    저장
                </button>
                <button type="button" onClick={onCancel} className="h-10 rounded-lg border border-m-border text-[13px] font-semibold text-m-muted">
                    취소
                </button>
            </div>
        </form>
    );
}

function CodeItemForm({
    form,
    editingItem,
    disabled,
    onChange,
    onSubmit,
    onCancel,
}: {
    form: typeof emptyItemForm;
    editingItem: CommonCodeItem | null;
    disabled: boolean;
    onChange: (form: typeof emptyItemForm) => void;
    onSubmit: (e: FormEvent<HTMLFormElement>) => void;
    onCancel: () => void;
}) {
    return (
        <form onSubmit={onSubmit} className="rounded-2xl border border-m-border bg-m-surface p-4">
            <h2 className="mb-3 text-[15px] font-bold text-m-text">{editingItem ? '상세 코드 수정' : '상세 코드 생성'}</h2>
            <div className="space-y-2">
                <input disabled={disabled || Boolean(editingItem)} value={form.code} onChange={(e) => onChange({ ...form, code: e.target.value.toUpperCase() })} placeholder="코드" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
                <input disabled={disabled} value={form.code_name} onChange={(e) => onChange({ ...form, code_name: e.target.value })} placeholder="코드명" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
                <div className="grid grid-cols-2 gap-2">
                    <input disabled={disabled} type="number" value={form.sort_order} onChange={(e) => onChange({ ...form, sort_order: Number(e.target.value) })} placeholder="정렬" className="h-10 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
                    <label className="flex h-10 items-center gap-2 rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] text-m-muted">
                        <input disabled={disabled} type="checkbox" checked={form.use_yn} onChange={(e) => onChange({ ...form, use_yn: e.target.checked })} />
                        사용
                    </label>
                </div>
                <input disabled={disabled} value={form.attr1} onChange={(e) => onChange({ ...form, attr1: e.target.value })} placeholder="속성 1" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
                <input disabled={disabled} value={form.attr2} onChange={(e) => onChange({ ...form, attr2: e.target.value })} placeholder="속성 2" className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary disabled:opacity-60" />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
                <button type="submit" disabled={disabled} className="h-10 rounded-lg bg-m-primary text-[13px] font-semibold text-white disabled:opacity-50">
                    저장
                </button>
                <button type="button" onClick={onCancel} className="h-10 rounded-lg border border-m-border text-[13px] font-semibold text-m-muted">
                    취소
                </button>
            </div>
        </form>
    );
}
