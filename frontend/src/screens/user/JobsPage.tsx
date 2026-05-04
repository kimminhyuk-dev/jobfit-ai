'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { jobsApi } from '../../api/jobs';
import type { JobPostingItem } from '../../api/types';

const PAGE_SIZE = 20;

const SOURCE_TABS = [
  { label: '공공기관 (ALIO)', source: 'ALIO', dataSource: 'PRODUCTION' },
  { label: 'IT 기업 (Mock)', source: undefined, dataSource: 'MOCK' },
];

const LOGO_COLORS = ['#1d4ed8', '#0f766e', '#7c3aed', '#ea580c', '#0284c7', '#15803d', '#b45309'];

function getInitials(name: string | null): string {
  if (!name) return '?';
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2);
  return words[0][0] + words[words.length - 1][0];
}

function getLogoColor(name: string | null): string {
  if (!name) return '#6b7280';
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffffffff;
  return LOGO_COLORS[Math.abs(hash) % LOGO_COLORS.length];
}

function formatDeadline(deadline: string | null): string {
  if (!deadline) return '상시채용';
  const date = new Date(deadline);
  if (isNaN(date.getTime())) return '상시채용';
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  if (diffMs < 0) return '마감';
  const days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  if (days === 0) return '오늘 마감';
  if (days <= 7) return `D-${days}`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) + ' 마감';
}

function formatPostedAt(postedAt: string | null): string {
  if (!postedAt) return '';
  const date = new Date(postedAt);
  if (isNaN(date.getTime())) return '';
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days === 0) return '오늘';
  if (days === 1) return '1일 전';
  if (days < 30) return `${days}일 전`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function InfoRow({ icon, label, value }: { icon: string; label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 text-[13px]">
      <span className="text-m-subtle mt-0.5 shrink-0">
        <Icon name={icon as Parameters<typeof Icon>[0]['name']} size={14} />
      </span>
      <div>
        <span className="text-m-subtle text-[11px]">{label}</span>
        <p className="text-m-muted">{value}</p>
      </div>
    </div>
  );
}

export default function JobsPage() {
  const [selected, setSelected] = useState<JobPostingItem | null>(null);
  const [query, setQuery] = useState('');
  const [tabIdx, setTabIdx] = useState(0);
  const [page, setPage] = useState(1);

  const tab = SOURCE_TABS[tabIdx];

  const { data, isLoading, isError } = useQuery({
    queryKey: ['jobs', tab.source, tab.dataSource, page],
    queryFn: () =>
      jobsApi.getJobs({
        source: tab.source,
        data_source: tab.dataSource,
        page,
        size: PAGE_SIZE,
      }),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const filtered = items.filter(
    (j) =>
      !query ||
      j.title.includes(query) ||
      (j.company_name ?? '').includes(query),
  );

  function handleTabChange(idx: number) {
    setTabIdx(idx);
    setPage(1);
    setSelected(null);
    setQuery('');
  }

  function handlePageChange(next: number) {
    setPage(next);
    setSelected(null);
  }

  return (
    <div className="flex h-full min-h-0">
      {/* List panel */}
      <div className="flex flex-col border-r border-m-border bg-m-surface w-95 shrink-0">
        {/* Header */}
        <div className="p-4 border-b border-m-border">
          <h1 className="text-[16px] font-bold text-m-text mb-3">채용공고</h1>

          {/* Source tabs */}
          <div className="flex gap-1 mb-3 p-1 rounded-lg bg-m-surface-alt">
            {SOURCE_TABS.map((t, i) => (
              <button
                key={i}
                onClick={() => handleTabChange(i)}
                className={`flex-1 h-7 rounded-md text-[12px] font-medium transition-colors ${
                  tabIdx === i
                    ? 'bg-white text-m-primary shadow-sm'
                    : 'text-m-subtle hover:text-m-muted'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
              <Icon name="search" size={14} />
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="공고명, 기관명 검색"
              className="w-full h-9 pl-9 pr-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            />
          </div>
          <p className="text-[11px] text-m-subtle mt-2">
            {total > 0 ? `전체 ${total}개 · 이 페이지 ${filtered.length}개` : `${filtered.length}개 공고`}
          </p>
        </div>

        {/* Job list */}
        <div className="flex-1 overflow-auto scrollbar-thin divide-y divide-m-border">
          {isLoading ? (
            <div className="flex items-center justify-center h-32 text-m-subtle">
              <p className="text-[13px]">불러오는 중...</p>
            </div>
          ) : isError ? (
            <div className="flex items-center justify-center h-32 text-m-subtle">
              <p className="text-[13px]">불러올 수 없습니다.</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-m-subtle">
              <p className="text-[13px]">공고가 없습니다.</p>
            </div>
          ) : (
            filtered.map((job) => (
              <button
                key={job.job_id}
                onClick={() => setSelected(job)}
                className={`w-full p-4 text-left hover:bg-m-surface-alt transition-colors ${
                  selected?.job_id === job.job_id
                    ? 'bg-m-primary-soft border-l-2 border-m-primary'
                    : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-[12px] font-bold shrink-0"
                    style={{ backgroundColor: getLogoColor(job.company_name) }}
                  >
                    {getInitials(job.company_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-m-text truncate">{job.title}</p>
                    <p className="text-[12px] text-m-muted">{job.company_name ?? '기관명 미상'}</p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      {job.location && (
                        <span className="text-[11px] text-m-subtle flex items-center gap-1">
                          <Icon name="map-pin" size={11} /> {job.location}
                        </span>
                      )}
                      {job.employment_type && (
                        <span className="text-[11px] text-m-subtle">{job.employment_type}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className="text-[12px] font-semibold text-m-primary">
                      {formatDeadline(job.deadline)}
                    </span>
                    {job.posted_at && (
                      <span className="text-[11px] text-m-subtle">
                        {formatPostedAt(job.posted_at)}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Pagination */}
        {!isLoading && !isError && total > PAGE_SIZE && (
          <div className="p-3 border-t border-m-border flex items-center justify-between">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="h-7 px-3 rounded-lg border text-[12px] font-medium disabled:opacity-40 text-m-muted border-m-border"
            >
              이전
            </button>
            <span className="text-[12px] text-m-subtle">{page} / {totalPages}</span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages}
              className="h-7 px-3 rounded-lg border text-[12px] font-medium disabled:opacity-40 text-m-muted border-m-border"
            >
              다음
            </button>
          </div>
        )}
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-auto scrollbar-thin">
        {selected ? (
          <div className="p-6">
            {/* Header */}
            <div className="flex items-start gap-5 mb-6">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-[18px] font-bold shrink-0"
                style={{ backgroundColor: getLogoColor(selected.company_name) }}
              >
                {getInitials(selected.company_name)}
              </div>
              <div className="flex-1">
                <h2 className="text-[20px] font-bold text-m-text tracking-tight">
                  {selected.title}
                </h2>
                <p className="text-[14px] text-m-muted mt-0.5">
                  {selected.company_name ?? '기관명 미상'}
                </p>
                <div className="flex flex-wrap gap-3 mt-2 text-[13px] text-m-muted">
                  {selected.location && (
                    <span className="flex items-center gap-1">
                      <Icon name="map-pin" size={13} />
                      {selected.location}
                    </span>
                  )}
                  {selected.employment_type && (
                    <span className="flex items-center gap-1">
                      <Icon name="briefcase" size={13} />
                      {selected.employment_type}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Icon name="building" size={13} />
                    {selected.source}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                {selected.source_url ? (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="h-9 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors flex items-center gap-1.5"
                  >
                    공고 보기 <Icon name="arrow" size={14} />
                  </a>
                ) : (
                  <button
                    disabled
                    className="h-9 px-4 rounded-lg bg-m-surface border border-m-border text-[13px] font-medium text-m-subtle cursor-not-allowed"
                  >
                    공고 보기
                  </button>
                )}
              </div>
            </div>

            {/* Job info */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-4">공고 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <InfoRow icon="map-pin" label="근무지" value={selected.location} />
                <InfoRow icon="briefcase" label="고용형태" value={selected.employment_type} />
                <InfoRow icon="user" label="경력" value={selected.career_level} />
                <InfoRow icon="building" label="학력" value={selected.education} />
                <InfoRow icon="building" label="기관유형" value={selected.organization_type} />
                <InfoRow icon="building" label="주무부처" value={selected.ministry} />
                <InfoRow icon="briefcase" label="NCS 분류" value={selected.ncs_category} />
                <div className="flex items-start gap-2 text-[13px]">
                  <span className="text-m-subtle mt-0.5 shrink-0">
                    <Icon name="briefcase" size={14} />
                  </span>
                  <div>
                    <span className="text-m-subtle text-[11px]">급여</span>
                    <p className="text-m-muted">공고문 참조</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Deadline */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">접수 기간</h3>
              <div className="flex items-center gap-6 text-[13px] text-m-muted">
                {selected.posted_at && (
                  <div>
                    <p className="text-[11px] text-m-subtle mb-0.5">등록일</p>
                    <p>{new Date(selected.posted_at).toLocaleDateString('ko-KR')}</p>
                  </div>
                )}
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">마감일</p>
                  <p className={selected.deadline ? 'text-m-primary font-semibold' : ''}>
                    {selected.deadline
                      ? new Date(selected.deadline).toLocaleDateString('ko-KR')
                      : '상시채용'}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">남은 기간</p>
                  <p className="font-semibold">{formatDeadline(selected.deadline)}</p>
                </div>
              </div>
            </div>

            {/* Source info */}
            <div className="bg-m-surface-alt border border-m-border rounded-2xl p-4 flex gap-3">
              <Icon name="building" size={16} className="shrink-0 mt-0.5 text-m-subtle" />
              <div>
                <p className="text-[13px] font-semibold text-m-text mb-1">수집 출처</p>
                <p className="text-[13px] text-m-muted">
                  {selected.source} · 수집일{' '}
                  {new Date(selected.collected_at).toLocaleDateString('ko-KR')}
                </p>
                {selected.source_url && (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[12px] text-m-primary hover:underline mt-1 block"
                  >
                    원문 공고 바로가기 →
                  </a>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-m-subtle">
            <p className="text-[14px]">공고를 선택하세요</p>
          </div>
        )}
      </div>
    </div>
  );
}
