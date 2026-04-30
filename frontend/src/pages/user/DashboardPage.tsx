import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import Gauge from '../../components/ui/Gauge';
import Icon from '../../components/ui/Icon';
import { useAuth } from '../../stores/authContext';
import { authApi } from '../../api/auth';
import { mockJobs, mockStats, mockApplications } from '../../api/mock/jobs';

function ProfileModal({ onClose }: { onClose: () => void }) {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user?.name ?? '');
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const mutation = useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: (updated) => {
      setUser(updated);
      setSuccess('저장되었습니다.');
      setCurrentPw('');
      setNewPw('');
    },
    onError: (e: { response?: { data?: { message?: string } } }) =>
      setError(e.response?.data?.message ?? '저장에 실패했습니다.'),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSuccess('');
    const body: Parameters<typeof authApi.updateMe>[0] = {};
    const trimmedName = name.trim();
    if (trimmedName !== (user?.name ?? '')) body.name = trimmedName || undefined;
    if (newPw) {
      if (!currentPw) { setError('현재 비밀번호를 입력하세요.'); return; }
      body.current_password = currentPw;
      body.new_password = newPw;
    }
    if (!Object.keys(body).length) { setError('변경할 내용이 없습니다.'); return; }
    mutation.mutate(body);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-100 p-6">
        <h2 className="text-[16px] font-bold mb-4" style={{ color: '#0f172a' }}>프로필 수정</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>이메일</label>
            <input
              value={user?.email ?? ''}
              disabled
              className="w-full h-9 px-3 rounded-lg border text-[13px]"
              style={{ borderColor: '#e2e8f0', background: '#f8fafc', color: '#94a3b8' }}
            />
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>이름</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={50}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="이름"
            />
          </div>
          <hr style={{ borderColor: '#f1f5f9' }} />
          <p className="text-[12px] font-medium" style={{ color: '#475569' }}>비밀번호 변경 (선택)</p>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>현재 비밀번호</label>
            <input
              type="password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="현재 비밀번호"
            />
          </div>
          <div>
            <label className="text-[12px] font-medium block mb-1" style={{ color: '#475569' }}>새 비밀번호</label>
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              minLength={8}
              className="w-full h-9 px-3 rounded-lg border text-[13px] focus:outline-none focus:border-blue-500"
              style={{ borderColor: '#e2e8f0' }}
              placeholder="8자 이상"
            />
          </div>

          {error && <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          {success && <p className="text-[12px] text-green-700 bg-green-50 px-3 py-2 rounded-lg">{success}</p>}

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="h-9 px-4 rounded-lg text-[13px] font-medium border"
              style={{ borderColor: '#e2e8f0', color: '#475569' }}
            >
              닫기
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="h-9 px-4 rounded-lg text-white text-[13px] font-semibold disabled:opacity-50"
              style={{ background: '#2563eb' }}
            >
              {mutation.isPending ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const statCards = [
  { label: '이력서 점수', valueKey: 'resumeScore' as const, suffix: '/100', icon: 'sparkle' as const, delta: '+5' },
  { label: '추천 공고', valueKey: 'matchedJobs' as const, suffix: '건', icon: 'briefcase' as const, delta: '+4' },
  { label: '지원 완료', valueKey: 'applied' as const, suffix: '건', icon: 'flag' as const, delta: '+2' },
  { label: '면접 진행', valueKey: 'interviews' as const, suffix: '건', icon: 'user' as const, delta: '+1' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [selectedJobId, setSelectedJobId] = useState(mockJobs[0].id);
  const [showProfile, setShowProfile] = useState(false);
  const selectedJob = mockJobs.find((j) => j.id === selectedJobId) ?? mockJobs[0];
  const stats = mockStats;

  return (
    <>
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
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowProfile(true)}
            className="h-9 px-4 flex items-center gap-1.5 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
          >
            <Icon name="user" size={13} />
            프로필 수정
          </button>
          <Link
            to="/user/matches"
            className="h-9 px-4 flex items-center gap-1.5 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
          >
            AI 분석 보기
            <Icon name="chevron" size={13} />
          </Link>
        </div>
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

    {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </>
  );
}
