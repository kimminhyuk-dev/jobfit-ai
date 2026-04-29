import { useState } from 'react';
import { Link } from 'react-router-dom';
import Gauge from '../../components/ui/Gauge';
import Icon from '../../components/ui/Icon';
import { useAuth } from '../../stores/authStore';
import { mockJobs, mockStats, mockApplications } from '../../api/mock/jobs';

const statCards = [
  { label: '이력서 점수', valueKey: 'resumeScore' as const, suffix: '/100', icon: 'sparkle' as const, delta: '+5' },
  { label: '추천 공고', valueKey: 'matchedJobs' as const, suffix: '건', icon: 'briefcase' as const, delta: '+4' },
  { label: '지원 완료', valueKey: 'applied' as const, suffix: '건', icon: 'flag' as const, delta: '+2' },
  { label: '면접 진행', valueKey: 'interviews' as const, suffix: '건', icon: 'user' as const, delta: '+1' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [selectedJobId, setSelectedJobId] = useState(mockJobs[0].id);
  const selectedJob = mockJobs.find((j) => j.id === selectedJobId) ?? mockJobs[0];
  const stats = mockStats;

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Greeting */}
      <div className="flex items-end justify-between mb-5 gap-4 flex-wrap">
        <div>
          <h1 className="text-[22px] font-bold text-m-text tracking-tight">
            안녕하세요, {user?.name ?? '사용자'}님 👋
          </h1>
          <p className="text-[14px] text-m-muted mt-1.5">
            오늘 새로 매칭된 공고가 <strong className="text-m-text">{stats.weeklyDelta}건</strong> 있어요. 좋은 하루 되세요!
          </p>
        </div>
        <Link
          to="/user/matches"
          className="h-9 px-4 flex items-center gap-1.5 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
        >
          AI 분석 보기
          <Icon name="chevron" size={13} />
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3.5 mb-5">
        {statCards.map((s) => (
          <div key={s.label} className="bg-m-surface border border-m-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[12px] text-m-muted font-medium">{s.label}</p>
              <div className="w-7 h-7 rounded-lg bg-m-primary-soft text-m-primary flex items-center justify-center">
                <Icon name={s.icon} size={14} />
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-[26px] font-bold font-mono text-m-text tracking-tight">{stats[s.valueKey]}</span>
              <span className="text-[13px] text-m-subtle">{s.suffix}</span>
              <span className="ml-auto text-[11px] font-semibold text-m-success bg-m-success-soft px-1.5 py-0.5 rounded">
                {s.delta}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Main 2-col grid */}
      <div className="grid grid-cols-[1fr_300px] gap-4">
        {/* Left */}
        <div className="flex flex-col gap-4 min-w-0">
          {/* Top match card */}
          <div className="bg-m-surface border border-m-border rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-[11px] font-semibold text-m-primary tracking-widest uppercase">오늘의 최고 매칭</p>
                <h2 className="text-[16px] font-bold text-m-text mt-1">이 공고는 당신을 위한 것 같아요</h2>
              </div>
              <Link
                to="/user/jobs"
                className="h-8 px-3 flex items-center gap-1 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
              >
                전체 보기 <Icon name="chevron" size={12} />
              </Link>
            </div>

            <div className="flex items-center gap-5 mb-5">
              <Gauge score={selectedJob.score} size={100} stroke={8} label="매칭" />
              <div className="flex-1 min-w-0">
                <div
                  className="inline-flex items-center justify-center w-9 h-9 rounded-xl text-[13px] font-bold text-white mb-2"
                  style={{ backgroundColor: selectedJob.logoColor }}
                >
                  {selectedJob.logo}
                </div>
                <p className="text-[16px] font-bold text-m-text">{selectedJob.title}</p>
                <p className="text-[13px] text-m-muted mt-0.5">{selectedJob.company} · {selectedJob.location}</p>
                <p className="text-[12px] text-m-subtle mt-1">{selectedJob.salary} · {selectedJob.type}</p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-1">
                <p className="text-[11px] font-semibold text-m-success mb-1.5">매칭 스킬</p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.matchedSkills.map((s) => (
                    <span key={s} className="text-[11px] px-2 py-0.5 bg-m-success-soft text-m-success rounded-full font-medium">
                      ✓ {s}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex-1">
                <p className="text-[11px] font-semibold text-m-warn mb-1.5">보완 필요</p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.missingSkills.map((s) => (
                    <span key={s} className="text-[11px] px-2 py-0.5 bg-m-warn-soft text-m-warn rounded-full font-medium">
                      — {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Job list */}
          <div className="bg-m-surface border border-m-border rounded-xl">
            <div className="flex items-center justify-between p-4 border-b border-m-border">
              <h3 className="text-[14px] font-semibold text-m-text">추천 채용공고</h3>
              <Link to="/user/jobs" className="text-[12px] text-m-primary hover:underline">전체 보기</Link>
            </div>
            <div className="divide-y divide-m-border">
              {mockJobs.slice(0, 5).map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJobId(job.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-m-surface-alt transition-colors ${
                    selectedJobId === job.id ? 'bg-m-primary-soft' : ''
                  }`}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
                    style={{ backgroundColor: job.logoColor }}
                  >
                    {job.logo}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-m-text truncate">{job.title}</p>
                    <p className="text-[12px] text-m-muted">{job.company} · {job.location}</p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-2">
                    <span className={`text-[13px] font-bold font-mono ${
                      job.score >= 85 ? 'text-m-success' : job.score >= 70 ? 'text-m-primary' : 'text-m-warn'
                    }`}>
                      {job.score}
                    </span>
                    <span className="text-[11px] text-m-subtle">{job.posted}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right col */}
        <div className="flex flex-col gap-4">
          {/* Application tracker */}
          <div className="bg-m-surface border border-m-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-semibold text-m-text">지원 현황</h3>
              <span className="text-[11px] text-m-subtle font-mono">{stats.applied}건</span>
            </div>
            <div className="flex flex-col gap-2.5">
              {mockApplications.map((app) => (
                <div key={app.company} className="flex items-center gap-3">
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: app.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold text-m-text truncate">{app.company}</p>
                    <p className="text-[11px] text-m-subtle">{app.stage}</p>
                  </div>
                  <span className="text-[11px] text-m-subtle flex-shrink-0">{app.date}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Weekly insight */}
          <div className="bg-m-primary-soft border border-m-primary/15 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon name="sparkle" size={15} color="#1d4ed8" />
              <p className="text-[12px] font-semibold text-m-primary">주간 인사이트</p>
            </div>
            <p className="text-[13px] text-m-text leading-snug">
              이번 주 프론트엔드 신규 공고가 <strong>+14%</strong> 증가했어요. 지금이 지원하기 좋은 타이밍입니다.
            </p>
            <Link
              to="/user/matches"
              className="mt-3 flex items-center gap-1 text-[12px] font-medium text-m-primary hover:underline"
            >
              AI 분석 전체 보기 <Icon name="chevron" size={12} />
            </Link>
          </div>

          {/* Upload nudge */}
          <div className="bg-m-surface border border-m-border rounded-xl p-4">
            <p className="text-[12px] font-semibold text-m-text mb-1">이력서 업데이트</p>
            <p className="text-[12px] text-m-muted leading-snug">최신 이력서를 올리면 매칭 점수가 더 정확해져요.</p>
            <Link
              to="/user/resumes"
              className="mt-3 h-8 flex items-center justify-center gap-1.5 rounded-lg bg-m-text text-white text-[12px] font-semibold hover:opacity-80 transition-opacity"
            >
              <Icon name="upload" size={13} />
              이력서 업로드
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
