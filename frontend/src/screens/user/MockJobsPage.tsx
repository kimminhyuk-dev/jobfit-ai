'use client';

import { useState } from 'react';
import Icon from '../../components/ui/Icon';
import { mockItJobs, MOCK_JOB_CATEGORIES } from '../../api/mock/mockItJobs';
import type { MockJobItem } from '../../api/mock/mockItJobs';

const LOGO_COLORS = ['#1d4ed8', '#0f766e', '#7c3aed', '#ea580c', '#0284c7', '#15803d', '#b45309', '#be185d'];

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2);
  return words[0][0] + words[words.length - 1][0];
}

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
  if (days === 0) return '오늘 마감';
  if (days <= 7) return `D-${days}`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) + ' 마감';
}

function formatPostedAt(postedAt: string): string {
  const date = new Date(postedAt);
  const now = new Date();
  const days = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (days === 0) return '오늘';
  if (days === 1) return '1일 전';
  if (days < 30) return `${days}일 전`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function formatSalary(min: number, max: number): string {
  return `${min.toLocaleString()} ~ ${max.toLocaleString()}만원`;
}

function getWorkTag(schedule: string): string | null {
  if (schedule.includes('완전 원격') || schedule.includes('원격근무')) return '원격근무';
  if (schedule.includes('재택')) return '재택가능';
  if (schedule.includes('하이브리드')) return '하이브리드';
  return null;
}

export default function MockJobsPage() {
  const [selected, setSelected] = useState<MockJobItem | null>(null);
  const [query, setQuery] = useState('');
  const [categoryIdx, setCategoryIdx] = useState(0);

  const filtered = mockItJobs.filter((job) => {
    const matchesCategory =
      categoryIdx === 0 || job.job_category === MOCK_JOB_CATEGORIES[categoryIdx];
    const q = query.toLowerCase();
    const matchesSearch =
      !q ||
      job.title.toLowerCase().includes(q) ||
      job.company_name.toLowerCase().includes(q) ||
      job.tech_stack.some((t) => t.toLowerCase().includes(q));
    return matchesCategory && matchesSearch;
  });

  function handleCategoryChange(idx: number) {
    setCategoryIdx(idx);
    setSelected(null);
  }

  return (
    <div className="flex h-full min-h-0">
      {/* List panel */}
      <div className="flex flex-col border-r border-m-border bg-m-surface w-95 shrink-0">
        {/* Header */}
        <div className="p-4 border-b border-m-border">
          <div className="flex items-center gap-2 mb-3">
            <h1 className="text-[16px] font-bold text-m-text">IT 채용공고</h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 font-bold tracking-wide">
              MOCK
            </span>
          </div>

          {/* Category tabs */}
          <div className="flex gap-1 overflow-x-auto pb-1 mb-3 scrollbar-none">
            {MOCK_JOB_CATEGORIES.map((cat, i) => (
              <button
                key={cat}
                onClick={() => handleCategoryChange(i)}
                className={`shrink-0 h-7 px-2.5 rounded-lg text-[11px] font-medium transition-colors whitespace-nowrap ${
                  categoryIdx === i
                    ? 'bg-m-primary text-white'
                    : 'bg-m-surface-alt text-m-subtle hover:text-m-muted'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
              <Icon name="search" size={14} />
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="직무, 회사, 기술스택 검색"
              className="w-full h-9 pl-9 pr-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            />
          </div>
          <p className="text-[11px] text-m-subtle mt-2">{filtered.length}개 공고</p>
        </div>

        {/* Job list */}
        <div className="flex-1 overflow-auto scrollbar-thin divide-y divide-m-border">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center h-32">
              <p className="text-[13px] text-m-subtle">공고가 없습니다.</p>
            </div>
          ) : (
            filtered.map((job) => {
              const workTag = getWorkTag(job.work_schedule);
              const isActive = selected?.job_id === job.job_id;
              return (
                <button
                  key={job.job_id}
                  onClick={() => setSelected(job)}
                  className={`w-full p-4 text-left hover:bg-m-surface-alt transition-colors ${
                    isActive ? 'bg-m-primary-soft border-l-2 border-m-primary' : ''
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
                      <p className="text-[12px] text-m-muted">
                        {job.company_name} · {job.location}
                      </p>

                      {/* Tags row */}
                      <div className="flex items-center gap-1 mt-1.5 flex-wrap">
                        {workTag && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-600 border border-blue-100 font-medium">
                            {workTag}
                          </span>
                        )}
                        <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-m-surface border border-m-border text-m-subtle">
                          {job.career_level}
                        </span>
                      </div>

                      {/* Tech stack */}
                      <div className="flex items-center gap-1 mt-1.5 flex-wrap">
                        {job.tech_stack.slice(0, 3).map((t) => (
                          <span
                            key={t}
                            className="text-[10px] px-1.5 py-0.5 rounded-md bg-m-surface-alt border border-m-border text-m-muted font-medium"
                          >
                            {t}
                          </span>
                        ))}
                        {job.tech_stack.length > 3 && (
                          <span className="text-[10px] text-m-subtle">
                            +{job.tech_stack.length - 3}
                          </span>
                        )}
                      </div>

                      {/* Salary */}
                      <p className="text-[12px] font-semibold text-m-primary mt-1.5">
                        {formatSalary(job.min_salary, job.max_salary)}
                      </p>
                    </div>

                    {/* Right: deadline + posted */}
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className="text-[11px] font-semibold text-m-primary">
                        {formatDeadline(job.deadline)}
                      </span>
                      <span className="text-[11px] text-m-subtle">
                        {formatPostedAt(job.posted_at)}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-auto scrollbar-thin">
        {selected ? (
          <div className="p-6 max-w-2xl">
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
                <p className="text-[14px] text-m-muted mt-0.5">{selected.company_name}</p>
                <div className="flex flex-wrap gap-3 mt-2 text-[13px] text-m-muted">
                  <span className="flex items-center gap-1">
                    <Icon name="map-pin" size={13} />
                    {selected.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <Icon name="briefcase" size={13} />
                    {selected.employment_type}
                  </span>
                  <span className="flex items-center gap-1">
                    <Icon name="user" size={13} />
                    {selected.career_level}
                  </span>
                </div>
              </div>
              <button
                disabled
                className="shrink-0 h-9 px-4 rounded-lg bg-m-surface border border-m-border text-[13px] font-medium text-m-subtle cursor-not-allowed"
              >
                지원하기 (Mock)
              </button>
            </div>

            {/* Job Info */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-4">공고 정보</h3>
              <div className="grid grid-cols-2 gap-4 text-[13px]">
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">급여</p>
                  <p className="font-semibold text-m-primary">
                    {formatSalary(selected.min_salary, selected.max_salary)}
                  </p>
                  <p className="text-[11px] text-m-subtle mt-0.5">{selected.salary_text}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">근무형태</p>
                  <p className="text-m-muted">{selected.work_schedule}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">업종</p>
                  <p className="text-m-muted">{selected.industry}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">학력</p>
                  <p className="text-m-muted">{selected.education}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">NCS 분류</p>
                  <p className="text-m-muted">{selected.ncs_category}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">채용인원</p>
                  <p className="text-m-muted">
                    {selected.headcount ? `${selected.headcount}명` : '00명'}
                  </p>
                </div>
              </div>
            </div>

            {/* Tech Stack */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">기술 스택</h3>
              <div className="flex flex-wrap gap-2">
                {selected.tech_stack.map((tech) => (
                  <span
                    key={tech}
                    className="text-[12px] px-2.5 py-1 rounded-lg bg-m-primary-soft text-m-primary border border-m-primary/20 font-medium"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">직무 소개</h3>
              <p className="text-[13px] text-m-muted leading-relaxed">{selected.description}</p>
            </div>

            {/* Benefits */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">복리후생</h3>
              <ul className="space-y-1.5">
                {selected.benefits.map((b) => (
                  <li key={b} className="flex items-center gap-2 text-[13px] text-m-muted">
                    <Icon name="check" size={13} className="text-m-primary shrink-0" />
                    {b}
                  </li>
                ))}
              </ul>
            </div>

            {/* Deadline */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">접수 기간</h3>
              <div className="flex items-center gap-6 text-[13px] text-m-muted">
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">등록일</p>
                  <p>{new Date(selected.posted_at).toLocaleDateString('ko-KR')}</p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">마감일</p>
                  <p className="text-m-primary font-semibold">
                    {new Date(selected.deadline).toLocaleDateString('ko-KR')}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-m-subtle mb-0.5">남은 기간</p>
                  <p className="font-semibold">{formatDeadline(selected.deadline)}</p>
                </div>
              </div>
            </div>

            {/* AI Analysis Placeholder */}
            <div className="border border-dashed border-m-primary/30 rounded-2xl p-5 bg-m-primary-soft/30">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="sparkle" size={16} className="text-m-primary" />
                <h3 className="text-[14px] font-semibold text-m-primary">AI 분석</h3>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-m-primary/10 text-m-primary font-bold">
                  준비 중
                </span>
              </div>
              <p className="text-[13px] text-m-muted mb-4">
                이력서를 등록하면 이 공고와의 AI 매칭 분석을 받아볼 수 있습니다.
              </p>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: '매칭도 예측', icon: 'target' as const },
                  { label: '강점 분석', icon: 'trend' as const },
                  { label: '개선 제안', icon: 'star' as const },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-m-surface border border-m-border opacity-50"
                  >
                    <Icon name={item.icon} size={18} className="text-m-primary" />
                    <p className="text-[11px] text-m-muted font-medium">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-m-subtle gap-2">
            <Icon name="layers" size={32} className="opacity-30" />
            <p className="text-[14px]">공고를 선택하세요</p>
            <p className="text-[12px] text-m-subtle opacity-70">
              Work24 구조 기반 IT 기업 Mock 데이터
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
