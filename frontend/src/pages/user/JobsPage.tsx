import { useState } from 'react';
import Icon from '../../components/ui/Icon';
import Gauge from '../../components/ui/Gauge';
import { mockJobs } from '../../api/mock/jobs';
import type { Job } from '../../api/types';

type ViewMode = 'grid' | 'list';

export default function JobsPage() {
  const [view, setView] = useState<ViewMode>('list');
  const [selected, setSelected] = useState<Job | null>(mockJobs[0]);
  const [query, setQuery] = useState('');

  const filtered = mockJobs.filter(
    (j) =>
      !query ||
      j.title.includes(query) ||
      j.company.includes(query) ||
      j.matchedSkills.some((s) => s.toLowerCase().includes(query.toLowerCase())),
  );

  return (
    <div className="flex h-full min-h-0">
      {/* List panel */}
      <div className="flex flex-col border-r border-m-border bg-m-surface w-[380px] flex-shrink-0">
        {/* Header */}
        <div className="p-4 border-b border-m-border">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-[16px] font-bold text-m-text">추천 채용공고</h1>
            <div className="flex items-center gap-1 p-1 bg-m-surface-alt rounded-lg">
              <button
                onClick={() => setView('list')}
                className={`p-1.5 rounded ${view === 'list' ? 'bg-m-surface shadow-sm text-m-text' : 'text-m-subtle'}`}
              >
                <Icon name="list" size={14} />
              </button>
              <button
                onClick={() => setView('grid')}
                className={`p-1.5 rounded ${view === 'grid' ? 'bg-m-surface shadow-sm text-m-text' : 'text-m-subtle'}`}
              >
                <Icon name="grid" size={14} />
              </button>
            </div>
          </div>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
              <Icon name="search" size={14} />
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="회사, 직무, 스킬 검색"
              className="w-full h-9 pl-9 pr-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            />
          </div>
          <p className="text-[11px] text-m-subtle mt-2">{filtered.length}개 공고</p>
        </div>

        {/* Job list */}
        <div className="flex-1 overflow-auto scrollbar-thin divide-y divide-m-border">
          {filtered.map((job) => (
            <button
              key={job.id}
              onClick={() => setSelected(job)}
              className={`w-full p-4 text-left hover:bg-m-surface-alt transition-colors ${
                selected?.id === job.id ? 'bg-m-primary-soft border-l-2 border-m-primary' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-[12px] font-bold flex-shrink-0"
                  style={{ backgroundColor: job.logoColor }}
                >
                  {job.logo}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-m-text truncate">{job.title}</p>
                  <p className="text-[12px] text-m-muted">{job.company}</p>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className="text-[11px] text-m-subtle flex items-center gap-1">
                      <Icon name="map-pin" size={11} /> {job.location}
                    </span>
                    <span className="text-[11px] text-m-subtle">{job.salary}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span
                    className={`text-[13px] font-bold font-mono ${
                      job.score >= 85 ? 'text-m-success' : job.score >= 70 ? 'text-m-primary' : 'text-m-warn'
                    }`}
                  >
                    {job.score}점
                  </span>
                  <span className="text-[11px] text-m-subtle">{job.posted}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-auto scrollbar-thin">
        {selected ? (
          <div className="p-6">
            {/* Header */}
            <div className="flex items-start gap-5 mb-6">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-[18px] font-bold flex-shrink-0"
                style={{ backgroundColor: selected.logoColor }}
              >
                {selected.logo}
              </div>
              <div className="flex-1">
                <h2 className="text-[20px] font-bold text-m-text tracking-tight">{selected.title}</h2>
                <p className="text-[14px] text-m-muted mt-0.5">{selected.company}</p>
                <div className="flex flex-wrap gap-3 mt-2 text-[13px] text-m-muted">
                  <span className="flex items-center gap-1"><Icon name="map-pin" size={13} />{selected.location}</span>
                  <span className="flex items-center gap-1"><Icon name="building" size={13} />{selected.type}</span>
                  <span className="flex items-center gap-1"><Icon name="dollar" size={13} />{selected.salary}</span>
                </div>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button className="h-9 px-4 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors flex items-center gap-1.5">
                  <Icon name="bookmark" size={14} /> 저장
                </button>
                <button className="h-9 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors flex items-center gap-1.5">
                  지원하기 <Icon name="arrow" size={14} />
                </button>
              </div>
            </div>

            {/* Match score */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4 flex items-center gap-6">
              <Gauge score={selected.score} size={88} stroke={7} label="매칭" />
              <div className="flex-1 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[11px] font-semibold text-m-success mb-2">매칭 스킬</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.matchedSkills.map((s) => (
                      <span key={s} className="text-[12px] px-2.5 py-1 bg-m-success-soft text-m-success rounded-full font-medium">
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-m-warn mb-2">보완 필요</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.missingSkills.map((s) => (
                      <span key={s} className="text-[12px] px-2.5 py-1 bg-m-warn-soft text-m-warn rounded-full font-medium">
                        — {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Info */}
            <div className="bg-m-surface border border-m-border rounded-2xl p-5 mb-4">
              <h3 className="text-[14px] font-semibold text-m-text mb-3">공고 정보</h3>
              <div className="grid grid-cols-2 gap-3 text-[13px]">
                <div className="flex items-center gap-2 text-m-muted">
                  <Icon name="briefcase" size={14} />
                  <span>{selected.type}</span>
                </div>
                <div className="flex items-center gap-2 text-m-muted">
                  <Icon name="map-pin" size={14} />
                  <span>{selected.location}</span>
                </div>
                <div className="flex items-center gap-2 text-m-muted">
                  <Icon name="dollar" size={14} />
                  <span>{selected.salary}</span>
                </div>
                <div className="flex items-center gap-2 text-m-muted">
                  <Icon name="user" size={14} />
                  <span>지원자 {selected.applicants}명</span>
                </div>
              </div>
            </div>

            {/* AI tip */}
            <div className="bg-m-primary-soft border border-m-primary/15 rounded-2xl p-4 flex gap-3">
              <Icon name="sparkle" size={16} color="#1d4ed8" className="flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-[13px] font-semibold text-m-primary mb-1">AI 추천 이유</p>
                <p className="text-[13px] text-m-muted leading-relaxed">
                  회원님의 React, TypeScript 숙련도와 이 포지션의 요구사항이 높은 수준으로 일치합니다.
                  GraphQL을 추가로 학습하면 매칭 점수가 더 올라갈 수 있어요.
                </p>
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
