'use client';

import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminMenuApi, type AdminMenu, type AdminMenuPayload } from '../../api/menus';
import type { ApiError } from '../../api/types';
import Icon, { type IconName } from '../../components/ui/Icon';

interface MenuFormState {
    parent_id: string;
    menu_name: string;
    menu_url: string;
    icon: string;
    sort_order: number;
    use_yn: boolean;
    required_permission: string;
}

interface MenuNode extends AdminMenu {
    children: MenuNode[];
}

const emptyMenuForm: MenuFormState = {
    parent_id: '',
    menu_name: '',
    menu_url: '',
    icon: 'file',
    sort_order: 0,
    use_yn: true,
    required_permission: '',
};

const iconOptions: IconName[] = [
    'home',
    'user',
    'layers',
    'file',
    'briefcase',
    'grid',
    'calendar',
    'shield',
    'list',
    'settings',
];

const permissionOptions = [
    '',
    'CODE_MANAGE',
    'MENU_MANAGE',
    'AUDIT_VIEW',
    'USER_MANAGE',
    'JOB_MANAGE',
    'LEAVE_REQUEST',
    'LEAVE_APPROVE',
];

function buildMenuTree(menus: AdminMenu[]): MenuNode[] {
    const map = new Map<number, MenuNode>();
    menus.forEach((menu) => {
        map.set(menu.id, { ...menu, children: [] });
    });

    const roots: MenuNode[] = [];
    map.forEach((node) => {
        if (node.parent_id && map.has(node.parent_id)) {
            map.get(node.parent_id)?.children.push(node);
            return;
        }
        roots.push(node);
    });

    const sortNodes = (nodes: MenuNode[]) => {
        nodes.sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
        nodes.forEach((node) => sortNodes(node.children));
    };

    sortNodes(roots);
    return roots;
}

function collectDescendantIds(menu: MenuNode | undefined): Set<number> {
    const ids = new Set<number>();
    const walk = (node: MenuNode) => {
        node.children.forEach((child) => {
            ids.add(child.id);
            walk(child);
        });
    };

    if (menu) {
        walk(menu);
    }
    return ids;
}

function flattenMenuTree(nodes: MenuNode[], depth = 0): Array<MenuNode & { depth: number }> {
    return nodes.flatMap((node) => [
        { ...node, depth },
        ...flattenMenuTree(node.children, depth + 1),
    ]);
}

export default function AdminMenusPage() {
    const queryClient = useQueryClient();
    const [editingMenu, setEditingMenu] = useState<AdminMenu | null>(null);
    const [menuForm, setMenuForm] = useState<MenuFormState>(emptyMenuForm);
    const [error, setError] = useState<string | null>(null);

    const { data: menus = [], isLoading } = useQuery({
        queryKey: ['admin', 'menus', 'list'],
        queryFn: adminMenuApi.list,
    });

    const menuTree = useMemo(() => buildMenuTree(menus), [menus]);
    const flatMenus = useMemo(() => flattenMenuTree(menuTree), [menuTree]);
    const editingNode = useMemo(
        () => flatMenus.find((menu) => menu.id === editingMenu?.id),
        [editingMenu, flatMenus],
    );
    const blockedParentIds = useMemo(() => {
        const ids = collectDescendantIds(editingNode);
        if (editingMenu) {
            ids.add(editingMenu.id);
        }
        return ids;
    }, [editingMenu, editingNode]);

    const invalidateMenus = () => {
        queryClient.invalidateQueries({ queryKey: ['admin', 'menus'] });
    };
    const onError = (err: ApiError) => setError(err.message || '처리에 실패했습니다.');

    const createMutation = useMutation({
        mutationFn: (payload: AdminMenuPayload) => adminMenuApi.create(payload),
        onSuccess: () => {
            setError(null);
            setEditingMenu(null);
            setMenuForm(emptyMenuForm);
            invalidateMenus();
        },
        onError,
    });

    const updateMutation = useMutation({
        mutationFn: ({ menuId, payload }: { menuId: number; payload: AdminMenuPayload }) =>
            adminMenuApi.update(menuId, payload),
        onSuccess: () => {
            setError(null);
            setEditingMenu(null);
            setMenuForm(emptyMenuForm);
            invalidateMenus();
        },
        onError,
    });

    const deleteMutation = useMutation({
        mutationFn: (menuId: number) => adminMenuApi.delete(menuId),
        onSuccess: () => {
            setError(null);
            setEditingMenu(null);
            setMenuForm(emptyMenuForm);
            invalidateMenus();
        },
        onError,
    });

    function startEdit(menu: AdminMenu) {
        setEditingMenu(menu);
        setMenuForm({
            parent_id: menu.parent_id ? String(menu.parent_id) : '',
            menu_name: menu.menu_name,
            menu_url: menu.menu_url ?? '',
            icon: menu.icon ?? 'file',
            sort_order: menu.sort_order,
            use_yn: menu.use_yn,
            required_permission: menu.required_permission ?? '',
        });
    }

    function submitMenu(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const payload: AdminMenuPayload = {
            parent_id: menuForm.parent_id ? Number(menuForm.parent_id) : null,
            menu_name: menuForm.menu_name,
            menu_url: menuForm.menu_url || null,
            icon: menuForm.icon || null,
            sort_order: Number(menuForm.sort_order),
            use_yn: menuForm.use_yn,
            required_permission: menuForm.required_permission || null,
        };

        if (editingMenu) {
            updateMutation.mutate({ menuId: editingMenu.id, payload });
            return;
        }
        createMutation.mutate(payload);
    }

    return (
        <div className="mx-auto flex h-full max-w-7xl flex-col p-6">
            <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                    <h1 className="text-[22px] font-bold text-m-text">메뉴 관리</h1>
                    <p className="mt-1 text-[13px] text-m-muted">관리자 사이드바에 노출할 메뉴와 권한을 관리합니다.</p>
                </div>
                <div className="flex h-10 items-center gap-2 rounded-full border border-m-border bg-m-surface px-4 text-[13px] font-semibold text-m-muted">
                    <Icon name="list" size={16} />
                    {menus.length.toLocaleString('ko-KR')}개 메뉴
                </div>
            </div>

            {error && (
                <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
                    {error}
                </div>
            )}

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <section className="min-h-0 overflow-hidden rounded-2xl border border-m-border bg-m-surface">
                    <div className="flex h-11 items-center justify-between border-b border-m-border px-4">
                        <p className="text-[13px] font-semibold text-m-text">메뉴 트리</p>
                        <button
                            type="button"
                            onClick={() => {
                                setEditingMenu(null);
                                setMenuForm(emptyMenuForm);
                            }}
                            className="flex h-8 items-center gap-1 rounded-lg border border-m-border px-2 text-[12px] font-semibold text-m-muted"
                        >
                            <Icon name="plus" size={14} />
                            신규
                        </button>
                    </div>

                    <div className="max-h-[calc(100vh-238px)] min-h-[360px] overflow-y-auto p-3">
                        {isLoading ? (
                            <div className="flex h-64 items-center justify-center text-[13px] text-m-subtle">불러오는 중...</div>
                        ) : menuTree.length === 0 ? (
                            <div className="flex h-64 items-center justify-center text-[13px] text-m-subtle">메뉴가 없습니다.</div>
                        ) : (
                            menuTree.map((menu) => (
                                <MenuTreeItem
                                    key={menu.id}
                                    menu={menu}
                                    depth={0}
                                    selectedId={editingMenu?.id ?? null}
                                    onSelect={startEdit}
                                />
                            ))
                        )}
                    </div>
                </section>

                <aside className="min-h-0 overflow-y-auto rounded-2xl border border-m-border bg-m-surface p-5">
                    <div className="mb-4 flex items-center justify-between gap-3">
                        <h2 className="text-[17px] font-bold text-m-text">{editingMenu ? '메뉴 수정' : '메뉴 추가'}</h2>
                        {editingMenu && (
                            <button
                                type="button"
                                onClick={() => {
                                    setEditingMenu(null);
                                    setMenuForm(emptyMenuForm);
                                }}
                                className="h-8 rounded-lg border border-m-border px-3 text-[12px] font-semibold text-m-muted"
                            >
                                취소
                            </button>
                        )}
                    </div>

                    <form onSubmit={submitMenu} className="space-y-3">
                        <label className="block">
                            <span className="mb-1 block text-[12px] font-semibold text-m-muted">상위 메뉴</span>
                            <select
                                value={menuForm.parent_id}
                                onChange={(e) => setMenuForm((prev) => ({ ...prev, parent_id: e.target.value }))}
                                className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                            >
                                <option value="">최상위</option>
                                {flatMenus
                                    .filter((menu) => !blockedParentIds.has(menu.id))
                                    .map((menu) => (
                                        <option key={menu.id} value={menu.id}>
                                            {'　'.repeat(menu.depth)}{menu.menu_name}
                                        </option>
                                    ))}
                            </select>
                        </label>

                        <label className="block">
                            <span className="mb-1 block text-[12px] font-semibold text-m-muted">메뉴명</span>
                            <input
                                required
                                value={menuForm.menu_name}
                                onChange={(e) => setMenuForm((prev) => ({ ...prev, menu_name: e.target.value }))}
                                className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                            />
                        </label>

                        <label className="block">
                            <span className="mb-1 block text-[12px] font-semibold text-m-muted">주소</span>
                            <input
                                value={menuForm.menu_url}
                                onChange={(e) => setMenuForm((prev) => ({ ...prev, menu_url: e.target.value }))}
                                placeholder="/admin/example"
                                className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                            />
                        </label>

                        <div className="grid grid-cols-2 gap-3">
                            <label className="block">
                                <span className="mb-1 block text-[12px] font-semibold text-m-muted">아이콘</span>
                                <select
                                    value={menuForm.icon}
                                    onChange={(e) => setMenuForm((prev) => ({ ...prev, icon: e.target.value }))}
                                    className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                                >
                                    {iconOptions.map((icon) => (
                                        <option key={icon} value={icon}>{icon}</option>
                                    ))}
                                </select>
                            </label>
                            <label className="block">
                                <span className="mb-1 block text-[12px] font-semibold text-m-muted">정렬</span>
                                <input
                                    type="number"
                                    value={menuForm.sort_order}
                                    onChange={(e) => setMenuForm((prev) => ({ ...prev, sort_order: Number(e.target.value) }))}
                                    className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                                />
                            </label>
                        </div>

                        <label className="block">
                            <span className="mb-1 block text-[12px] font-semibold text-m-muted">필요 권한</span>
                            <select
                                value={menuForm.required_permission}
                                onChange={(e) => setMenuForm((prev) => ({ ...prev, required_permission: e.target.value }))}
                                className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] outline-none focus:border-m-primary"
                            >
                                {permissionOptions.map((permission) => (
                                    <option key={permission || 'none'} value={permission}>
                                        {permission || '권한 없음'}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label className="flex h-10 items-center justify-between rounded-lg border border-m-border bg-m-surface-alt px-3">
                            <span className="text-[13px] font-semibold text-m-muted">사용 여부</span>
                            <input
                                type="checkbox"
                                checked={menuForm.use_yn}
                                onChange={(e) => setMenuForm((prev) => ({ ...prev, use_yn: e.target.checked }))}
                                className="h-4 w-4 accent-m-primary"
                            />
                        </label>

                        <div className="flex gap-2 pt-2">
                            <button
                                type="submit"
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className="h-10 flex-1 rounded-lg bg-m-primary text-[13px] font-semibold text-white disabled:opacity-50"
                            >
                                {editingMenu ? '수정' : '추가'}
                            </button>
                            {editingMenu && (
                                <button
                                    type="button"
                                    disabled={deleteMutation.isPending}
                                    onClick={() => {
                                        if (window.confirm('선택한 메뉴를 삭제하시겠습니까?')) {
                                            deleteMutation.mutate(editingMenu.id);
                                        }
                                    }}
                                    className="h-10 rounded-lg border border-m-danger px-3 text-[13px] font-semibold text-m-danger disabled:opacity-50"
                                >
                                    삭제
                                </button>
                            )}
                        </div>
                    </form>
                </aside>
            </div>
        </div>
    );
}

function MenuTreeItem({
    menu,
    depth,
    selectedId,
    onSelect,
}: {
    menu: MenuNode;
    depth: number;
    selectedId: number | null;
    onSelect: (menu: AdminMenu) => void;
}) {
    const iconName = iconOptions.includes((menu.icon ?? '') as IconName) ? (menu.icon as IconName) : 'file';
    const selected = selectedId === menu.id;

    return (
        <div>
            <button
                type="button"
                onClick={() => onSelect(menu)}
                className={`mb-1 grid w-full grid-cols-[minmax(0,1fr)_120px_84px] items-center rounded-xl py-3 pr-3 text-left transition-colors ${
                    selected ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                }`}
                style={{ paddingLeft: 12 + depth * 18 }}
            >
                <span className="flex min-w-0 items-center gap-2">
                    <Icon name={iconName} size={16} />
                    <span className="min-w-0">
                        <span className="block truncate text-[13px] font-semibold text-m-text">{menu.menu_name}</span>
                        <span className="block truncate text-[11px] text-m-subtle">{menu.menu_url ?? '-'}</span>
                    </span>
                </span>
                <span className="truncate text-[12px] text-m-muted">{menu.required_permission ?? '권한 없음'}</span>
                <span className={`text-right text-[11px] font-semibold ${menu.use_yn ? 'text-m-primary' : 'text-m-subtle'}`}>
                    {menu.use_yn ? '사용' : '중지'} · {menu.sort_order}
                </span>
            </button>
            {menu.children.map((child) => (
                <MenuTreeItem
                    key={child.id}
                    menu={child}
                    depth={depth + 1}
                    selectedId={selectedId}
                    onSelect={onSelect}
                />
            ))}
        </div>
    );
}
