'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi, type AdminUserListParams } from '../../api/admin';
import Icon from '../../components/ui/Icon';
import ResumeParsedDataEditor from '../../components/resume/ResumeParsedDataEditor';
import type { AdminUser, ApiError, Resume, ResumeUpdatePayload } from '../../api/types';

type RoleFilter = 'USER' | 'COMPANY' | 'ADMIN';

interface SearchState {
  q: string;
  admin_identifier: string;
  admin_level: '' | 'A' | 'B' | 'C';
  name: string;
  birth_date: string;
  company_name: string;
  business_number: string;
  representative_name: string;
}

const ROLE_TABS: { role: RoleFilter; label: string; icon: 'user' | 'building' | 'shield' }[] = [
  { role: 'USER', label: '일반회원', icon: 'user' },
  { role: 'COMPANY', label: '기업회원', icon: 'building' },
  { role: 'ADMIN', label: '관리자', icon: 'shield' },
];

const initialSearch: SearchState = {
  q: '',
  admin_identifier: '',
  admin_level: '',
  name: '',
  birth_date: '',
  company_name: '',
  business_number: '',
  representative_name: '',
};

function buildParams(role: RoleFilter, search: SearchState): AdminUserListParams {
  return {
    role,
    limit: 500,
    q: search.q.trim(),
    admin_identifier: role === 'ADMIN' ? search.admin_identifier.trim() : undefined,
    admin_level: role === 'ADMIN' ? search.admin_level : undefined,
    name: role === 'USER' ? search.name.trim() : undefined,
    birth_date: role === 'USER' ? search.birth_date.trim() : undefined,
    company_name: role === 'COMPANY' ? search.company_name.trim() : undefined,
    business_number: role === 'COMPANY' ? search.business_number.trim() : undefined,
    representative_name: role === 'COMPANY' ? search.representative_name.trim() : undefined,
  };
}

function roleLabel(role: string): string {
  if (role === 'ADMIN') return '관리자';
  if (role === 'COMPANY') return '기업회원';
  return '일반회원';
}

function displayName(user: AdminUser | undefined | null): string {
  if (!user) return '-';
  if (user.role === 'COMPANY') return user.company?.company_name ?? user.name ?? '기업회원';
  return user.name ?? user.email;
}

function valueOrDash(value: string | null | undefined): string {
  return value && value.trim() ? value : '-';
}

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`;
  return `${(size / 1024 / 1024).toFixed(1)}MB`;
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [role, setRole] = useState<RoleFilter>('USER');
  const [search, setSearch] = useState<SearchState>(initialSearch);
  const [appliedSearch, setAppliedSearch] = useState<SearchState>(initialSearch);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const listParams = useMemo(() => buildParams(role, appliedSearch), [role, appliedSearch]);

  const {
    data: users = [],
    isLoading: isListLoading,
    isError: isListError,
    error: listError,
  } = useQuery({
    queryKey: ['admin', 'users', listParams],
    queryFn: () => adminApi.listUsers(listParams),
  });

  const { data: userDetail, isLoading: isDetailLoading } = useQuery({
    queryKey: ['admin', 'user', selectedUserId],
    queryFn: () => adminApi.getUserDetail(selectedUserId as number),
    enabled: selectedUserId !== null,
  });

  const { data: resumeDetail } = useQuery({
    queryKey: ['admin', 'resume', selectedResumeId],
    queryFn: () => adminApi.getResumeDetail(selectedResumeId as number),
    enabled: selectedResumeId !== null,
  });

  const updateMutation = useMutation<Resume, ApiError, { resumeId: number; data: ResumeUpdatePayload }>({
    mutationFn: ({ resumeId, data }) => adminApi.updateResumeDetail(resumeId, data),
    onSuccess: (resume) => {
      setError(null);
      queryClient.setQueryData(['admin', 'resume', resume.resume_id], resume);
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', selectedUserId] });
    },
    onError: (err: ApiError) => setError(err.message || '이력서 수정에 실패했습니다.'),
  });

  const {
    data: previewBlob,
    isFetching: isPreviewLoading,
    isError: isPreviewError,
  } = useQuery({
    queryKey: ['admin', 'resume-file', selectedResumeId],
    queryFn: () => adminApi.getResumeFileBlob(selectedResumeId as number),
    enabled: selectedResumeId !== null,
  });

  const previewUrl = useMemo(() => {
    if (!previewBlob) return null;
    return URL.createObjectURL(previewBlob);
  }, [previewBlob]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function applySearch(e: React.FormEvent) {
    e.preventDefault();
    setSelectedUserId(null);
    setSelectedResumeId(null);
    setAppliedSearch(search);
  }

  function resetSearch() {
    setSearch(initialSearch);
    setAppliedSearch(initialSearch);
    setSelectedUserId(null);
    setSelectedResumeId(null);
  }

  function selectRole(nextRole: RoleFilter) {
    setRole(nextRole);
    setSelectedUserId(null);
    setSelectedResumeId(null);
  }

  return (
    <div className="flex h-full max-h-[calc(100vh-100px)] flex-col overflow-hidden">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold text-m-text">사용자 관리</h1>
          <p className="mt-1 text-[13px] text-m-muted">
            일반회원, 기업회원, 관리자를 구분해서 조회하고 검색합니다.
          </p>
        </div>
      </div>

      {(error || isListError) && (
        <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
          {error || (listError instanceof Error ? listError.message : '회원 목록을 불러오지 못했습니다.')}
        </div>
      )}

      <div className="grid h-full grid-cols-12 gap-6 overflow-hidden">
        <aside className="col-span-4 flex flex-col overflow-hidden rounded-2xl border border-m-border bg-m-surface">
          <div className="border-b border-m-border p-4">
            <div className="mb-3 grid grid-cols-3 gap-1">
              {ROLE_TABS.map((tab) => (
                <button
                  key={tab.role}
                  type="button"
                  onClick={() => selectRole(tab.role)}
                  className={`flex h-9 items-center justify-center gap-1.5 rounded-lg text-[12px] font-semibold ${
                    role === tab.role ? 'bg-m-primary text-white' : 'bg-m-surface-alt text-m-muted hover:text-m-text'
                  }`}
                >
                  <Icon name={tab.icon} size={14} />
                  {tab.label}
                </button>
              ))}
            </div>

            <form onSubmit={applySearch} className="space-y-2">
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="search" size={14} />
                </span>
                <input
                  value={search.q}
                  onChange={(e) => setSearch((prev) => ({ ...prev, q: e.target.value }))}
                  placeholder="통합 검색"
                  className="h-9 w-full rounded-lg border border-m-border bg-m-surface-alt pl-9 pr-3 text-[13px] outline-none focus:border-m-primary"
                />
              </div>

              {role === 'USER' && (
                <div className="grid grid-cols-2 gap-2">
                  <input
                    value={search.name}
                    onChange={(e) => setSearch((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="이름"
                    className="h-9 rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                  />
                  <input
                    type="date"
                    value={search.birth_date}
                    onChange={(e) => setSearch((prev) => ({ ...prev, birth_date: e.target.value }))}
                    className="h-9 rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                  />
                </div>
              )}

              {role === 'COMPANY' && (
                <div className="space-y-2">
                  <input
                    value={search.company_name}
                    onChange={(e) => setSearch((prev) => ({ ...prev, company_name: e.target.value }))}
                    placeholder="회사이름"
                    className="h-9 w-full rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      value={search.business_number}
                      onChange={(e) => setSearch((prev) => ({ ...prev, business_number: e.target.value }))}
                      placeholder="사업자번호"
                      className="h-9 rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                    />
                    <input
                      value={search.representative_name}
                      onChange={(e) => setSearch((prev) => ({ ...prev, representative_name: e.target.value }))}
                      placeholder="대표이름"
                      className="h-9 rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                    />
                  </div>
                </div>
              )}

              {role === 'ADMIN' && (
                <div className="grid grid-cols-[1fr_86px] gap-2">
                  <input
                    value={search.admin_identifier}
                    onChange={(e) => setSearch((prev) => ({ ...prev, admin_identifier: e.target.value }))}
                    placeholder="관리자 ID 또는 이메일"
                    className="h-9 rounded-lg border border-m-border px-3 text-[13px] outline-none focus:border-m-primary"
                  />
                  <select
                    value={search.admin_level}
                    onChange={(e) =>
                      setSearch((prev) => ({ ...prev, admin_level: e.target.value as SearchState['admin_level'] }))
                    }
                    className="h-9 rounded-lg border border-m-border px-2 text-[13px] outline-none focus:border-m-primary"
                  >
                    <option value="">등급</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                </div>
              )}

              <div className="flex gap-2">
                <button type="submit" className="h-9 flex-1 rounded-lg bg-m-primary text-[13px] font-semibold text-white">
                  검색
                </button>
                <button
                  type="button"
                  onClick={resetSearch}
                  className="h-9 rounded-lg border border-m-border px-3 text-[13px] font-semibold text-m-muted"
                >
                  초기화
                </button>
              </div>
            </form>
          </div>

          <div className="border-b border-m-border px-4 py-2 text-[12px] text-m-muted">
            {isListLoading ? '불러오는 중...' : `${roleLabel(role)} ${users.length}명 표시`}
          </div>

          <div className="flex-1 space-y-1 overflow-y-auto p-2">
            {isListLoading ? (
              <div className="p-4 text-center text-[13px] text-m-subtle">목록을 불러오는 중입니다.</div>
            ) : users.length === 0 ? (
              <div className="p-4 text-center text-[13px] text-m-subtle">검색 결과가 없습니다.</div>
            ) : (
              users.map((user) => (
                <button
                  key={user.user_id}
                  type="button"
                  onClick={() => {
                    setSelectedUserId(user.user_id);
                    setSelectedResumeId(null);
                  }}
                  className={`w-full rounded-xl p-3 text-left transition-colors ${
                    selectedUserId === user.user_id ? 'bg-m-primary-soft' : 'hover:bg-m-surface-alt'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-m-surface-alt text-m-subtle">
                      <Icon name={user.role === 'COMPANY' ? 'building' : user.role === 'ADMIN' ? 'shield' : 'user'} size={20} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <p className="truncate text-[13px] font-semibold text-m-text">{displayName(user)}</p>
                        {user.role === 'ADMIN' && user.admin_level && (
                          <span className="rounded bg-m-danger-soft px-1.5 py-0.5 text-[10px] font-bold text-m-danger">
                            {user.admin_level}
                          </span>
                        )}
                      </div>
                      <p className="truncate text-[11px] text-m-muted">{user.email}</p>
                      {user.role === 'COMPANY' && (
                        <p className="truncate text-[11px] text-m-subtle">
                          사업자번호 {valueOrDash(user.company?.business_number)}
                        </p>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="col-span-8 h-full space-y-6 overflow-y-auto pr-2">
          {selectedUserId ? (
            <>
              <div className="rounded-2xl border border-m-border bg-m-surface p-6">
                {isDetailLoading ? (
                  <div className="py-4 text-center text-[13px] text-m-subtle">상세 정보를 불러오는 중입니다.</div>
                ) : (
                  <>
                    <div className="mb-5 flex items-center gap-4">
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-m-surface-alt text-m-subtle">
                        <Icon name={userDetail?.user.role === 'COMPANY' ? 'building' : userDetail?.user.role === 'ADMIN' ? 'shield' : 'user'} size={32} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h2 className="truncate text-[18px] font-bold text-m-text">{displayName(userDetail?.user)}</h2>
                        <p className="text-[13px] text-m-muted">
                          {userDetail?.user.email} · {roleLabel(userDetail?.user.role ?? 'USER')}
                          {userDetail?.user.admin_level ? ` ${userDetail.user.admin_level}등급` : ''}
                        </p>
                      </div>
                    </div>

                    <div className="mb-6 grid grid-cols-2 gap-3 text-[13px]">
                      <div className="rounded-xl bg-m-surface-alt p-3">
                        <p className="mb-1 text-[11px] font-semibold text-m-subtle">생년월일</p>
                        <p className="text-m-text">{valueOrDash(userDetail?.user.birth_date)}</p>
                      </div>
                      <div className="rounded-xl bg-m-surface-alt p-3">
                        <p className="mb-1 text-[11px] font-semibold text-m-subtle">전화번호</p>
                        <p className="text-m-text">{valueOrDash(userDetail?.user.phone)}</p>
                      </div>
                      <div className="col-span-2 rounded-xl bg-m-surface-alt p-3">
                        <p className="mb-1 text-[11px] font-semibold text-m-subtle">주소</p>
                        <p className="text-m-text">
                          {[userDetail?.user.zipcode, userDetail?.user.address1, userDetail?.user.address2]
                            .filter(Boolean)
                            .join(' ') || '-'}
                        </p>
                      </div>
                      {userDetail?.user.role === 'COMPANY' && (
                        <>
                          <div className="rounded-xl bg-m-surface-alt p-3">
                            <p className="mb-1 text-[11px] font-semibold text-m-subtle">회사이름</p>
                            <p className="text-m-text">{valueOrDash(userDetail.user.company?.company_name)}</p>
                          </div>
                          <div className="rounded-xl bg-m-surface-alt p-3">
                            <p className="mb-1 text-[11px] font-semibold text-m-subtle">사업자번호</p>
                            <p className="text-m-text">{valueOrDash(userDetail.user.company?.business_number)}</p>
                          </div>
                        </>
                      )}
                    </div>

                    <h3 className="mb-3 text-[14px] font-semibold text-m-text">등록된 이력서</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {userDetail?.resumes.map((resume) => (
                        <button
                          key={resume.resume_id}
                          type="button"
                          onClick={() => setSelectedResumeId(resume.resume_id)}
                          className={`flex items-center gap-3 rounded-xl border p-4 text-left transition-colors ${
                            selectedResumeId === resume.resume_id
                              ? 'border-m-primary bg-m-primary-soft'
                              : 'border-m-border hover:bg-m-surface-alt'
                          }`}
                        >
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-m-primary-soft text-m-primary">
                            <Icon name="pdf" size={20} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-[13px] font-semibold text-m-text">{resume.title}</p>
                            <p className="text-[11px] text-m-muted">
                              {new Date(resume.created_at).toLocaleDateString('ko-KR')} · {formatFileSize(resume.file_size)}
                            </p>
                          </div>
                        </button>
                      ))}
                      {userDetail?.resumes.length === 0 && (
                        <div className="col-span-2 rounded-xl bg-m-surface-alt p-4 text-center text-[13px] text-m-subtle">
                          등록된 이력서가 없습니다.
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>

              {selectedResumeId && (
                <div className="rounded-2xl border border-m-border bg-m-surface p-6">
                  <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-[16px] font-bold text-m-text">이력서 상세: {resumeDetail?.title}</h2>
                    <span
                      className={`rounded-full px-2 py-1 text-[11px] font-semibold ${
                        resumeDetail?.parse_status === 'COMPLETED'
                          ? 'bg-m-success-soft text-m-success'
                          : 'bg-m-warn-soft text-m-warn'
                      }`}
                    >
                      {resumeDetail?.parse_status === 'COMPLETED' ? '파싱 완료' : '대기 또는 실패'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                    {resumeDetail ? (
                      <ResumeParsedDataEditor
                        key={`${resumeDetail.resume_id}-${resumeDetail.updated_at}`}
                        resume={resumeDetail}
                        isSaving={updateMutation.isPending}
                        onSave={(data) => updateMutation.mutate({ resumeId: resumeDetail.resume_id, data })}
                      />
                    ) : (
                      <div className="rounded-xl bg-m-surface-alt p-4 text-[13px] text-m-subtle">
                        이력서 상세 정보를 불러오는 중입니다.
                      </div>
                    )}

                    <div>
                      <h3 className="mb-2 text-[13px] font-semibold text-m-text">파일 미리보기</h3>
                      <div className="relative aspect-[1/1.4] overflow-hidden rounded-xl border border-m-border bg-m-surface-alt">
                        {isPreviewLoading ? (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <Icon name="sparkle" size={24} className="animate-spin text-m-primary" />
                          </div>
                        ) : previewUrl && !isPreviewError ? (
                          <iframe src={previewUrl} className="h-full w-full border-none" title="Resume File Preview" />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center p-4 text-center">
                            <p className="text-[11px] text-m-subtle">파일을 불러올 수 없습니다.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-m-border bg-m-surface text-m-subtle">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-m-surface-alt">
                <Icon name="user" size={32} />
              </div>
              <p className="text-[14px]">왼쪽 목록에서 회원을 선택하세요.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
