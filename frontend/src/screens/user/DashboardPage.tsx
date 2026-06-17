'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { useAuth } from '../../stores/authContext';
import { jobsApi } from '../../api/jobs';
import { applicationsApi } from '../../api/applications';
import { resumesApi } from '../../api/resumes';
import type { ApplicationStatus, JobPostingItem } from '../../api/types';

const APPLICATION_STATUS: Record<ApplicationStatus, { label: string; color: string }> = {
  SUBMITTED: { label: '지원 완료', color: '#6366f1' },
  VIEWED: { label: '열람됨', color: '#f59e0b' },
  ACCEPTED: { label: '합격', color: '#10b981' },
  REJECTED: { label: '불합격', color: '#ef4444' },
  CANCELED: { label: '지원취소', color: '#94a3b8' },
};

const LOGO_COLORS = ['#1d4ed8', '#0f766e', '#7c3aed', '#ea580c', '#0284c7', '#15803d', '#b45309'];

function logoColor(name: string | null): string {
  if (!name) return '#6b7280';
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffffffff;
  return LOGO_COLORS[Math.abs(hash) % LOGO_COLORS.length];
}

function initials(name: string | null): string {
  if (!name) return '?';
  return name.trim().slice(0, 2);
}

function deadlineLabel(deadline: string | null): string {
  if (!deadline) return '상시채용';
  const d = new Date(deadline);
  if (isNaN(d.getTime())) return '상시채용';
  const days = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  if (days < 0) return '마감';
  if (days === 0) return '오늘 마감';
  if (days <= 7) return `D-${days}`;
  return d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function appliedDate(value: string): string {
  const d = new Date(value);
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: jobsResp, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 'main'],
    queryFn: () => jobsApi.getJobs({ source: 'ALIO', data_source: 'PRODUCTION', page: 1, size: 9 }),
  });
  const { data: applications = [] } = useQuery({
    queryKey: ['applications', 'me'],
    queryFn: applicationsApi.getMyApplications,
  });
  const { data: resumes = [] } = useQuery({
    queryKey: ['resumes'],
    queryFn: resumesApi.getResumes,
  });

  const jobs = jobsResp?.items ?? [];
  const featured = jobs.slice(0, 3);
  const recommended = jobs.slice(0, 6);

  const quickInfo = [
    { label: '내 이력서', value: resumes.length, href: '/user/resumes', icon: 'file' as const },
    { label: '지원 현황', value: applications.length, href: '/user/applications', icon: 'flag' as const },
    { label: '추천 공고', value: jobsResp?.total ?? 0, href: '/user/jobs', icon: 'briefcase' as const },
    { label: 'AI 매칭', value: '보기', href: '/user/matches', icon: 'sparkle' as const },
  ];

  return (
    <div className="p-6 max-w-300 mx-auto">
      {/* Greeting */}
      <div className="mb-5">
        <h1 className="text-[22px] font-bold text-m-text tracking-tight">
          안녕하세요, {user?.name ?? '사용자'}님 👋
        </h1>
        <p className="text-[14px] text-m-muted mt-1.5">
          지금까지 <strong className="text-m-text">{applications.length}건</strong> 지원했어요. 오늘도 좋은 공고를 찾아보세요!
        </p>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4 max-lg:grid-cols-1">
        {/* Left */}
        <div className="flex flex-col gap-4 min-w-0">
          {/* AI 추천 */}
          <div className="bg-m-surface border border-m-border rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Icon name="sparkle" size={16} className="text-m-primary" />
                <h2 className="text-[15px] font-bold text-m-text">오늘의 AI 추천</h2>
              </div>
              <Link href="/user/jobs" className="text-[12px] text-m-primary hover:underline flex items-center gap-0.5">
                전체 보기 <Icon name="chevron" size={12} />
              </Link>
            </div>
            <p className="text-[12px] text-m-muted mb-4">실제 수집된 공공기관 공고에서 선별했어요.</p>

            {jobsLoading ? (
              <div className="py-10 text-center text-[13px] text-m-subtle">불러오는 중...</div>
            ) : featured.length === 0 ? (
              <div className="py-10 text-center text-[13px] text-m-subtle">표시할 공고가 없습니다.</div>
            ) : (
              <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
                {featured.map((job) => (
                  <Link
                    key={job.job_id}
                    href="/user/jobs"
                    className="border border-m-border rounded-xl p-4 hover:border-m-primary hover:bg-m-surface-alt transition-colors"
                  >
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-[12px] font-bold mb-2"
                      style={{ backgroundColor: logoColor(job.company_name) }}
                    >
                      {initials(job.company_name)}
                    </div>
                    <p className="text-[13px] font-semibold text-m-text line-clamp-2 min-h-9">{job.title}</p>
                    <p className="text-[12px] text-m-muted mt-1 truncate">{job.company_name ?? '기관명 미상'}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[11px] font-semibold text-m-primary">{deadlineLabel(job.deadline)}</span>
                      {job.location && <span className="text-[11px] text-m-subtle truncate">{job.location}</span>}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* 추천 채용공고 리스트 */}
          <div className="bg-m-surface border border-m-border rounded-2xl">
            <div className="flex items-center justify-between p-4 border-b border-m-border">
              <h3 className="text-[14px] font-semibold text-m-text">추천 채용공고</h3>
              <Link href="/user/jobs" className="text-[12px] text-m-primary hover:underline">전체 보기</Link>
            </div>
            <div className="divide-y divide-m-border">
              {recommended.map((job: JobPostingItem) => (
                <Link
                  key={job.job_id}
                  href="/user/jobs"
                  className="flex items-center gap-3 px-4 py-3 hover:bg-m-surface-alt transition-colors"
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-[11px] font-bold shrink-0"
                    style={{ backgroundColor: logoColor(job.company_name) }}
                  >
                    {initials(job.company_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-m-text truncate">{job.title}</p>
                    <p className="text-[12px] text-m-muted truncate">
                      {job.company_name ?? '기관명 미상'}{job.location ? ` · ${job.location}` : ''}
                    </p>
                  </div>
                  <span className="text-[12px] font-semibold text-m-primary shrink-0">{deadlineLabel(job.deadline)}</span>
                </Link>
              ))}
              {!jobsLoading && recommended.length === 0 && (
                <div className="px-4 py-8 text-center text-[13px] text-m-subtle">공고가 없습니다.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right */}
        <div className="flex flex-col gap-4">
          {/* 맞춤 정보 */}
          <div className="bg-m-surface border border-m-border rounded-2xl p-4">
            <p className="text-[13px] font-semibold text-m-text mb-3">{user?.name ?? '사용자'}님을 위한 맞춤 정보</p>
            <div className="grid grid-cols-2 gap-2.5">
              {quickInfo.map((q) => (
                <Link
                  key={q.label}
                  href={q.href}
                  className="rounded-xl border border-m-border p-3 hover:bg-m-surface-alt transition-colors"
                >
                  <div className="w-7 h-7 rounded-lg bg-m-primary-soft text-m-primary flex items-center justify-center mb-2">
                    <Icon name={q.icon} size={14} />
                  </div>
                  <p className="text-[11px] text-m-subtle">{q.label}</p>
                  <p className="text-[16px] font-bold text-m-text">{q.value}</p>
                </Link>
              ))}
            </div>
          </div>

          {/* 지원 현황 */}
          <div className="bg-m-surface border border-m-border rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-semibold text-m-text">지원 현황</h3>
              <Link href="/user/applications" className="text-[12px] text-m-primary hover:underline">전체 보기</Link>
            </div>
            {applications.length === 0 ? (
              <p className="text-[12px] text-m-subtle py-4 text-center">아직 지원한 공고가 없어요.</p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {applications.slice(0, 6).map((app) => {
                  const meta = APPLICATION_STATUS[app.status];
                  return (
                    <div key={app.application_id} className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: meta.color }} />
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-semibold text-m-text truncate">
                          {app.company_name ?? app.job_title}
                        </p>
                        <p className="text-[11px] text-m-subtle truncate">{meta.label} · {app.job_title}</p>
                      </div>
                      <span className="text-[11px] text-m-subtle shrink-0">{appliedDate(app.applied_at)}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 이력서 업로드 유도 */}
          <div className="bg-m-surface border border-m-border rounded-2xl p-4">
            <p className="text-[12px] font-semibold text-m-text mb-1">이력서 업데이트</p>
            <p className="text-[12px] text-m-muted leading-snug">최신 이력서를 올리면 더 잘 맞는 공고를 추천받을 수 있어요.</p>
            <Link
              href="/user/resumes"
              className="mt-3 h-8 flex items-center justify-center gap-1.5 rounded-lg bg-m-text text-white text-[12px] font-semibold hover:opacity-80 transition-opacity"
            >
              <Icon name="upload" size={13} />
              이력서 관리
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
