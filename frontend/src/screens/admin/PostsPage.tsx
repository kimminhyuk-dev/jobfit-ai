'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import type { Category, Post, PostCreate, PostUpdate } from '../../api/types';

type ModalMode = 'create' | 'edit';

interface ModalState {
  mode: ModalMode;
  post?: Post;
}

function PostModal({
  modal,
  categories,
  onClose,
}: {
  modal: ModalState;
  categories: Category[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const isEdit = modal.mode === 'edit';
  const post = modal.post;

  const [categoryId, setCategoryId] = useState(
    String(post?.category_id ?? (categories[0]?.category_id ?? ''))
  );
  const [title, setTitle] = useState(post?.title ?? '');
  const [content, setContent] = useState(post?.content ?? '');
  const [error, setError] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: PostCreate) => adminApi.createPost(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'posts'] }); onClose(); },
    onError: (e: { response?: { data?: { message?: string } } }) =>
      setError(e.response?.data?.message ?? '생성에 실패했습니다.'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: PostUpdate) => adminApi.updatePost(post!.post_id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'posts'] }); onClose(); },
    onError: (e: { response?: { data?: { message?: string } } }) =>
      setError(e.response?.data?.message ?? '수정에 실패했습니다.'),
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();
    if (!trimmedTitle || !trimmedContent) {
      setError('제목과 내용은 필수입니다.');
      return;
    }
    if (!categoryId) {
      setError('카테고리를 선택하세요.');
      return;
    }
    if (isEdit) {
      updateMutation.mutate({
        category_id: Number(categoryId),
        title: trimmedTitle,
        content: trimmedContent,
      });
    } else {
      createMutation.mutate({
        category_id: Number(categoryId),
        title: trimmedTitle,
        content: trimmedContent,
      });
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-140 p-6">
        <h2 className="text-[16px] font-bold mb-4" style={{ color: '#0f172a' }}>
          {isEdit ? '게시글 수정' : '게시글 작성'}
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>카테고리 *</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0', background: '#fff' }}
            >
              {categories.map((c) => (
                <option key={c.category_id} value={c.category_id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>제목 *</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="게시글 제목"
            />
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>내용 *</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              maxLength={5000}
              rows={8}
              className="w-full px-3 py-2 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500 resize-y"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="게시글 내용을 입력하세요."
            />
            <p className="text-[11px] mt-0.5 text-right" style={{ color: '#94a3b8' }}>
              {content.length}/5000
            </p>
          </div>

          {error && (
            <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-1">
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
              {isPending ? '저장 중...' : isEdit ? '수정' : '작성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PostsPage() {
  const qc = useQueryClient();
  const [modal, setModal] = useState<ModalState | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Post | null>(null);
  const [filterCategoryId, setFilterCategoryId] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: categories = [] } = useQuery({
    queryKey: ['admin', 'categories'],
    queryFn: adminApi.listCategories,
  });

  const offset = (page - 1) * pageSize;
  const { data: posts = [], isLoading, isError } = useQuery({
    queryKey: ['admin', 'posts', filterCategoryId, offset],
    queryFn: () =>
      adminApi.listPosts({
        offset,
        limit: pageSize,
        ...(filterCategoryId ? { category_id: Number(filterCategoryId) } : {}),
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminApi.deletePost(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'posts'] });
      setDeleteTarget(null);
    },
  });

  const categoryMap = new Map(categories.map((c) => [c.category_id, c.name]));

  const filtered = search
    ? posts.filter((p) => p.title.includes(search))
    : posts;

  const activeCategories = categories.filter((c) => c.is_active);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-bold" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>Q&A 게시글 관리</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#475569' }}>관리자 전용 Q&A 게시글을 관리합니다.</p>
        </div>
        <button
          onClick={() => setModal({ mode: 'create' })}
          disabled={activeCategories.length === 0}
          className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold flex items-center gap-1.5 disabled:opacity-50"
          style={{ background: '#2563eb' }}
        >
          + 게시글 작성
        </button>
      </div>

      <div className="flex items-center gap-3 mb-4">
        <select
          value={filterCategoryId}
          onChange={(e) => { setFilterCategoryId(e.target.value); setPage(1); }}
          className="h-9 px-3 rounded-lg border text-[13px] focus:outline-none"
          style={{ borderColor: '#e2e8f0', background: '#fff', color: '#0f172a', minWidth: 140 }}
        >
          <option value="">전체 카테고리</option>
          {categories.map((c) => (
            <option key={c.category_id} value={c.category_id}>{c.name}</option>
          ))}
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="제목 검색"
          className="h-9 px-3 rounded-lg border text-[13px] focus:outline-none"
          style={{ borderColor: '#e2e8f0', background: '#fff', color: '#0f172a', width: 220 }}
        />
      </div>

      {isLoading && (
        <div className="text-center py-12 text-[13px]" style={{ color: '#94a3b8' }}>
          게시글을 불러오는 중...
        </div>
      )}

      {isError && (
        <div className="text-center py-12 text-[13px] text-red-500">
          게시글을 불러올 수 없습니다.
        </div>
      )}

      {!isLoading && !isError && (
        <>
          <div className="bg-white border rounded-xl overflow-hidden" style={{ borderColor: '#e2e8f0' }}>
            <table className="w-full text-[13px]">
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  {['#', '제목', '카테고리', '날짜', '관리'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-semibold" style={{ color: '#475569' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: '#f1f5f9' }}>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center" style={{ color: '#94a3b8' }}>
                      {search ? '검색 결과가 없습니다.' : '게시글이 없습니다.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((p) => (
                    <tr key={p.post_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-[12px]" style={{ color: '#94a3b8' }}>{p.post_id}</td>
                      <td className="px-4 py-3 font-medium max-w-xs" style={{ color: '#0f172a' }}>
                        <p className="truncate">{p.title}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#eff6ff', color: '#2563eb' }}>
                          {categoryMap.get(p.category_id) ?? `#${p.category_id}`}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-[12px]" style={{ color: '#94a3b8' }}>
                        {new Date(p.created_at).toLocaleDateString('ko-KR')}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => setModal({ mode: 'edit', post: p })}
                            className="text-[12px] font-medium hover:underline"
                            style={{ color: '#2563eb' }}
                          >
                            수정
                          </button>
                          <button
                            onClick={() => setDeleteTarget(p)}
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

          {/* Pagination */}
          <div className="flex items-center justify-between mt-3">
            <p className="text-[12px]" style={{ color: '#94a3b8' }}>
              {filtered.length}개 표시 중
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="h-8 px-3 rounded-lg border text-[12px] font-medium disabled:opacity-40"
                style={{ borderColor: '#e2e8f0', color: '#475569' }}
              >
                이전
              </button>
              <span className="h-8 px-3 flex items-center text-[12px]" style={{ color: '#475569' }}>
                {page}페이지
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={posts.length < pageSize}
                className="h-8 px-3 rounded-lg border text-[12px] font-medium disabled:opacity-40"
                style={{ borderColor: '#e2e8f0', color: '#475569' }}
              >
                다음
              </button>
            </div>
          </div>
        </>
      )}

      {modal && (
        <PostModal
          modal={modal}
          categories={activeCategories}
          onClose={() => setModal(null)}
        />
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-100 p-6">
            <h2 className="text-[16px] font-bold mb-2" style={{ color: '#0f172a' }}>게시글 삭제</h2>
            <p className="text-[13px] mb-4" style={{ color: '#475569' }}>
              <strong className="line-clamp-1">{deleteTarget.title}</strong>
              <br />이 게시글을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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
                onClick={() => deleteMutation.mutate(deleteTarget.post_id)}
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
