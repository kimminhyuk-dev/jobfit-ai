'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { applicationsApi } from '../../api/applications';
import { showToast } from '../../components/ui/Toast';
import type { ApiError, ApplicationStatus, MyApplication } from '../../api/types';

const STATUS_META: Record<ApplicationStatus, { label: string; cls: string }> = {
  SUBMITTED: { label: '지원 완료', cls: 'bg-m-primary-soft text-m-primary' },
  VIEWED: { label: '이력서 열람', cls: 'bg-m-warn-soft text-m-warn' },
  ACCEPTED: { label: '합격', cls: 'bg-m-success-soft text-m-success' },
  REJECTED: { label: '불합격', cls: 'bg-m-danger-soft text-m-danger' },
  CANCELED: { label: '지원취소', cls: 'bg-m-surface-alt text-m-subtle' },
};

// 합격/불합격 확정 전까지만 지원 취소를 허용한다.
const CANCELABLE: ApplicationStatus[] = ['SUBMITTED', 'VIEWED'];

const STATUS_ORDER: ApplicationStatus[] = ['SUBMITTED', 'VIEWED', 'ACCEPTED', 'REJECTED', 'CANCELED'];

function dateStr(value: string): string {
  const d = new Date(value);
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function ApplicationsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: applications = [], isLoading, isError } = useQuery({
    queryKey: ['applications', 'me'],
    queryFn: applicationsApi.getMyApplications,
  });

  const cancelMutation = useMutation({
    mutationFn: (applicationId: number) => applicationsApi.cancel(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', 'me'] });
      showToast('지원을 취소했습니다.', 'success');
    },
    onError: (e: ApiError) => showToast(e.message || '지원 취소에 실패했습니다.', 'error'),
  });

  function handleCancel(app: MyApplication) {
    if (cancelMutation.isPending) return;
    if (!window.confirm(`'${app.job_title}' 지원을 취소할까요?`)) return;
    cancelMutation.mutate(app.application_id);
  }

  const counts = STATUS_ORDER.map((status) => ({
    status,
    count: applications.filter((a) => a.status === status).length,
  }));

  return (
    <div className="p-6 max-w-300 mx-auto">
      <div className="mb-5">
        <h1 className="text-[22px] font-bold text-m-text tracking-tight">지원 현황</h1>
        <p className="text-[13px] text-m-muted mt-1">
          지금까지 <strong className="text-m-primary">{applications.length}</strong>건의 공고에 지원했어요.
        </p>
      </div>

      {/* 상태 요약 */}
      <div className="grid grid-cols-5 gap-3 mb-5 max-lg:grid-cols-3 max-md:grid-cols-2">
        {counts.map(({ status, count }) => (
          <div key={status} className="bg-m-surface border border-m-border rounded-xl p-4">
            <span className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_META[status].cls}`}>
              {STATUS_META[status].label}
            </span>
            <p className="text-[24px] font-bold text-m-text mt-2 font-mono">{count}</p>
          </div>
        ))}
      </div>

      {/* 목록 */}
      <div className="bg-m-surface border border-m-border rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-[13px] text-m-subtle">불러오는 중...</div>
        ) : isError ? (
          <div className="py-16 text-center text-[13px] text-m-subtle">지원 현황을 불러올 수 없습니다.</div>
        ) : applications.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-[14px] text-m-muted mb-3">아직 지원한 공고가 없어요.</p>
            <Link
              href="/user/jobs"
              className="inline-flex h-9 px-4 items-center rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors"
            >
              채용공고 보러가기
            </Link>
          </div>
        ) : (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-m-border bg-m-surface-alt text-[12px] text-m-subtle">
                <th className="px-5 py-3 text-left font-semibold">지원 공고</th>
                <th className="px-4 py-3 text-left font-semibold">사용 이력서</th>
                <th className="px-4 py-3 text-left font-semibold">상태</th>
                <th className="px-4 py-3 text-left font-semibold">지원일</th>
                <th className="px-4 py-3 text-right font-semibold">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-m-border">
              {applications.map((app: MyApplication) => {
                const meta = STATUS_META[app.status];
                return (
                  <tr
                    key={app.application_id}
                    className="hover:bg-m-surface-alt transition-colors cursor-pointer"
                    onClick={() => router.push(`/user/jobs/${app.job_id}`)}
                  >
                    <td className="px-5 py-3.5">
                      <p className="font-semibold text-m-text truncate max-w-100">{app.job_title}</p>
                      <p className="text-[11px] text-m-subtle">{app.company_name ?? '기관명 미상'}</p>
                    </td>
                    <td className="px-4 py-3.5 text-m-muted truncate max-w-40">{app.resume_title}</td>
                    <td className="px-4 py-3.5">
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
                        {meta.label}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-m-subtle">{dateStr(app.applied_at)}</td>
                    <td className="px-4 py-3.5 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/user/jobs/${app.job_id}`}
                          className="text-[12px] font-medium text-m-primary hover:underline"
                        >
                          공고
                        </Link>
                        {app.source_url && (
                          <a
                            href={app.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[12px] font-medium text-m-muted hover:underline"
                          >
                            원문
                          </a>
                        )}
                        {CANCELABLE.includes(app.status) && (
                          <button
                            onClick={() => handleCancel(app)}
                            disabled={cancelMutation.isPending}
                            className="text-[12px] font-medium text-m-danger hover:underline disabled:opacity-50"
                          >
                            지원취소
                          </button>
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
  );
}
