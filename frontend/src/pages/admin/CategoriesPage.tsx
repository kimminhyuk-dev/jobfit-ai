import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import type { Category, CategoryCreate, CategoryUpdate } from '../../api/types';

type ModalMode = 'create' | 'edit';

interface ModalState {
  mode: ModalMode;
  category?: Category;
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');
}

function CategoryModal({
  modal,
  onClose,
}: {
  modal: ModalState;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const isEdit = modal.mode === 'edit';
  const cat = modal.category;

  const [name, setName] = useState(cat?.name ?? '');
  const [slug, setSlug] = useState(cat?.slug ?? '');
  const [description, setDescription] = useState(cat?.description ?? '');
  const [sortOrder, setSortOrder] = useState(String(cat?.sort_order ?? 0));
  const [isActive, setIsActive] = useState(cat?.is_active ?? true);
  const [error, setError] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: CategoryCreate) => adminApi.createCategory(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'categories'] }); onClose(); },
    onError: (e: { response?: { data?: { message?: string } } }) =>
      setError(e.response?.data?.message ?? '생성에 실패했습니다.'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: CategoryUpdate) => adminApi.updateCategory(cat!.category_id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'categories'] }); onClose(); },
    onError: (e: { response?: { data?: { message?: string } } }) =>
      setError(e.response?.data?.message ?? '수정에 실패했습니다.'),
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  function handleNameChange(value: string) {
    setName(value);
    if (!isEdit) setSlug(slugify(value));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const data = {
      name: name.trim(),
      slug: slug.trim(),
      description: description.trim() || undefined,
      sort_order: Number(sortOrder) || 0,
      is_active: isActive,
    };
    if (!data.name || !data.slug) { setError('이름과 slug는 필수입니다.'); return; }
    if (isEdit) updateMutation.mutate(data);
    else createMutation.mutate(data as CategoryCreate);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-120 p-6">
        <h2 className="text-[16px] font-bold mb-4" style={{ color: '#0f172a' }}>
          {isEdit ? '카테고리 수정' : '카테고리 추가'}
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>이름 *</label>
            <input
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="예: 프론트엔드"
            />
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>Slug *</label>
            <input
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500 font-mono"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="예: frontend"
            />
            <p className="text-[11px] mt-1" style={{ color: '#94a3b8' }}>영소문자·숫자·하이픈만 사용</p>
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>설명</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500 resize-none"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="카테고리 설명 (선택)"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>정렬 순서</label>
              <input
                type="number"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                min={0}
                className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
                style={{ borderColor: '#e2e8f0' }}
              />
            </div>
            <div className="flex items-end pb-0.5">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded"
                />
                <span className="text-[13px]" style={{ color: '#475569' }}>활성</span>
              </label>
            </div>
          </div>

          {error && (
            <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="h-9 px-4 rounded-lg text-[13px] font-medium border"
              style={{ borderColor: '#e2e8f0', color: '#475569' }}
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold disabled:opacity-50"
              style={{ background: '#2563eb' }}
            >
              {isPending ? '저장 중...' : isEdit ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CategoriesPage() {
  const qc = useQueryClient();
  const [modal, setModal] = useState<ModalState | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);

  const { data: categories = [], isLoading, isError } = useQuery({
    queryKey: ['admin', 'categories'],
    queryFn: adminApi.listCategories,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminApi.deleteCategory(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'categories'] });
      setDeleteTarget(null);
    },
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-bold" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>카테고리 관리</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#475569' }}>Q&A 게시글을 분류하는 카테고리를 관리합니다.</p>
        </div>
        <button
          onClick={() => setModal({ mode: 'create' })}
          className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold flex items-center gap-1.5"
          style={{ background: '#2563eb' }}
        >
          + 카테고리 추가
        </button>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-[13px]" style={{ color: '#94a3b8' }}>
          카테고리를 불러오는 중...
        </div>
      )}

      {isError && (
        <div className="text-center py-12 text-[13px] text-red-500">
          카테고리를 불러올 수 없습니다.
        </div>
      )}

      {!isLoading && !isError && (
        <div className="bg-white border rounded-xl overflow-hidden" style={{ borderColor: '#e2e8f0' }}>
          <table className="w-full text-[13px]">
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                {['이름', 'Slug', '설명', '순서', '상태', '관리'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-semibold" style={{ color: '#475569' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y" style={{ borderColor: '#f1f5f9' }}>
              {categories.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center" style={{ color: '#94a3b8' }}>
                    카테고리가 없습니다. 추가해 보세요.
                  </td>
                </tr>
              ) : (
                categories.map((c) => (
                  <tr key={c.category_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-semibold" style={{ color: '#0f172a' }}>{c.name}</td>
                    <td className="px-4 py-3 font-mono text-[12px]" style={{ color: '#64748b' }}>{c.slug}</td>
                    <td className="px-4 py-3 max-w-60" style={{ color: '#475569' }}>
                      <p className="truncate">{c.description ?? '-'}</p>
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-center" style={{ color: '#0f172a' }}>{c.sort_order}</td>
                    <td className="px-4 py-3">
                      <span
                        className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                        style={c.is_active
                          ? { background: '#f0fdf4', color: '#16a34a' }
                          : { background: '#f1f5f9', color: '#94a3b8' }
                        }
                      >
                        {c.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => setModal({ mode: 'edit', category: c })}
                          className="text-[12px] font-medium hover:underline"
                          style={{ color: '#2563eb' }}
                        >
                          수정
                        </button>
                        <button
                          onClick={() => setDeleteTarget(c)}
                          className="text-[12px] font-medium hover:underline"
                          style={{ color: '#dc2626' }}
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <CategoryModal modal={modal} onClose={() => setModal(null)} />
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-100 p-6">
            <h2 className="text-[16px] font-bold mb-2" style={{ color: '#0f172a' }}>카테고리 삭제</h2>
            <p className="text-[13px] mb-4" style={{ color: '#475569' }}>
              <strong>{deleteTarget.name}</strong> 카테고리를 삭제하시겠습니까?
              <br />이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteTarget(null)}
                className="h-9 px-4 rounded-lg text-[13px] font-medium border"
                style={{ borderColor: '#e2e8f0', color: '#475569' }}
              >
                취소
              </button>
              <button
                onClick={() => deleteMutation.mutate(deleteTarget.category_id)}
                disabled={deleteMutation.isPending}
                className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold disabled:opacity-50"
                style={{ background: '#dc2626' }}
              >
                {deleteMutation.isPending ? '삭제 중...' : '삭제'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
