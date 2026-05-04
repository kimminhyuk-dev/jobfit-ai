'use client';

import { useState } from 'react';
import Icon from '../../components/ui/Icon';
import { mockItJobs, MOCK_JOB_CATEGORIES } from '../../api/mock/mockItJobs';
import type { MockJobItem } from '../../api/mock/mockItJobs';

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2);
  return words[0][0] + words[words.length - 1][0];
}

const LOGO_COLORS = ['#1d4ed8', '#0f766e', '#7c3aed', '#ea580c', '#0284c7', '#15803d', '#b45309', '#be185d'];

function getLogoColor(name: string): string {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffffffff;
  return LOGO_COLORS[Math.abs(hash) % LOGO_COLORS.length];
}

function formatDeadline(deadline: string): string {
  const date = new Date(deadline);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  if (diffMs < 0) return '마감';
  const days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  if (days <= 7) return `D-${days}`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function formatSalary(min: number, max: number): string {
  return `${min.toLocaleString()} ~ ${max.toLocaleString()}만`;
}

const CATEGORY_COLORS: Record<string, { bg: string; color: string }> = {
  '백엔드':      { bg: '#eff6ff', color: '#1d4ed8' },
  '프론트엔드':  { bg: '#f0fdf4', color: '#15803d' },
  'AI · ML':     { bg: '#fdf4ff', color: '#7c3aed' },
  'DevOps · SRE':{ bg: '#fff7ed', color: '#c2410c' },
  '모바일':      { bg: '#ecfdf5', color: '#0f766e' },
  '데이터':      { bg: '#fffbeb', color: '#b45309' },
  'QA · 보안':   { bg: '#fef2f2', color: '#b91c1c' },
  '게임':        { bg: '#f5f3ff', color: '#6d28d9' },
};

function CategoryBadge({ category }: { category: string }) {
  const style = CATEGORY_COLORS[category] ?? { bg: '#f1f5f9', color: '#64748b' };
  return (
    <span
      className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
      style={{ background: style.bg, color: style.color }}
    >
      {category}
    </span>
  );
}

const CATS = MOCK_JOB_CATEGORIES;

export default function AdminMockJobsPage() {
  const [selected, setSelected] = useState<MockJobItem | null>(null);
  const [catIdx, setCatIdx] = useState(0);
  const [query, setQuery] = useState('');

  const filtered = mockItJobs.filter((job) => {
    const matchCat = catIdx === 0 || job.job_category === CATS[catIdx];
    const q = query.toLowerCase();
    const matchQ =
      !q ||
      job.title.toLowerCase().includes(q) ||
      job.company_name.toLowerCase().includes(q) ||
      job.tech_stack.some((t) => t.toLowerCase().includes(q));
    return matchCat && matchQ;
  });

  // stats
  const totalJobs = mockItJobs.length;
  const catCounts = CATS.slice(1).map((cat) => ({
    cat,
    count: mockItJobs.filter((j) => j.job_category === cat).length,
  }));
  const avgSalary = Math.round(
    mockItJobs.reduce((sum, j) => sum + (j.min_salary + j.max_salary) / 2, 0) / mockItJobs.length,
  );

  return (
    <div className="flex h-full min-h-0">
      {/* Left: list */}
      <div className="flex flex-col border-r bg-white shrink-0" style={{ width: 480, borderColor: '#e2e8f0' }}>
        {/* Header */}
        <div className="p-4 border-b" style={{ borderColor: '#e2e8f0' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold" style={{ color: '#0f172a' }}>
                Mock 채용공고
              </h2>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold" style={{ background: '#fef9c3', color: '#92400e' }}>
                MOCK · WORK24
              </span>
            </div>
            <span className="text-[12px] font-medium" style={{ color: '#64748b' }}>
              총 {totalJobs}건
            </span>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="p-2 rounded-lg" style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <p className="text-[10px] font-medium" style={{ color: '#94a3b8' }}>총 공고</p>
              <p className="text-[18px] font-bold" style={{ color: '#0f172a' }}>{totalJobs}</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <p className="text-[10px] font-medium" style={{ color: '#94a3b8' }}>평균 연봉</p>
              <p className="text-[18px] font-bold" style={{ color: '#2563eb' }}>{avgSalary.toLocaleString()}만</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <p className="text-[10px] font-medium" style={{ color: '#94a3b8' }}>카테고리</p>
              <p className="text-[18px] font-bold" style={{ color: '#0f172a' }}>{CATS.length - 1}개</p>
            </div>
          </div>

          {/* Category filter */}
          <div className="flex gap-1 overflow-x-auto pb-1 mb-3" style={{ scrollbarWidth: 'none' }}>
            {CATS.map((cat, i) => (
              <button
                key={cat}
                onClick={() => { setCatIdx(i); setSelected(null); }}
                className="shrink-0 h-7 px-2.5 rounded-lg text-[11px] font-medium transition-colors whitespace-nowrap"
                style={{
                  background: catIdx === i ? '#2563eb' : '#f1f5f9',
                  color: catIdx === i ? '#fff' : '#64748b',
                }}
              >
                {cat}
                {i > 0 && (
                  <span className="ml-1 opacity-70">
                    {mockItJobs.filter((j) => j.job_category === cat).length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#94a3b8' }}>
              <Icon name="search" size={13} />
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="직무, 회사, 기술스택 검색"
              className="w-full h-8 pl-8 pr-3 rounded-lg text-[12px] focus:outline-none"
              style={{ border: '1px solid #e2e8f0', background: '#f8fafc', color: '#0f172a' }}
            />
          </div>
          <p className="text-[11px] mt-1.5" style={{ color: '#94a3b8' }}>
            {filtered.length}개 표시 중
          </p>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-[12px]" style={{ color: '#334155' }}>
            <thead className="sticky top-0" style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <tr>
                <th className="text-left px-4 py-2 font-semibold" style={{ color: '#64748b' }}>회사 / 직무</th>
                <th className="text-left px-3 py-2 font-semibold" style={{ color: '#64748b' }}>연봉</th>
                <th className="text-left px-3 py-2 font-semibold" style={{ color: '#64748b' }}>분류</th>
                <th className="text-right px-4 py-2 font-semibold" style={{ color: '#64748b' }}>마감</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((job) => {
                const isActive = selected?.job_id === job.job_id;
                return (
                  <tr
                    key={job.job_id}
                    onClick={() => setSelected(job)}
                    className="cursor-pointer border-b transition-colors"
                    style={{
                      borderColor: '#f1f5f9',
                      background: isActive ? '#eff6ff' : undefined,
                    }}
                    onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = '#f8fafc'; }}
                    onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = ''; }}
                  >
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[10px] font-bold shrink-0"
                          style={{ backgroundColor: getLogoColor(job.company_name) }}
                        >
                          {getInitials(job.company_name)}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold truncate max-w-[160px]" style={{ color: '#0f172a' }}>
                            {job.title}
                          </p>
                          <p style={{ color: '#64748b' }}>{job.company_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="font-semibold" style={{ color: '#2563eb' }}>
                        {formatSalary(job.min_salary, job.max_salary)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <CategoryBadge category={job.job_category} />
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <span style={{ color: '#64748b' }}>{formatDeadline(job.deadline)}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right: detail */}
      <div className="flex-1 overflow-auto" style={{ background: '#f6f8fb' }}>
        {selected ? (
          <div className="p-6 max-w-xl">
            {/* Header card */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <div className="flex items-start gap-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-[16px] font-bold shrink-0"
                  style={{ backgroundColor: getLogoColor(selected.company_name) }}
                >
                  {getInitials(selected.company_name)}
                </div>
                <div className="flex-1">
                  <h3 className="text-[16px] font-bold" style={{ color: '#0f172a' }}>
                    {selected.title}
                  </h3>
                  <p className="text-[13px]" style={{ color: '#64748b' }}>{selected.company_name}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <CategoryBadge category={selected.job_category} />
                    <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#f1f5f9', color: '#475569' }}>
                      {selected.employment_type}
                    </span>
                    <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#f1f5f9', color: '#475569' }}>
                      {selected.career_level}
                    </span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-[18px] font-bold" style={{ color: '#2563eb' }}>
                    {selected.min_salary.toLocaleString()}
                  </p>
                  <p className="text-[11px]" style={{ color: '#94a3b8' }}>
                    ~ {selected.max_salary.toLocaleString()}만원
                  </p>
                  <p className="text-[11px] mt-1" style={{ color: '#64748b' }}>
                    {formatDeadline(selected.deadline)} 마감
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-3" style={{ color: '#0f172a' }}>공고 메타데이터</p>
              <div className="grid grid-cols-2 gap-3 text-[12px]">
                {[
                  { label: 'source', value: selected.source },
                  { label: 'source_job_id', value: selected.source_job_id },
                  { label: 'data_source', value: selected.data_source },
                  { label: 'location', value: selected.location },
                  { label: 'industry', value: selected.industry },
                  { label: 'work_schedule', value: selected.work_schedule },
                  { label: 'education', value: selected.education },
                  { label: 'ncs_category', value: selected.ncs_category },
                  { label: 'headcount', value: selected.headcount ? `${selected.headcount}명` : '-' },
                  { label: 'status', value: selected.status },
                  { label: 'posted_at', value: new Date(selected.posted_at).toLocaleDateString('ko-KR') },
                  { label: 'deadline', value: new Date(selected.deadline).toLocaleDateString('ko-KR') },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <p className="font-mono text-[10px]" style={{ color: '#94a3b8' }}>{label}</p>
                    <p className="font-medium truncate" style={{ color: '#334155' }}>{value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Tech stack */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-3" style={{ color: '#0f172a' }}>tech_stack</p>
              <div className="flex flex-wrap gap-2">
                {selected.tech_stack.map((tech) => (
                  <span
                    key={tech}
                    className="text-[12px] px-2.5 py-1 rounded-lg font-medium"
                    style={{ background: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe' }}
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-2" style={{ color: '#0f172a' }}>직무 소개</p>
              <p className="text-[13px] leading-relaxed" style={{ color: '#475569' }}>
                {selected.description}
              </p>
            </div>

            {/* Benefits */}
            <div className="bg-white rounded-2xl p-5 mb-4 border" style={{ borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-3" style={{ color: '#0f172a' }}>복리후생</p>
              <ul className="space-y-1.5">
                {selected.benefits.map((b) => (
                  <li key={b} className="flex items-center gap-2 text-[12px]" style={{ color: '#475569' }}>
                    <Icon name="check" size={12} color="#2563eb" />
                    {b}
                  </li>
                ))}
              </ul>
            </div>

            {/* Category stats */}
            <div className="bg-white rounded-2xl p-5 border" style={{ borderColor: '#e2e8f0' }}>
              <p className="text-[13px] font-semibold mb-3" style={{ color: '#0f172a' }}>카테고리별 분포</p>
              <div className="space-y-2">
                {catCounts.filter((c) => c.count > 0).map(({ cat, count }) => (
                  <div key={cat} className="flex items-center gap-2">
                    <span className="text-[11px] w-24 shrink-0" style={{ color: '#64748b' }}>{cat}</span>
                    <div className="flex-1 h-1.5 rounded-full" style={{ background: '#f1f5f9' }}>
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${(count / totalJobs) * 100}%`,
                          background: CATEGORY_COLORS[cat]?.color ?? '#94a3b8',
                        }}
                      />
                    </div>
                    <span className="text-[11px] font-semibold w-5 text-right" style={{ color: '#334155' }}>
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2" style={{ color: '#94a3b8' }}>
            <Icon name="layers" size={32} />
            <p className="text-[14px] font-medium" style={{ color: '#64748b' }}>공고를 선택하세요</p>
            <p className="text-[12px]">Work24 구조 기반 IT 기업 Mock 데이터</p>
          </div>
        )}
      </div>
    </div>
  );
}
