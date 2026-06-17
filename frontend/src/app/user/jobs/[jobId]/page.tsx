'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Icon from '../../../../components/ui/Icon';
import ApplyModal from '../../../../components/jobs/ApplyModal';
import { showToast } from '../../../../components/ui/Toast';
import { jobsApi } from '../../../../api/jobs';
import { applicationsApi } from '../../../../api/applications';

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

function dday(deadline: string | null): string {
  if (!deadline) return '상시채용';
  const d = new Date(deadline);
  if (isNaN(d.getTime())) return '상시채용';
  const days = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  if (days < 0) return '마감';
  if (days === 0) return '오늘 마감';
  return `D-${days}`;
}

function dateStr(value: string | null): string {
  if (!value) return '-';
  const d = new Date(value);
  return isNaN(d.getTime()) ? '-' : d.toLocaleDateString('ko-KR');
}

function InfoRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex gap-3 py-2.5 border-b border-m-border last:border-0">
      <span className="w-24 shrink-0 text-[12px] text-m-subtle">{label}</span>
      <span className="text-[13px] text-m-text">{value}</span>
    </div>
  );
}

export default function JobDetailRoutePage() {
  const params = useParams();
  const router = useRouter();
  const jobId = Number(params.jobId);
  const [showApply, setShowApply] = useState(false);

  const { data: job, isLoading, isError } = useQuery({
    queryKey: ['jobs', 'detail', jobId],
    queryFn: () => jobsApi.getJob(jobId),
    enabled: Number.isFinite(jobId),
  });

  const { data: myApplications = [] } = useQuery({
    queryKey: ['applications', 'me'],
    queryFn: applicationsApi.getMyApplications,
  });
  const alreadyApplied = myApplications.some(
    (a) => a.job_id === jobId && a.status !== 'CANCELED',
  );

  if (isLoading) {
    return <div className="p-10 text-center text-[13px] text-m-subtle">공고를 불러오는 중...</div>;
  }
  if (isError || !job) {
    return (
      <div className="p-10 text-center">
        <p className="text-[14px] text-m-muted mb-4">공고를 불러올 수 없습니다.</p>
        <button
          onClick={() => router.push('/user/jobs')}
          className="h-9 px-4 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt"
        >
          목록으로
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <button
        onClick={() => router.push('/user/jobs')}
        className="mb-4 flex items-center gap-1 text-[13px] text-m-muted hover:text-m-text transition-colors"
      >
        <Icon name="arrow-left" size={15} /> 채용공고 목록
      </button>

      {/* 상단 헤더 (가로로 넓게) */}
      <div className="bg-m-surface border border-m-border rounded-2xl p-6 mb-4">
        <div className="flex items-start gap-5">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-[20px] font-bold shrink-0"
            style={{ backgroundColor: logoColor(job.company_name) }}
          >
            {initials(job.company_name)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] text-m-muted">{job.company_name ?? '기관명 미상'}</p>
            <h1 className="text-[22px] font-bold text-m-text tracking-tight mt-0.5">{job.title}</h1>
            <div className="flex flex-wrap gap-2 mt-3">
              {job.ncs_category && (
                <span className="text-[12px] px-2.5 py-1 rounded-full bg-m-primary-soft text-m-primary font-medium">
                  {job.ncs_category}
                </span>
              )}
              {job.career_level && (
                <span className="text-[12px] px-2.5 py-1 rounded-full bg-m-surface-alt text-m-muted">
                  {job.career_level}
                </span>
              )}
              {job.location && (
                <span className="text-[12px] px-2.5 py-1 rounded-full bg-m-surface-alt text-m-muted flex items-center gap-1">
                  <Icon name="map-pin" size={11} /> {job.location}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <span className="text-[15px] font-bold text-m-danger">{dday(job.deadline)}</span>
            {alreadyApplied ? (
              <button
                onClick={() => showToast('이미 지원한 공고입니다.', 'info')}
                className="h-10 px-5 rounded-lg border border-m-border text-m-subtle text-[13px] font-semibold hover:bg-m-surface-alt transition-colors flex items-center gap-1.5"
              >
                <Icon name="check" size={14} /> 지원 완료
              </button>
            ) : (
              <button
                onClick={() => setShowApply(true)}
                className="h-10 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors flex items-center gap-1.5"
              >
                <Icon name="upload" size={14} /> 이력서 보내기
              </button>
            )}
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="h-9 px-4 rounded-lg border border-m-border text-[12px] font-semibold text-m-muted hover:bg-m-surface-alt transition-colors flex items-center gap-1.5"
              >
                원문 보기 <Icon name="arrow" size={13} />
              </a>
            )}
          </div>
        </div>
      </div>

      {/* 본문 2단 (가로로 넓게) */}
      <div className="grid grid-cols-[1fr_340px] gap-4 max-lg:grid-cols-1">
        {/* 직무 내용 */}
        <div className="bg-m-surface border border-m-border rounded-2xl p-6">
          <h2 className="text-[15px] font-semibold text-m-text mb-4">직무 내용</h2>
          {job.raw_content ? (
            <p className="text-[13px] text-m-muted leading-relaxed whitespace-pre-wrap">{job.raw_content}</p>
          ) : (
            <p className="text-[13px] text-m-subtle">
              상세 직무 내용은 원문 공고에서 확인하세요.
              {job.source_url && (
                <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-m-primary hover:underline ml-1">
                  원문 보기 →
                </a>
              )}
            </p>
          )}
        </div>

        {/* 우측 정보 */}
        <div className="flex flex-col gap-4">
          <div className="bg-m-surface border border-m-border rounded-2xl p-5">
            <h3 className="text-[14px] font-semibold text-m-text mb-2">모집 조건</h3>
            <InfoRow label="근무지역" value={job.location} />
            <InfoRow label="고용형태" value={job.employment_type} />
            <InfoRow label="경력" value={job.career_level} />
            <InfoRow label="학력" value={job.education} />
            <InfoRow label="직종" value={job.ncs_category} />
            <InfoRow label="기관유형" value={job.organization_type} />
            <InfoRow label="주무부처" value={job.ministry} />
          </div>

          <div className="bg-m-surface border border-m-border rounded-2xl p-5">
            <h3 className="text-[14px] font-semibold text-m-text mb-2">접수 기간</h3>
            <InfoRow label="등록일" value={dateStr(job.posted_at)} />
            <InfoRow label="마감일" value={job.deadline ? dateStr(job.deadline) : '상시채용'} />
            <InfoRow label="남은 기간" value={dday(job.deadline)} />
          </div>

          <div className="bg-m-surface-alt border border-m-border rounded-2xl p-4 text-[12px] text-m-muted">
            <p className="font-semibold text-m-text mb-1">수집 출처</p>
            <p>{job.source} · 수집일 {dateStr(job.collected_at)}</p>
          </div>
        </div>
      </div>

      {showApply && <ApplyModal job={job} onClose={() => setShowApply(false)} />}
    </div>
  );
}
