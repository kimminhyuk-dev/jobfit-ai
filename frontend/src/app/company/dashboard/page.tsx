'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { RequireAuth } from '../../../components/auth/RequireAuth';
import Icon from '../../../components/ui/Icon';
import { companyApi } from '../../../api/company';
import { useAuth } from '../../../stores/authContext';
import type { ApplicationStatus, CompanyApplicant } from '../../../api/types';

const STATUS_META: Record<ApplicationStatus, { label: string; cls: string }> = {
  SUBMITTED: { label: '접수', cls: 'bg-m-primary-soft text-m-primary' },
  VIEWED: { label: '열람', cls: 'bg-m-warn-soft text-m-warn' },
  ACCEPTED: { label: '합격', cls: 'bg-m-success-soft text-m-success' },
  REJECTED: { label: '불합격', cls: 'bg-m-danger-soft text-m-danger' },
};

function formatDateTime(value: string): string {
  const d = new Date(value);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

function CompanyDashboardInner() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['company', 'dashboard'],
    queryFn: companyApi.getDashboard,
  });

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  const stats = [
    { label: '접수된 지원', value: data?.received_count ?? 0, icon: 'file' as const },
    { label: '열람 대기', value: data?.pending_count ?? 0, icon: 'eye' as const },
    { label: '등록 공고', value: data?.posting_count ?? 0, icon: 'briefcase' as const },
  ];

  return (
    <div className="min-h-screen bg-m-bg p-8 font-sans">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-[24px] font-bold text-m-text">기업회원 대시보드</h1>
            <p className="mt-1 text-[13px] text-m-muted">
              {data?.company_name ?? user?.name ?? '기업회원'}
              {data?.business_number ? ` · 사업자번호 ${data.business_number}` : ''}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] font-semibold text-m-muted hover:bg-m-surface-alt transition-colors"
          >
            <Icon name="logout" size={14} />
            로그아웃
          </button>
        </div>

        {isError && (
          <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
            {error instanceof Error ? error.message : '대시보드를 불러오지 못했습니다.'}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {stats.map((item) => (
            <div key={item.label} className="rounded-xl border border-m-border bg-m-surface p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-m-primary-soft text-m-primary">
                <Icon name={item.icon} size={18} />
              </div>
              <p className="text-[12px] font-semibold text-m-subtle">{item.label}</p>
              <p className="mt-1 text-[22px] font-bold text-m-text">
                {isLoading ? '–' : item.value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>

        {/* Applicants */}
        <div className="rounded-2xl border border-m-border bg-m-surface overflow-hidden">
          <div className="flex items-center justify-between border-b border-m-border p-4">
            <h2 className="text-[15px] font-semibold text-m-text">지원자 현황</h2>
            <span className="text-[12px] text-m-subtle">{data?.applicants.length ?? 0}명</span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-[13px] text-m-subtle">불러오는 중...</div>
          ) : !data || data.applicants.length === 0 ? (
            <div className="p-10 text-center text-[13px] text-m-subtle">
              아직 받은 지원이 없습니다.
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
                </tr>
              </thead>
              <tbody className="divide-y divide-m-border">
                {data.applicants.map((a: CompanyApplicant) => {
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
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
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
