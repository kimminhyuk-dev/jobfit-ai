'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { RequireAuth } from '../../../components/auth/RequireAuth';
import Icon from '../../../components/ui/Icon';
import { showToast } from '../../../components/ui/Toast';
import CompanyJobFormModal from '../../../components/company/CompanyJobFormModal';
import CompanyJobDetailModal from '../../../components/company/CompanyJobDetailModal';
import { companyApi } from '../../../api/company';
import type { ApiError, CompanyJob } from '../../../api/types';

function dateStr(value: string | null): string {
  if (!value) return '상시';
  const d = new Date(value);
  return isNaN(d.getTime()) ? '상시' : d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function CompanyJobsInner() {
  const queryClient = useQueryClient();
  const [detailJob, setDetailJob] = useState<CompanyJob | null>(null);
  const [formState, setFormState] = useState<{ mode: 'create' | 'edit'; job?: CompanyJob } | null>(null);

  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: ['company', 'jobs'],
    queryFn: companyApi.listJobs,
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: number) => companyApi.deleteJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', 'jobs'] });
      queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
      showToast('공고를 삭제했습니다.', 'success');
      setDetailJob(null);
    },
    onError: (e: ApiError) => showToast(e.message || '삭제에 실패했습니다.', 'error'),
  });

  const hiddenMutation = useMutation({
    mutationFn: ({ jobId, hidden }: { jobId: number; hidden: boolean }) =>
      companyApi.updateJob(jobId, { status: hidden ? 'HIDDEN' : 'OPEN' }),
    onSuccess: (updatedJob) => {
      queryClient.invalidateQueries({ queryKey: ['company', 'jobs'] });
      queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
      setDetailJob((current) =>
        current?.job_id === updatedJob.job_id ? updatedJob : current,
      );
      showToast(
        updatedJob.status === 'HIDDEN' ? '공고를 숨김 처리했습니다.' : '공고를 다시 공개했습니다.',
        'success',
      );
    },
    onError: (e: ApiError) => showToast(e.message || '공고 상태 변경에 실패했습니다.', 'error'),
  });

  function handleDelete(job: CompanyJob) {
    if (!window.confirm(`'${job.title}' 공고를 삭제할까요?`)) return;
    deleteMutation.mutate(job.job_id);
  }

  function handleToggleHidden(job: CompanyJob) {
    const shouldHide = job.status !== 'HIDDEN';
    hiddenMutation.mutate({ jobId: job.job_id, hidden: shouldHide });
  }

  return (
    <div className="min-h-screen bg-m-bg p-8 font-sans">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <Link
              href="/company/dashboard"
              className="mb-2 inline-flex items-center gap-1 text-[13px] text-m-muted hover:text-m-text transition-colors"
            >
              <Icon name="arrow-left" size={14} /> 대시보드
            </Link>
            <h1 className="text-[24px] font-bold text-m-text">공고 관리</h1>
            <p className="mt-1 text-[13px] text-m-muted">
              등록한 공고를 확인·수정하고 새 공고를 올릴 수 있습니다. 외부 수집 공고는 읽기 전용입니다.
            </p>
          </div>
          <button
            onClick={() => setFormState({ mode: 'create' })}
            className="flex items-center gap-1.5 rounded-lg bg-m-primary px-4 py-2.5 text-[13px] font-semibold text-white hover:bg-m-primary-hover transition-colors"
          >
            <Icon name="plus" size={15} /> 새 공고 등록
          </button>
        </div>

        <div className="rounded-2xl border border-m-border bg-m-surface overflow-hidden">
          {isLoading ? (
            <div className="py-16 text-center text-[13px] text-m-subtle">불러오는 중...</div>
          ) : isError ? (
            <div className="py-16 text-center text-[13px] text-m-subtle">공고를 불러올 수 없습니다.</div>
          ) : jobs.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-[14px] text-m-muted mb-3">아직 등록한 공고가 없습니다.</p>
              <button
                onClick={() => setFormState({ mode: 'create' })}
                className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white hover:bg-m-primary-hover transition-colors"
              >
                <Icon name="plus" size={14} /> 첫 공고 등록하기
              </button>
            </div>
          ) : (
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-m-border bg-m-surface-alt text-[12px] text-m-subtle">
                  <th className="px-4 py-2.5 text-left font-semibold">공고</th>
                  <th className="px-4 py-2.5 text-left font-semibold">상태</th>
                  <th className="px-4 py-2.5 text-left font-semibold">지원자</th>
                  <th className="px-4 py-2.5 text-left font-semibold">마감일</th>
                  <th className="px-4 py-2.5 text-right font-semibold">관리</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m-border">
                {jobs.map((job) => {
                  const closed = job.status === 'CLOSED';
                  const hidden = job.status === 'HIDDEN';
                  return (
                    <tr
                      key={job.job_id}
                      onClick={() => setDetailJob(job)}
                      className="cursor-pointer hover:bg-m-surface-alt transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-m-text">{job.title}</p>
                          {!job.editable && (
                            <span className="rounded bg-m-surface-alt px-1.5 py-0.5 text-[10px] font-semibold text-m-subtle">
                              외부
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-m-subtle">
                          {[job.location, job.employment_type].filter(Boolean).join(' · ') || '조건 미입력'}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            hidden
                              ? 'bg-m-warn-soft text-m-warn'
                              : closed
                                ? 'bg-m-surface-alt text-m-subtle'
                                : 'bg-m-success-soft text-m-success'
                          }`}
                        >
                          {hidden ? '숨김' : closed ? '마감' : '모집중'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-m-muted">{job.applicant_count}명</td>
                      <td className="px-4 py-3 text-m-subtle">{dateStr(job.deadline)}</td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setDetailJob(job)}
                            className="text-[12px] font-medium text-m-primary hover:underline"
                          >
                            확인
                          </button>
                          {job.editable && (
                            <>
                              <button
                                onClick={() => setFormState({ mode: 'edit', job })}
                                className="text-[12px] font-medium text-m-muted hover:underline"
                              >
                                수정
                              </button>
                              <button
                                onClick={() => handleToggleHidden(job)}
                                className="text-[12px] font-medium text-m-muted hover:underline"
                              >
                                {hidden ? '공개' : '숨김'}
                              </button>
                              <button
                                onClick={() => handleDelete(job)}
                                className="text-[12px] font-medium text-m-danger hover:underline"
                              >
                                삭제
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {detailJob && (
        <CompanyJobDetailModal
          job={detailJob}
          onClose={() => setDetailJob(null)}
          onEdit={() => {
            setFormState({ mode: 'edit', job: detailJob });
            setDetailJob(null);
          }}
          onDelete={() => handleDelete(detailJob)}
          onToggleHidden={() => handleToggleHidden(detailJob)}
          deleting={deleteMutation.isPending}
          togglingHidden={hiddenMutation.isPending}
        />
      )}

      {formState && (
        <CompanyJobFormModal
          mode={formState.mode}
          job={formState.job}
          onClose={() => setFormState(null)}
        />
      )}
    </div>
  );
}

export default function CompanyJobsPage() {
  return (
    <RequireAuth allowedRoles={['COMPANY']}>
      <CompanyJobsInner />
    </RequireAuth>
  );
}
