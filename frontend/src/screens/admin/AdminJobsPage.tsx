'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { adminApi } from '../../api/admin';
import type { JobPostingItem } from '../../api/types';

const LOGO_COLORS = ['#1d4ed8', '#0f766e', '#7c3aed', '#ea580c', '#0284c7', '#15803d', '#b45309'];

const SOURCES = ['전체', 'ALIO', 'WORK24', 'SARAMIN', 'MANUAL'] as const;
type SourceFilter = (typeof SOURCES)[number];

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

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; bg: string; color: string }> = {
    OPEN: { label: '공개', bg: '#f0fdf4', color: '#15803d' },
    CLOSED: { label: '마감', bg: '#f1f5f9', color: '#64748b' },
    EXPIRED: { label: '만료', bg: '#fff7ed', color: '#c2410c' },
    HIDDEN: { label: '숨김', bg: '#faf5ff', color: '#7c3aed' },
  };
  const s = map[status] ?? { label: status, bg: '#f1f5f9', color: '#64748b' };
  return (
    <span
      className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
      style={{ background: s.bg, color: s.color }}
    >
      {s.label}
    </span>
  );
}

function InfoRow({ icon, label, value }: { icon: string; label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 text-[13px]">
      <span className="mt-0.5 shrink-0" style={{ color: '#94a3b8' }}>
        <Icon name={icon as Parameters<typeof Icon>[0]['name']} size={14} />
      </span>
      <div>
        <span className="text-[11px]" style={{ color: '#94a3b8' }}>{label}</span>
        <p style={{ color: '#475569' }}>{value}</p>
      </div>
    </div>
  );
}

export default function AdminJobsPage() {
  const [selected, setSelected] = useState<JobPostingItem | null>(null);
  const [query, setQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('ALIO');

  const apiSource = sourceFilter === '전체' ? undefined : sourceFilter;

  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'jobs', apiSource],
    queryFn: () => adminApi.getJobs({ source: apiSource, size: 100 }),
  });

  const items = data?.items ?? [];
  const filtered = items.filter(
    (j) =>
      !query ||
      j.title.includes(query) ||
      (j.company_name ?? '').includes(query),
  );

  return (
    <div className="flex h-full min-h-0">
      {/* List panel */}
      <div className="flex flex-col border-r w-96 shrink-0 bg-white" style={{ borderColor: '#e2e8f0' }}>
        {/* Header */}
        <div className="p-4 border-b" style={{ borderColor: '#e2e8f0' }}>
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-[16px] font-bold" style={{ color: '#0f172a' }}>채용공고 관리</h1>
            <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#fef3c7', color: '#92400e' }}>
              관리자
            </span>
          </div>

          {/* Source filter tabs */}
          <div className="flex gap-1 mb-3 flex-wrap">
            {SOURCES.map((src) => (
              <button
                key={src}
                onClick={() => { setSourceFilter(src); setSelected(null); }}
                className="text-[11px] px-2.5 py-1 rounded-lg font-medium transition-colors"
                style={
                  sourceFilter === src
                    ? { background: '#2563eb', color: '#fff' }
                    : { background: '#f1f5f9', color: '#475569' }
                }
              >
                {src}
              </button>
            ))}
          </div>

          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#94a3b8' }}>
              <Icon name="search" size={14} />
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="공고명, 기관명 검색"
              className="w-full h-9 pl-9 pr-3 rounded-lg text-[13px] focus:outline-none"
              style={{ border: '1px solid #e2e8f0', background: '#f1f5f9', color: '#0f172a' }}
            />
          </div>
          <p className="text-[11px] mt-2" style={{ color: '#94a3b8' }}>
            {isLoading ? '불러오는 중...' : `${filtered.length}개 공고`}
          </p>
        </div>

        {/* Job list */}
        <div className="flex-1 overflow-auto divide-y" style={{ borderColor: '#e2e8f0' }}>
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="p-4 animate-pulse">
                <div className="flex gap-3">
                  <div className="w-9 h-9 rounded-xl shrink-0" style={{ background: '#e2e8f0' }} />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 rounded w-3/4" style={{ background: '#e2e8f0' }} />
                    <div className="h-2 rounded w-1/2" style={{ background: '#e2e8f0' }} />
                  </div>
                </div>
              </div>
            ))
          ) : isError ? (
            <div className="flex items-center justify-center h-32 text-[13px]" style={{ color: '#94a3b8' }}>
              데이터를 불러올 수 없습니다.
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-[13px]" style={{ color: '#94a3b8' }}>
              공고가 없습니다.
            </div>
          ) : (
            filtered.map((job) => (
              <button
                key={job.job_id}
                onClick={() => setSelected(job)}
                className="w-full p-4 text-left transition-colors hover:bg-slate-50"
                style={
                  selected?.job_id === job.job_id
                    ? { background: '#eff6ff', borderLeft: '2px solid #2563eb' }
                    : {}
                }
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-[12px] font-bold shrink-0"
                    style={{ backgroundColor: getLogoColor(job.company_name) }}
                  >
                    {getInitials(job.company_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <p className="text-[13px] font-semibold truncate" style={{ color: '#0f172a' }}>{job.title}</p>
                      <StatusBadge status={job.status} />
                    </div>
                    <p className="text-[12px]" style={{ color: '#64748b' }}>{job.company_name ?? '기관명 미상'}</p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {job.location && (
                        <span className="text-[11px] flex items-center gap-0.5" style={{ color: '#94a3b8' }}>
                          <Icon name="map-pin" size={11} /> {job.location}
                        </span>
                      )}
                      <span className="text-[11px] px-1.5 py-0.5 rounded font-medium" style={{ background: '#f1f5f9', color: '#64748b' }}>
                        {job.source}
                      </span>
                    </div>
                  </div>
                  <span className="text-[12px] font-semibold shrink-0" style={{ color: '#2563eb' }}>
                    {formatDeadline(job.deadline)}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-auto" style={{ background: '#f6f8fb' }}>
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
                <div className="flex items-center gap-2 mb-0.5">
                  <h2 className="text-[20px] font-bold tracking-tight" style={{ color: '#0f172a' }}>
                    {selected.title}
                  </h2>
                  <StatusBadge status={selected.status} />
                </div>
                <p className="text-[14px]" style={{ color: '#64748b' }}>
                  {selected.company_name ?? '기관명 미상'}
                </p>
                <div className="flex flex-wrap gap-3 mt-2 text-[13px]" style={{ color: '#64748b' }}>
                  {selected.location && (
                    <span className="flex items-center gap-1">
                      <Icon name="map-pin" size={13} /> {selected.location}
                    </span>
                  )}
                  {selected.employment_type && (
                    <span className="flex items-center gap-1">
                      <Icon name="briefcase" size={13} /> {selected.employment_type}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Icon name="building" size={13} /> {selected.source}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                {selected.source_url ? (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold flex items-center gap-1.5 transition-colors"
                    style={{ background: '#2563eb' }}
                  >
                    원문 보기 <Icon name="arrow" size={14} />
                  </a>
                ) : (
                  <button
                    disabled
                    className="h-9 px-4 rounded-lg text-[13px] font-medium cursor-not-allowed"
                    style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#94a3b8' }}
                  >
                    원문 보기
                  </button>
                )}
              </div>
            </div>

            {/* Job info */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <h3 className="text-[14px] font-semibold mb-4" style={{ color: '#0f172a' }}>공고 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <InfoRow icon="map-pin" label="근무지" value={selected.location} />
                <InfoRow icon="briefcase" label="고용형태" value={selected.employment_type} />
                <InfoRow icon="user" label="경력" value={selected.career_level} />
                <InfoRow icon="building" label="학력" value={selected.education} />
                <InfoRow icon="building" label="기관유형" value={selected.organization_type} />
                <InfoRow icon="building" label="주무부처" value={selected.ministry} />
                <InfoRow icon="briefcase" label="NCS 분류" value={selected.ncs_category} />
              </div>
            </div>

            {/* Deadline */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <h3 className="text-[14px] font-semibold mb-3" style={{ color: '#0f172a' }}>접수 기간</h3>
              <div className="flex items-center gap-6 text-[13px]" style={{ color: '#475569' }}>
                {selected.posted_at && (
                  <div>
                    <p className="text-[11px] mb-0.5" style={{ color: '#94a3b8' }}>등록일</p>
                    <p>{new Date(selected.posted_at).toLocaleDateString('ko-KR')}</p>
                  </div>
                )}
                <div>
                  <p className="text-[11px] mb-0.5" style={{ color: '#94a3b8' }}>마감일</p>
                  <p className={selected.deadline ? 'font-semibold' : ''} style={selected.deadline ? { color: '#2563eb' } : {}}>
                    {selected.deadline
                      ? new Date(selected.deadline).toLocaleDateString('ko-KR')
                      : '상시채용'}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] mb-0.5" style={{ color: '#94a3b8' }}>남은 기간</p>
                  <p className="font-semibold">{formatDeadline(selected.deadline)}</p>
                </div>
              </div>
            </div>

            {/* Admin meta */}
            <div className="rounded-2xl p-4 border" style={{ background: '#f8fafc', borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-2" style={{ color: '#0f172a' }}>수집 메타</p>
              <div className="grid grid-cols-2 gap-y-1.5 text-[12px]" style={{ color: '#64748b' }}>
                <span>출처</span>
                <span className="font-medium">{selected.source}</span>
                <span>수집일</span>
                <span>{new Date(selected.collected_at).toLocaleDateString('ko-KR')}</span>
                {selected.source_job_id && (
                  <>
                    <span>공고 ID</span>
                    <span className="font-mono break-all">{selected.source_job_id}</span>
                  </>
                )}
                {selected.source_url && (
                  <>
                    <span>원문 URL</span>
                    <a
                      href={selected.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="truncate hover:underline"
                      style={{ color: '#2563eb' }}
                    >
                      {selected.source_url}
                    </a>
                  </>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-[14px]" style={{ color: '#94a3b8' }}>
            공고를 선택하세요
          </div>
        )}
      </div>
    </div>
  );
}
