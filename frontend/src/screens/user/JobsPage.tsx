'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import ApplyModal from '../../components/jobs/ApplyModal';
import { showToast } from '../../components/ui/Toast';
import { jobsApi } from '../../api/jobs';
import { applicationsApi } from '../../api/applications';
import type { JobPostingItem } from '../../api/types';

const PAGE_SIZE = 20;

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
  return d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) + ' 마감';
}

interface Filters {
  region: string;
  education: string;
  employment_type: string;
  ncs_category: string;
  keyword: string;
}

const EMPTY_FILTERS: Filters = {
  region: '',
  education: '',
  employment_type: '',
  ncs_category: '',
  keyword: '',
};

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`h-10 px-3 rounded-lg border border-m-border bg-m-surface text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary ${
        value ? 'text-m-text font-medium' : 'text-m-subtle'
      }`}
    >
      <option value="">{label}</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}

export default function JobsPage() {
  const router = useRouter();
  const [draft, setDraft] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const [applyJob, setApplyJob] = useState<JobPostingItem | null>(null);

  const { data: options } = useQuery({
    queryKey: ['jobs', 'filter-options'],
    queryFn: jobsApi.getFilterOptions,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['jobs', 'list', applied, page],
    queryFn: () =>
      jobsApi.getJobs({
        region: applied.region,
        education: applied.education,
        employment_type: applied.employment_type,
        ncs_category: applied.ncs_category,
        keyword: applied.keyword,
        page,
        size: PAGE_SIZE,
      }),
  });

  const { data: myApplications = [] } = useQuery({
    queryKey: ['applications', 'me'],
    queryFn: applicationsApi.getMyApplications,
  });
  const appliedJobIds = new Set(myApplications.map((a) => a.job_id));

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function applyFilters() {
    setApplied(draft);
    setPage(1);
  }

  function resetFilters() {
    setDraft(EMPTY_FILTERS);
    setApplied(EMPTY_FILTERS);
    setPage(1);
  }

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-[22px] font-bold text-m-text tracking-tight">채용공고</h1>
        <p className="text-[13px] text-m-muted mt-1">
          전체 <strong className="text-m-primary">{total.toLocaleString()}</strong>건의 공고
        </p>
      </div>

      {/* 필터 바 */}
      <div className="bg-m-surface border border-m-border rounded-2xl p-4 mb-5">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            label="지역 전체"
            value={draft.region}
            options={options?.regions ?? []}
            onChange={(v) => setDraft((p) => ({ ...p, region: v }))}
          />
          <FilterSelect
            label="학력 전체"
            value={draft.education}
            options={options?.educations ?? []}
            onChange={(v) => setDraft((p) => ({ ...p, education: v }))}
          />
          <FilterSelect
            label="직종 전체"
            value={draft.ncs_category}
            options={options?.job_categories ?? []}
            onChange={(v) => setDraft((p) => ({ ...p, ncs_category: v }))}
          />
          <FilterSelect
            label="고용형태 전체"
            value={draft.employment_type}
            options={options?.employment_types ?? []}
            onChange={(v) => setDraft((p) => ({ ...p, employment_type: v }))}
          />
          <div className="relative flex-1 min-w-50">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
              <Icon name="search" size={14} />
            </div>
            <input
              value={draft.keyword}
              onChange={(e) => setDraft((p) => ({ ...p, keyword: e.target.value }))}
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              placeholder="공고명, 기관명 검색"
              className="w-full h-10 pl-9 pr-3 rounded-lg border border-m-border bg-m-surface text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            />
          </div>
          <button
            onClick={applyFilters}
            className="h-10 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors"
          >
            검색
          </button>
          <button
            onClick={resetFilters}
            className="h-10 px-3 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors flex items-center gap-1"
          >
            <Icon name="x" size={13} /> 초기화
          </button>
        </div>
      </div>

      {/* 리스트 (가로로 넓게) */}
      <div className="bg-m-surface border border-m-border rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center text-[13px] text-m-subtle">불러오는 중...</div>
        ) : isError ? (
          <div className="py-20 text-center text-[13px] text-m-subtle">공고를 불러올 수 없습니다.</div>
        ) : items.length === 0 ? (
          <div className="py-20 text-center text-[13px] text-m-subtle">조건에 맞는 공고가 없습니다.</div>
        ) : (
          <div className="divide-y divide-m-border">
            {items.map((job) => (
              <div
                key={job.job_id}
                onClick={() => router.push(`/user/jobs/${job.job_id}`)}
                className="flex items-center gap-4 px-5 py-4 hover:bg-m-surface-alt transition-colors cursor-pointer"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-[14px] font-bold shrink-0"
                  style={{ backgroundColor: logoColor(job.company_name) }}
                >
                  {initials(job.company_name)}
                </div>
                <div className="w-48 shrink-0 min-w-0">
                  <p className="text-[13px] font-semibold text-m-text truncate">
                    {job.company_name ?? '기관명 미상'}
                  </p>
                  <p className="text-[11px] text-m-subtle truncate">{job.source}</p>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-semibold text-m-text truncate">{job.title}</p>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-[12px] text-m-muted">
                    {job.ncs_category && <span>{job.ncs_category}</span>}
                    {job.career_level && <span>· {job.career_level}</span>}
                    {job.education && <span>· {job.education}</span>}
                  </div>
                </div>
                <div className="w-32 shrink-0 text-[12px] text-m-muted truncate hidden md:block">
                  {job.location && (
                    <span className="flex items-center gap-1">
                      <Icon name="map-pin" size={12} /> {job.location}
                    </span>
                  )}
                  {job.employment_type && <span className="text-[11px] text-m-subtle">{job.employment_type}</span>}
                </div>
                <div className="w-28 shrink-0 text-right">
                  <p className="text-[12px] font-semibold text-m-primary mb-1.5">
                    {deadlineLabel(job.deadline)}
                  </p>
                  {appliedJobIds.has(job.job_id) ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        showToast('이미 지원한 공고입니다.', 'info');
                      }}
                      className="h-7 px-3 rounded-lg border border-m-border text-m-subtle text-[12px] font-semibold hover:bg-m-surface-alt transition-colors"
                    >
                      지원완료
                    </button>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setApplyJob(job);
                      }}
                      className="h-7 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover transition-colors"
                    >
                      입사지원
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 페이지네이션 */}
        {!isLoading && !isError && total > PAGE_SIZE && (
          <div className="flex items-center justify-between p-4 border-t border-m-border">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="h-8 px-4 rounded-lg border border-m-border text-[12px] font-medium text-m-muted disabled:opacity-40"
            >
              이전
            </button>
            <span className="text-[12px] text-m-subtle">{page} / {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="h-8 px-4 rounded-lg border border-m-border text-[12px] font-medium text-m-muted disabled:opacity-40"
            >
              다음
            </button>
          </div>
        )}
      </div>

      {applyJob && <ApplyModal job={applyJob} onClose={() => setApplyJob(null)} />}
    </div>
  );
}
