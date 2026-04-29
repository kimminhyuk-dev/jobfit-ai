import Gauge from '../../components/ui/Gauge';
import Icon from '../../components/ui/Icon';
import { mockAnalysis, mockSkills } from '../../api/mock/analysis';
import { mockStats } from '../../api/mock/jobs';

export default function MatchesPage() {
  const { strengths, weaknesses, recommendations } = mockAnalysis;

  return (
    <div className="p-6 max-w-[1100px] mx-auto">
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <h1 className="text-[20px] font-bold text-m-text tracking-tight">AI 매칭 분석</h1>
          <p className="text-[13px] text-m-muted mt-1">최신 이력서 기준으로 분석된 결과입니다.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-m-surface border border-m-border rounded-full text-[12px] text-m-muted">
          <Icon name="sparkle" size={13} />
          마지막 분석: 2026-04-27
        </div>
      </div>

      {/* Overview: Score + stats */}
      <div className="grid grid-cols-[auto_1fr] gap-4 mb-5">
        <div className="bg-m-surface border border-m-border rounded-2xl p-6 flex flex-col items-center justify-center gap-2 w-[160px]">
          <Gauge score={mockStats.resumeScore} size={110} stroke={9} label="이력서 점수" />
          <p className="text-[11px] text-m-subtle text-center">경쟁자 대비 상위 28%</p>
        </div>
        <div className="bg-m-surface border border-m-border rounded-2xl p-5 grid grid-cols-3 gap-4">
          {[
            { label: '매칭 채용공고', value: mockStats.matchedJobs, suffix: '건', color: 'text-m-primary' },
            { label: '평균 매칭 점수', value: '81', suffix: '점', color: 'text-m-text' },
            { label: '강점 항목', value: strengths.length, suffix: '개', color: 'text-m-success' },
          ].map((s) => (
            <div key={s.label} className="flex flex-col justify-center">
              <p className="text-[11px] text-m-muted font-medium mb-1">{s.label}</p>
              <p className={`text-[28px] font-bold font-mono tracking-tight ${s.color}`}>
                {s.value}
                <span className="text-[14px] font-medium text-m-subtle ml-0.5">{s.suffix}</span>
              </p>
            </div>
          ))}
          <div className="col-span-3 pt-3 border-t border-m-border">
            <p className="text-[12px] text-m-muted">
              <strong className="text-m-text">GraphQL</strong> 스킬을 추가하면 매칭 공고 수가 평균 +9건 늘어납니다.
            </p>
          </div>
        </div>
      </div>

      {/* LLM Analysis — 3 columns */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        {/* Strengths */}
        <div className="bg-m-surface border border-m-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-m-border bg-m-success-soft">
            <Icon name="trend" size={15} color="#15803d" />
            <h3 className="text-[13px] font-semibold text-m-success">강점</h3>
            <span className="ml-auto text-[11px] font-semibold text-m-success bg-white px-1.5 py-0.5 rounded-full">
              {strengths.length}
            </span>
          </div>
          <div className="p-3 flex flex-col gap-2.5">
            {strengths.map((item) => (
              <div key={item.title} className="p-3 bg-m-surface-alt rounded-xl">
                <p className="text-[13px] font-semibold text-m-text mb-1">{item.title}</p>
                <p className="text-[12px] text-m-muted leading-relaxed">{item.detail}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Weaknesses */}
        <div className="bg-m-surface border border-m-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-m-border bg-m-danger-soft">
            <Icon name="x" size={15} color="#b91c1c" />
            <h3 className="text-[13px] font-semibold text-m-danger">약점</h3>
            <span className="ml-auto text-[11px] font-semibold text-m-danger bg-white px-1.5 py-0.5 rounded-full">
              {weaknesses.length}
            </span>
          </div>
          <div className="p-3 flex flex-col gap-2.5">
            {weaknesses.map((item) => (
              <div key={item.title} className="p-3 bg-m-surface-alt rounded-xl">
                <p className="text-[13px] font-semibold text-m-text mb-1">{item.title}</p>
                <p className="text-[12px] text-m-muted leading-relaxed">{item.detail}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-m-surface border border-m-border rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-m-border bg-m-primary-soft">
            <Icon name="sparkle" size={15} color="#1d4ed8" />
            <h3 className="text-[13px] font-semibold text-m-primary">개선 제안</h3>
            <span className="ml-auto text-[11px] font-semibold text-m-primary bg-white px-1.5 py-0.5 rounded-full">
              {recommendations.length}
            </span>
          </div>
          <div className="p-3 flex flex-col gap-2.5">
            {recommendations.map((item) => (
              <div key={item.title} className="p-3 bg-m-surface-alt rounded-xl">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-[13px] font-semibold text-m-text">{item.title}</p>
                  {item.impact && (
                    <span className="flex-shrink-0 text-[11px] font-bold text-m-success bg-m-success-soft px-1.5 py-0.5 rounded-full font-mono">
                      {item.impact}
                    </span>
                  )}
                </div>
                <p className="text-[12px] text-m-muted leading-relaxed">{item.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Skill Gap */}
      <div className="bg-m-surface border border-m-border rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[14px] font-semibold text-m-text">스킬 갭 분석</h3>
          <div className="flex items-center gap-4 text-[11px] text-m-subtle">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-2 rounded-sm bg-m-primary" />내 수준
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-2 rounded-sm bg-m-border-strong" />시장 평균
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-3.5">
          {mockSkills.map((skill) => (
            <div key={skill.name}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium text-m-text">{skill.name}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                      skill.status === 'strong'
                        ? 'bg-m-success-soft text-m-success'
                        : skill.status === 'gap'
                        ? 'bg-m-warn-soft text-m-warn'
                        : 'bg-m-danger-soft text-m-danger'
                    }`}
                  >
                    {skill.status === 'strong' ? '강점' : skill.status === 'gap' ? '보완' : '학습 필요'}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[12px] font-mono">
                  <span className="text-m-primary font-semibold">{skill.user}</span>
                  <span className="text-m-subtle">/</span>
                  <span className="text-m-subtle">{skill.market}</span>
                </div>
              </div>
              <div className="relative h-2 bg-m-surface-alt rounded-full overflow-hidden">
                {/* Market avg */}
                <div
                  className="absolute top-0 left-0 h-full bg-m-border-strong rounded-full"
                  style={{ width: `${skill.market}%` }}
                />
                {/* User level */}
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-700 ${
                    skill.status === 'strong'
                      ? 'bg-m-primary'
                      : skill.status === 'gap'
                      ? 'bg-m-warn'
                      : 'bg-m-danger'
                  }`}
                  style={{ width: `${skill.user}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
