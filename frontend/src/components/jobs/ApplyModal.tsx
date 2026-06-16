'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Icon from '../ui/Icon';
import { applicationsApi } from '../../api/applications';
import { resumesApi } from '../../api/resumes';
import type { ApiError, Resume } from '../../api/types';

function formatDate(value: string): string {
  const date = new Date(value);
  if (isNaN(date.getTime())) return '';
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function ApplyModal({
  job,
  onClose,
}: {
  job: { job_id: number; title: string; company_name: string | null };
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [error, setError] = useState('');

  const { data: resumes = [], isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: resumesApi.getResumes,
  });

  const mutation = useMutation({
    mutationFn: () =>
      applicationsApi.apply({ job_id: job.job_id, resume_id: selectedResumeId as number }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', 'me'] });
    },
    onError: (e: ApiError) => {
      setError(
        e.code === 'APPLICATION_001'
          ? '이미 지원한 공고입니다.'
          : e.message || '지원에 실패했습니다.',
      );
    },
  });

  function handleSubmit() {
    setError('');
    if (selectedResumeId === null) {
      setError('보낼 이력서를 선택하세요.');
      return;
    }
    mutation.mutate();
  }

  const done = mutation.isSuccess;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-m-surface rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-start justify-between mb-1">
          <h2 className="text-[16px] font-bold text-m-text">이력서 보내기</h2>
          <button onClick={onClose} className="text-m-subtle hover:text-m-muted p-1">
            <Icon name="x" size={16} />
          </button>
        </div>
        <p className="text-[12px] text-m-muted mb-4">
          <span className="font-semibold text-m-text">{job.title}</span>
          {job.company_name ? ` · ${job.company_name}` : ''}
        </p>

        {done ? (
          <div className="rounded-xl border border-m-success/30 bg-m-success-soft p-5 text-center">
            <Icon name="flag" size={22} className="text-m-success mx-auto mb-2" />
            <p className="text-[14px] font-semibold text-m-text">지원이 접수되었어요</p>
            <p className="text-[12px] text-m-muted mt-1">지원 현황에서 확인할 수 있습니다.</p>
            <button
              onClick={onClose}
              className="mt-4 h-9 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors"
            >
              확인
            </button>
          </div>
        ) : (
          <>
            <p className="text-[12px] font-medium text-m-muted mb-2">보낼 이력서 선택</p>
            <div className="flex flex-col gap-2 max-h-72 overflow-auto scrollbar-thin">
              {isLoading ? (
                <p className="text-[13px] text-m-subtle py-6 text-center">불러오는 중...</p>
              ) : resumes.length === 0 ? (
                <p className="text-[13px] text-m-subtle py-6 text-center">
                  등록된 이력서가 없습니다. 먼저 이력서를 업로드하세요.
                </p>
              ) : (
                resumes.map((r: Resume) => (
                  <button
                    key={r.resume_id}
                    type="button"
                    onClick={() => setSelectedResumeId(r.resume_id)}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-colors ${
                      selectedResumeId === r.resume_id
                        ? 'border-m-primary bg-m-primary-soft'
                        : 'border-m-border hover:bg-m-surface-alt'
                    }`}
                  >
                    <Icon name="file" size={16} className="text-m-muted shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-m-text truncate">{r.title}</p>
                      <p className="text-[11px] text-m-subtle">등록일 {formatDate(r.created_at)}</p>
                    </div>
                    {selectedResumeId === r.resume_id && (
                      <Icon name="check" size={16} className="text-m-primary shrink-0" />
                    )}
                  </button>
                ))
              )}
            </div>

            {error && (
              <p className="text-[12px] text-m-danger bg-m-danger/10 px-3 py-2 rounded-lg mt-3">
                {error}
              </p>
            )}

            <div className="flex justify-end gap-2 mt-5">
              <button
                onClick={onClose}
                className="h-9 px-4 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                disabled={mutation.isPending || resumes.length === 0}
                className="h-9 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {mutation.isPending ? '보내는 중...' : '보내기'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
