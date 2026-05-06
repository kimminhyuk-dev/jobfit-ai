'use client';

import { useState, useEffect, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import Icon from '../../components/ui/Icon';
import ResumeParsedDataEditor from '../../components/resume/ResumeParsedDataEditor';
import type { ApiError, Resume, ResumeUpdatePayload } from '../../api/types';

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`;
  return `${(size / 1024 / 1024).toFixed(1)}MB`;
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: users = [], isLoading: isListLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.listUsers(),
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
    onError: (err: ApiError) => {
      setError(err.message || '이력서 수정에 실패했습니다.');
    },
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

  const handleUserClick = (userId: number) => {
    setSelectedUserId(userId);
    setSelectedResumeId(null);
  };

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-100px)] overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-bold text-m-text">사용자 관리</h1>
          <p className="text-[13px] text-m-muted mt-1">등록된 사용자 목록과 이력서 정보를 확인합니다.</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6 h-full overflow-hidden">
        {/* 사용자 목록 */}
        <div className="col-span-4 bg-m-surface border border-m-border rounded-2xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-m-border">
            <h2 className="text-[14px] font-semibold text-m-text">사용자 목록 ({users.length})</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {isListLoading ? (
              <div className="p-4 text-center text-[13px] text-m-subtle">불러오는 중...</div>
            ) : users.length === 0 ? (
              <div className="p-4 text-center text-[13px] text-m-subtle">사용자가 없습니다.</div>
            ) : (
              users.map((user) => (
                <button
                  key={user.user_id}
                  onClick={() => handleUserClick(user.user_id)}
                  className={`w-full p-3 rounded-xl flex items-center gap-3 text-left transition-colors ${
                    selectedUserId === user.user_id ? 'bg-m-primary-soft text-m-primary' : 'hover:bg-m-surface-alt'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-m-surface-alt flex items-center justify-center text-m-subtle">
                    <Icon name="user" size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-m-text truncate">{user.name}</p>
                    <p className="text-[11px] text-m-muted truncate">{user.email}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* 사용자 상세 및 이력서 */}
        <div className="col-span-8 space-y-6 overflow-y-auto h-full pr-2">
          {selectedUserId ? (
            <>
              {/* 사용자 기본 정보 */}
              <div className="bg-m-surface border border-m-border rounded-2xl p-6">
                {isDetailLoading ? (
                  <div className="text-center py-4 text-[13px] text-m-subtle">사용자 정보를 불러오는 중...</div>
                ) : (
                  <>
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-16 h-16 rounded-full bg-m-surface-alt flex items-center justify-center text-m-subtle">
                        <Icon name="user" size={32} />
                      </div>
                      <div>
                        <h2 className="text-[18px] font-bold text-m-text">{userDetail?.user.name}</h2>
                        <p className="text-[13px] text-m-muted">
                          {userDetail?.user.email} · 가입일{' '}
                          {userDetail?.user.created_at && new Date(userDetail.user.created_at).toLocaleDateString('ko-KR')}
                        </p>
                      </div>
                    </div>

                    <h3 className="text-[14px] font-semibold text-m-text mb-3">등록된 이력서</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {userDetail?.resumes.map((resume) => (
                        <button
                          key={resume.resume_id}
                          onClick={() => setSelectedResumeId(resume.resume_id)}
                          className={`p-4 border rounded-xl flex items-center gap-3 text-left transition-colors ${
                            selectedResumeId === resume.resume_id
                              ? 'border-m-primary bg-m-primary-soft'
                              : 'border-m-border hover:bg-m-surface-alt'
                          }`}
                        >
                          <div className="w-10 h-10 rounded-lg bg-m-primary-soft text-m-primary flex items-center justify-center flex-shrink-0">
                            <Icon name="pdf" size={20} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-[13px] font-semibold text-m-text truncate">{resume.title}</p>
                            <p className="text-[11px] text-m-muted">
                              {new Date(resume.created_at).toLocaleDateString()} · {formatFileSize(resume.file_size)}
                            </p>
                          </div>
                        </button>
                      ))}
                      {userDetail?.resumes.length === 0 && (
                        <div className="col-span-2 p-4 text-center text-[13px] text-m-subtle bg-m-surface-alt rounded-xl">
                          등록된 이력서가 없습니다.
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* 이력서 상세 정보 */}
              {selectedResumeId && (
                <div className="bg-m-surface border border-m-border rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-[16px] font-bold text-m-text">이력서 상세: {resumeDetail?.title}</h2>
                    <span
                      className={`text-[11px] font-semibold px-2 py-1 rounded-full ${
                        resumeDetail?.parse_status === 'COMPLETED'
                          ? 'bg-m-success-soft text-m-success'
                          : 'bg-m-warn-soft text-m-warn'
                      }`}
                    >
                      {resumeDetail?.parse_status === 'COMPLETED' ? '파싱 완료' : '대기/실패'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-6">
                    {resumeDetail ? (
                      <ResumeParsedDataEditor
                        key={`${resumeDetail.resume_id}-${resumeDetail.updated_at}`}
                        resume={resumeDetail}
                        isSaving={updateMutation.isPending}
                        onSave={(data) => updateMutation.mutate({ resumeId: resumeDetail.resume_id, data })}
                      />
                    ) : (
                      <div className="rounded-xl bg-m-surface-alt p-4 text-[13px] text-m-subtle">
                        이력서 상세 정보를 불러오는 중...
                      </div>
                    )}

                    <div>
                      <h3 className="text-[13px] font-semibold text-m-text mb-2">파일 미리보기</h3>
                      <div className="rounded-xl border border-m-border bg-m-surface-alt overflow-hidden aspect-[1/1.4] relative">
                        {isPreviewLoading ? (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <Icon name="sparkle" size={24} className="animate-spin text-m-primary" />
                          </div>
                        ) : previewUrl && !isPreviewError ? (
                          <iframe
                            src={previewUrl}
                            className="w-full h-full border-none"
                            title="Resume File Preview"
                          />
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
            <div className="bg-m-surface border border-m-border rounded-2xl h-full flex flex-col items-center justify-center text-m-subtle">
              <div className="w-16 h-16 rounded-full bg-m-surface-alt flex items-center justify-center mb-4">
                <Icon name="user" size={32} />
              </div>
              <p className="text-[14px]">목록에서 사용자를 선택해 정보를 확인하세요.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
