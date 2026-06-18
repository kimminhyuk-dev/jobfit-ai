'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { RequireAuth } from '../../../components/auth/RequireAuth';
import Icon from '../../../components/ui/Icon';
import { showToast } from '../../../components/ui/Toast';
import ApplicantResumeModal from '../../../components/company/ApplicantResumeModal';
import { companyApi } from '../../../api/company';
import type { ApiError } from '../../../api/client';
import { useAuth } from '../../../stores/authContext';
import type { ApplicationStatus, CompanyApplicant } from '../../../api/types';

const STATUS_META: Record<ApplicationStatus, { label: string; cls: string }> = {
  SUBMITTED: { label: '접수', cls: 'bg-m-primary-soft text-m-primary' },
  VIEWED: { label: '열람', cls: 'bg-m-warn-soft text-m-warn' },
  REJECTED: { label: '불합격', cls: 'bg-m-danger-soft text-m-danger' },
  INTERVIEW: { label: '면접', cls: 'bg-m-success-soft text-m-success' },
  CANCELED: { label: '지원취소', cls: 'bg-m-surface-alt text-m-subtle' },
};

function formatDateTime(value: string): string {
  const d = new Date(value);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string' && message.trim()) return message;
  }
  return '대시보드를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.';
}

function CompanyDashboardInner() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [viewingApplicationId, setViewingApplicationId] = useState<number | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['company', 'dashboard'],
    queryFn: companyApi.getDashboard,
  });

  // 이력서를 열람하면 미열람 알람(pending_count)이 줄도록 대시보드를 갱신한다.
  const handleResumeViewed = () => {
    queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
  };

  const statusMutation = useMutation({
    mutationFn: (applicationId: number) =>
      companyApi.updateApplicationStatus(applicationId, 'REJECTED'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
      showToast('탈락 처리했습니다.', 'success');
    },
    onError: (e: ApiError) => {
      showToast(e.message || '상태 변경에 실패했습니다.', 'error');
    },
  });

  const handleReject = (applicant: CompanyApplicant) => {
    if (statusMutation.isPending || applicant.status === 'REJECTED') return;
    if (!window.confirm(`${applicant.applicant_name ?? '지원자'} 님을 탈락 처리할까요?`)) {
      return;
    }
    statusMutation.mutate(applicant.application_id);
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  const applicants = data?.applicants ?? [];
  const statusCounts = applicants.reduce<Record<ApplicationStatus, number>>(
    (acc, item) => {
      acc[item.status] += 1;
      return acc;
    },
    { SUBMITTED: 0, VIEWED: 0, INTERVIEW: 0, REJECTED: 0, CANCELED: 0 },
  );
  const reviewedCount = statusCounts.VIEWED + statusCounts.INTERVIEW + statusCounts.REJECTED;
  const reviewRate =
    data && data.received_count > 0 ? Math.round((reviewedCount / data.received_count) * 100) : 0;
  const recentApplicants = applicants.slice(0, 5);
  const companyName = data?.company_name ?? user?.name ?? '기업회원';

  const stats = [
    { label: '접수된 지원', value: data?.received_count ?? 0, icon: 'file' as const, hint: '전체 지원' },
    { label: '열람 대기', value: data?.pending_count ?? 0, icon: 'bell' as const, hint: '확인 필요' },
    { label: '등록 공고', value: data?.posting_count ?? 0, icon: 'briefcase' as const, hint: '연결 공고' },
    { label: '검토율', value: reviewRate, suffix: '%', icon: 'chart' as const, hint: '열람 이상' },
  ];

  const statusSummary: Array<{ key: ApplicationStatus; label: string; description: string }> = [
    { key: 'SUBMITTED', label: '신규 접수', description: '아직 열람하지 않은 지원' },
    { key: 'VIEWED', label: '이력서 열람', description: '검토가 시작된 지원' },
    { key: 'INTERVIEW', label: '면접 예정', description: '면접 안내 대상' },
    { key: 'REJECTED', label: '불합격 처리', description: '검토 종료' },
  ];

  return (
    <div className="min-h-screen bg-m-bg p-8 font-sans">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-[24px] font-bold text-m-text">기업회원 대시보드</h1>
            <p className="mt-1 text-[13px] text-m-muted">
              {companyName}
              {data?.business_number ? ` · 사업자번호 ${data.business_number}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/company/jobs"
              className="flex items-center gap-1.5 rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] font-semibold text-m-muted hover:bg-m-surface-alt transition-colors"
            >
              <Icon name="briefcase" size={14} />
              공고 관리
            </Link>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-1.5 rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] font-semibold text-m-muted hover:bg-m-surface-alt disabled:opacity-60 transition-colors"
            >
              <Icon name="trend" size={14} />
              {isFetching ? '새로고침 중' : '새로고침'}
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] font-semibold text-m-muted hover:bg-m-surface-alt transition-colors"
            >
              <Icon name="logout" size={14} />
              로그아웃
            </button>
          </div>
        </div>

        {isError && (
          <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
            {getErrorMessage(error)}
          </div>
        )}

        <div className="mb-6 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
          <section className="rounded-2xl border border-m-border bg-m-surface p-5">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-[12px] font-semibold text-m-primary">오늘 확인할 일</p>
                <h2 className="mt-1 text-[18px] font-bold text-m-text">
                  미열람 지원 {data?.pending_count ?? 0}건을 확인하세요
                </h2>
              </div>
              <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-m-primary-soft text-m-primary">
                <Icon name="bell" size={19} />
                {(data?.pending_count ?? 0) > 0 && (
                  <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-m-danger px-1.5 py-0.5 text-center text-[10px] font-bold text-white">
                    {data?.pending_count}
                  </span>
                )}
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-m-surface-alt p-3">
                <p className="text-[11px] font-semibold text-m-subtle">최근 지원</p>
                <p className="mt-1 text-[20px] font-bold text-m-text">{recentApplicants.length}</p>
              </div>
              <div className="rounded-xl bg-m-surface-alt p-3">
                <p className="text-[11px] font-semibold text-m-subtle">검토 완료</p>
                <p className="mt-1 text-[20px] font-bold text-m-text">{reviewedCount}</p>
              </div>
              <div className="rounded-xl bg-m-surface-alt p-3">
                <p className="text-[11px] font-semibold text-m-subtle">연결 공고</p>
                <p className="mt-1 text-[20px] font-bold text-m-text">{data?.posting_count ?? 0}</p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-m-border bg-m-surface p-5">
            <p className="text-[12px] font-semibold text-m-subtle">운영 상태</p>
            <div className="mt-4 space-y-3">
              {[
                { label: '지원 접수', ok: (data?.received_count ?? 0) > 0 },
                { label: '기업 정보 연결', ok: Boolean(data?.company_id) },
                { label: '공고 연결', ok: (data?.posting_count ?? 0) > 0 },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between text-[13px]">
                  <span className="text-m-muted">{item.label}</span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                      item.ok ? 'bg-m-success-soft text-m-success' : 'bg-m-surface-alt text-m-subtle'
                    }`}
                  >
                    <Icon name={item.ok ? 'check' : 'x'} size={12} />
                    {item.ok ? '정상' : '대기'}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Stats */}
        <div className="grid gap-4 mb-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((item) => (
            <div key={item.label} className="rounded-xl border border-m-border bg-m-surface p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-m-primary-soft text-m-primary">
                  <Icon name={item.icon} size={18} />
                </div>
                <span className="text-[11px] font-semibold text-m-subtle">{item.hint}</span>
              </div>
              <p className="text-[12px] font-semibold text-m-subtle">{item.label}</p>
              <p className="mt-1 text-[22px] font-bold text-m-text">
                {isLoading ? '–' : `${item.value.toLocaleString()}${item.suffix ?? ''}`}
              </p>
            </div>
          ))}
        </div>

        <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_1fr]">
          <section className="rounded-2xl border border-m-border bg-m-surface p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold text-m-text">지원 상태 요약</h2>
              <span className="text-[12px] text-m-subtle">총 {applicants.length}건</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {statusSummary.map((item) => {
                const meta = STATUS_META[item.key];
                return (
                  <div key={item.key} className="rounded-xl border border-m-border p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
                        {item.label}
                      </span>
                      <span className="text-[18px] font-bold text-m-text">{statusCounts[item.key]}</span>
                    </div>
                    <p className="text-[12px] text-m-subtle">{item.description}</p>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="rounded-2xl border border-m-border bg-m-surface p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold text-m-text">최근 지원</h2>
              <span className="text-[12px] text-m-subtle">최신 5건</span>
            </div>
            {isLoading ? (
              <div className="py-8 text-center text-[13px] text-m-subtle">불러오는 중...</div>
            ) : recentApplicants.length === 0 ? (
              <div className="rounded-xl bg-m-surface-alt p-4 text-[13px] text-m-subtle">
                아직 최근 지원이 없습니다. 지원자가 들어오면 여기에서 바로 확인할 수 있습니다.
              </div>
            ) : (
              <div className="space-y-3">
                {recentApplicants.map((a) => {
                  const meta = STATUS_META[a.status];
                  return (
                    <div key={a.application_id} className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold text-m-text">
                          {a.applicant_name ?? '이름 미상'} · {a.resume_title}
                        </p>
                        <p className="truncate text-[12px] text-m-subtle">{a.job_title}</p>
                      </div>
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
                        {meta.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        {/* Applicants */}
        <div className="rounded-2xl border border-m-border bg-m-surface overflow-hidden">
          <div className="flex items-center justify-between border-b border-m-border p-4">
            <h2 className="text-[15px] font-semibold text-m-text">지원자 현황</h2>
            <span className="text-[12px] text-m-subtle">{data?.applicants.length ?? 0}명</span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-[13px] text-m-subtle">불러오는 중...</div>
          ) : !data || applicants.length === 0 ? (
            <div className="p-10">
              <div className="mx-auto max-w-md text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-m-primary-soft text-m-primary">
                  <Icon name="briefcase" size={22} />
                </div>
                <p className="text-[15px] font-semibold text-m-text">아직 받은 지원이 없습니다</p>
                <p className="mt-2 text-[13px] leading-6 text-m-subtle">
                  공고에 지원자가 생기면 이 표에 지원자, 지원 공고, 이력서, 열람 상태가 자동으로 정리됩니다.
                </p>
              </div>
            </div>
          ) : (
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-m-border bg-m-surface-alt text-[12px] text-m-subtle">
                  <th className="px-4 py-2.5 text-left font-semibold">지원자</th>
                  <th className="px-4 py-2.5 text-left font-semibold">지원 공고</th>
                  <th className="px-4 py-2.5 text-left font-semibold">이력서</th>
                  <th className="px-4 py-2.5 text-left font-semibold">상태</th>
                  <th className="px-4 py-2.5 text-left font-semibold">지원일</th>
                  <th className="px-4 py-2.5 text-left font-semibold">열람일</th>
                  <th className="px-4 py-2.5 text-left font-semibold">처리</th>
                  <th className="px-4 py-2.5 text-right font-semibold">이력서</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m-border">
                {applicants.map((a: CompanyApplicant) => {
                  const meta = STATUS_META[a.status];
                  return (
                    <tr key={a.application_id} className="hover:bg-m-surface-alt transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-semibold text-m-text">{a.applicant_name ?? '이름 미상'}</p>
                        <p className="text-[11px] text-m-subtle">{a.applicant_email}</p>
                      </td>
                      <td className="px-4 py-3 text-m-muted">{a.job_title}</td>
                      <td className="px-4 py-3 text-m-muted">{a.resume_title}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-m-subtle">{formatDateTime(a.applied_at)}</td>
                      <td className="px-4 py-3 text-m-subtle">
                        {a.viewed_at ? formatDateTime(a.viewed_at) : '미열람'}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => handleReject(a)}
                          disabled={statusMutation.isPending || a.status === 'REJECTED'}
                          className="rounded-lg border border-m-border px-2.5 py-1 text-[12px] font-semibold text-m-danger transition-colors hover:bg-m-danger-soft disabled:cursor-not-allowed disabled:opacity-45"
                        >
                          {a.status === 'REJECTED' ? '처리됨' : '탈락'}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setViewingApplicationId(a.application_id)}
                          className="inline-flex items-center gap-1 rounded-lg border border-m-border px-2.5 py-1 text-[12px] font-semibold text-m-primary hover:bg-m-primary-soft transition-colors"
                        >
                          <Icon name="eye" size={13} />
                          이력서 보기
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {viewingApplicationId !== null && (
        <ApplicantResumeModal
          applicationId={viewingApplicationId}
          onClose={() => setViewingApplicationId(null)}
          onViewed={handleResumeViewed}
        />
      )}
    </div>
  );
}

export default function CompanyDashboardPage() {
  return (
    <RequireAuth allowedRoles={['COMPANY']}>
      <CompanyDashboardInner />
    </RequireAuth>
  );
}
