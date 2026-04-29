import { useState } from 'react';
import Icon from '../../components/ui/Icon';
import Gauge from '../../components/ui/Gauge';
import { mockResumes } from '../../api/mock/resumes';
import type { Resume } from '../../api/types';

type UploadStage = 'idle' | 'uploading' | 'analyzing' | 'done';

export default function ResumesPage() {
  const [stage, setStage] = useState<UploadStage>('idle');
  const [progress, setProgress] = useState(0);
  const [drag, setDrag] = useState(false);
  const [resumes] = useState<Resume[]>(mockResumes);

  const startUpload = () => {
    setStage('uploading');
    setProgress(0);
    let p = 0;
    const tick = () => {
      p += 4 + Math.random() * 8;
      if (p >= 100) {
        setProgress(100);
        setTimeout(() => {
          setStage('analyzing');
          let q = 0;
          const tick2 = () => {
            q += 3 + Math.random() * 5;
            if (q >= 100) {
              setProgress(100);
              setTimeout(() => setStage('done'), 400);
            } else {
              setProgress(q);
              setTimeout(tick2, 180);
            }
          };
          setProgress(0);
          tick2();
        }, 400);
      } else {
        setProgress(p);
        setTimeout(tick, 120);
      }
    };
    tick();
  };

  const analysisSteps = [
    { label: '텍스트 추출 완료', done: true },
    { label: '경력 및 스킬 파싱 완료', done: true },
    { label: '12,400개 채용공고와 매칭 중...', done: false },
    { label: '강점/약점 분석', done: false },
  ];

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <h1 className="text-[20px] font-bold text-m-text tracking-tight mb-1">내 이력서</h1>
      <p className="text-[13px] text-m-muted mb-6">이력서를 업로드하면 AI가 분석 후 맞춤 채용공고를 추천해 드려요.</p>

      {/* Upload area */}
      <div className="bg-m-surface border border-m-border rounded-2xl p-6 mb-6">
        {/* Stepper */}
        <div className="flex items-center gap-2 justify-center mb-6">
          {[
            { n: 1, label: '이력서 업로드', active: true, done: stage === 'done' },
            { n: 2, label: 'AI 분석', active: stage === 'analyzing' || stage === 'done', done: stage === 'done' },
            { n: 3, label: '맞춤 채용공고', active: stage === 'done', done: false },
          ].map((s, i, arr) => (
            <div key={s.n} className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold font-mono ${
                    s.done
                      ? 'bg-m-success text-white'
                      : s.active
                      ? 'bg-m-primary text-white'
                      : 'bg-m-border text-m-subtle'
                  }`}
                >
                  {s.done ? <Icon name="check" size={13} strokeWidth={3} /> : s.n}
                </div>
                <span className={`text-[13px] ${s.active ? 'font-semibold text-m-text' : 'text-m-muted'}`}>
                  {s.label}
                </span>
              </div>
              {i < arr.length - 1 && <div className="w-8 h-px bg-m-border" />}
            </div>
          ))}
        </div>

        {/* Dropzone */}
        {stage === 'idle' && (
          <div
            onDragEnter={(e) => { e.preventDefault(); setDrag(true); }}
            onDragOver={(e) => e.preventDefault()}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); startUpload(); }}
            onClick={startUpload}
            className={`rounded-xl border-2 border-dashed py-14 text-center cursor-pointer transition-all ${
              drag
                ? 'border-m-primary bg-m-primary-soft'
                : 'border-m-border-strong bg-m-surface-alt hover:border-m-primary hover:bg-m-primary-soft'
            }`}
          >
            <div className="w-14 h-14 rounded-2xl bg-m-primary-soft text-m-primary flex items-center justify-center mx-auto mb-4">
              <Icon name="upload" size={26} />
            </div>
            <p className="text-[15px] font-semibold text-m-text mb-1">파일을 끌어다 놓거나 클릭해 선택하세요</p>
            <p className="text-[13px] text-m-muted">PDF · DOCX · 최대 10MB</p>
            <button className="mt-5 h-9 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors">
              파일 선택
            </button>
          </div>
        )}

        {/* Progress */}
        {(stage === 'uploading' || stage === 'analyzing') && (
          <div className="border border-m-border rounded-xl p-5">
            <div className="flex items-center gap-3.5 mb-4">
              <div className="w-11 h-11 rounded-xl bg-m-primary-soft text-m-primary flex items-center justify-center">
                <Icon name={stage === 'uploading' ? 'pdf' : 'sparkle'} size={22} />
              </div>
              <div className="flex-1">
                <p className="text-[14px] font-semibold text-m-text">
                  {stage === 'uploading' ? 'resume_v4.pdf' : 'AI가 이력서를 분석하고 있어요'}
                </p>
                <p className="text-[12px] text-m-muted mt-0.5">
                  {stage === 'uploading' ? '업로드 중 · 1.4MB' : '경력, 스킬, 프로젝트를 추출 중...'}
                </p>
              </div>
              <span className="text-[13px] font-bold text-m-primary font-mono">{Math.round(progress)}%</span>
            </div>
            <div className="h-1.5 bg-m-surface-alt rounded-full overflow-hidden">
              <div
                className="h-full bg-m-primary rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
            {stage === 'analyzing' && (
              <div className="flex flex-col gap-2 mt-5">
                {analysisSteps.map((s) => (
                  <div key={s.label} className="flex items-center gap-2.5 text-[13px]">
                    <div
                      className={`w-[18px] h-[18px] rounded-full flex items-center justify-center flex-shrink-0 ${
                        s.done ? 'bg-m-success text-white' : 'bg-m-surface-alt text-m-subtle'
                      }`}
                    >
                      {s.done ? (
                        <Icon name="check" size={11} strokeWidth={3} />
                      ) : (
                        <span className="w-1.5 h-1.5 bg-m-subtle rounded-full animate-pulse" />
                      )}
                    </div>
                    <span className={s.done ? 'text-m-text' : 'text-m-muted'}>{s.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Done */}
        {stage === 'done' && (
          <div className="text-center py-4">
            <div className="w-14 h-14 rounded-full bg-m-success-soft text-m-success flex items-center justify-center mx-auto mb-4">
              <Icon name="check" size={28} strokeWidth={2.5} />
            </div>
            <h2 className="text-[18px] font-bold text-m-text">분석 완료!</h2>
            <p className="text-[14px] text-m-muted mt-2">
              <strong className="text-m-text">28개</strong>의 추천 채용공고와{' '}
              <strong className="text-m-text">3개</strong>의 개선 제안을 준비했어요.
            </p>
            <button
              onClick={() => setStage('idle')}
              className="mt-5 h-10 px-6 rounded-lg bg-m-primary text-white text-[14px] font-semibold hover:bg-m-primary-hover transition-colors inline-flex items-center gap-2"
            >
              대시보드로 이동
              <Icon name="arrow" size={16} />
            </button>
          </div>
        )}

        {/* Tip */}
        {stage === 'idle' && (
          <div className="mt-4 flex gap-3 items-start p-4 bg-m-primary-soft rounded-xl">
            <Icon name="sparkle" size={16} color="#1d4ed8" className="mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[13px] font-semibold text-m-text">이력서가 없으신가요?</p>
              <p className="text-[12px] text-m-muted mt-0.5">LinkedIn 프로필을 연동하거나 빈 템플릿으로 시작할 수 있어요.</p>
            </div>
          </div>
        )}
      </div>

      {/* Existing resumes */}
      {resumes.length > 0 && (
        <div>
          <h2 className="text-[14px] font-semibold text-m-text mb-3">업로드한 이력서</h2>
          <div className="flex flex-col gap-2.5">
            {resumes.map((r, i) => (
              <div key={r.id} className="bg-m-surface border border-m-border rounded-xl p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-m-primary-soft text-m-primary flex items-center justify-center flex-shrink-0">
                  <Icon name="pdf" size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-m-text truncate">
                    {r.filename}
                    {i === 0 && (
                      <span className="ml-2 text-[11px] px-1.5 py-0.5 bg-m-primary text-white rounded font-medium">
                        최신
                      </span>
                    )}
                  </p>
                  <p className="text-[12px] text-m-muted mt-0.5">
                    {new Date(r.uploaded_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                  </p>
                </div>
                <Gauge score={r.score} size={52} stroke={5} label="" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
