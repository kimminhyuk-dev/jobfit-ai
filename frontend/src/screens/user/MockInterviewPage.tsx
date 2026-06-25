'use client';

import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { applicationsApi } from '../../api/applications';
import { mockInterviewApi } from '../../api/mockInterview';
import { resumesApi } from '../../api/resumes';
import type {
  ApiError,
  MockInterviewSession,
  MockInterviewStage,
  MockInterviewTurn,
  MyApplication,
  Resume,
} from '../../api/types';
import Icon from '../../components/ui/Icon';

const STAGE_META: Record<
  MockInterviewStage,
  { label: string; short: string; cls: string }
> = {
  WARMUP: {
    label: '워밍업',
    short: '소개·기초',
    cls: 'bg-m-primary-soft text-m-primary',
  },
  EXPERIENCE: {
    label: '경험',
    short: '프로젝트',
    cls: 'bg-m-warn-soft text-m-warn',
  },
  DEEP: {
    label: '심화',
    short: '기술·인성',
    cls: 'bg-m-danger-soft text-m-danger',
  },
  COMPLETED: {
    label: '완료',
    short: '리포트',
    cls: 'bg-m-success-soft text-m-success',
  },
};

const STAGE_ORDER: MockInterviewStage[] = ['WARMUP', 'EXPERIENCE', 'DEEP'];

export default function MockInterviewPage() {
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [session, setSession] = useState<MockInterviewSession | null>(null);
  const [answerDraft, setAnswerDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data: resumes = [], isLoading: resumesLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: resumesApi.getResumes,
  });
  const { data: applications = [], isLoading: applicationsLoading } = useQuery({
    queryKey: ['applications', 'me'],
    queryFn: applicationsApi.getMyApplications,
  });

  const readyResumes = useMemo(
    () => resumes.filter((resume) => resume.parse_status === 'COMPLETED'),
    [resumes],
  );
  const activeResumeId =
    selectedResumeId ?? readyResumes[0]?.resume_id ?? null;
  const resumeApplications = useMemo(() => {
    if (!activeResumeId) return [];
    return applications.filter(
      (application) =>
        application.resume_id === activeResumeId &&
        application.status !== 'CANCELED',
    );
  }, [activeResumeId, applications]);
  const activeJobId = useMemo(() => {
    if (resumeApplications.length === 0) return null;
    const selected = resumeApplications.find(
      (application) => application.job_id === selectedJobId,
    );
    return selected?.job_id ?? resumeApplications[0].job_id;
  }, [resumeApplications, selectedJobId]);

  const startMutation = useMutation({
    mutationFn: () => {
      if (!activeResumeId) {
        throw new Error('면접을 시작할 이력서가 없습니다.');
      }
      return mockInterviewApi.start({
        resume_id: activeResumeId,
        job_id: activeJobId,
      });
    },
    onSuccess: (result) => {
      setError(null);
      setSession(result.session);
      setAnswerDraft('');
    },
    onError: (err: ApiError | Error) => {
      setError(err.message || '모의면접을 시작하지 못했습니다.');
    },
  });

  const answerMutation = useMutation({
    mutationFn: (answer: string) => {
      if (!session) {
        throw new Error('진행 중인 면접이 없습니다.');
      }
      return mockInterviewApi.answer({
        sessionId: session.session_id,
        answer,
      });
    },
    onSuccess: (result) => {
      setError(null);
      setSession(result.session);
      setAnswerDraft('');
    },
    onError: (err: ApiError | Error) => {
      setError(err.message || '답변을 제출하지 못했습니다.');
    },
  });

  const finishMutation = useMutation({
    mutationFn: () => {
      if (!session) {
        throw new Error('진행 중인 면접이 없습니다.');
      }
      return mockInterviewApi.finish(session.session_id);
    },
    onSuccess: (result) => {
      setError(null);
      setSession(result.session);
    },
    onError: (err: ApiError | Error) => {
      setError(err.message || '종합 리포트를 만들지 못했습니다.');
    },
  });

  const isLoading = resumesLoading || applicationsLoading;
  const canStart = Boolean(activeResumeId && activeJobId);
  const currentTurn = session?.turns.find((turn) => !turn.user_answer) ?? null;
  const readyToFinish =
    Boolean(session) &&
    session?.status === 'IN_PROGRESS' &&
    session.turns.length >= 6 &&
    session.turns.every((turn) => turn.user_answer);

  function handleResumeChange(value: string) {
    const nextResumeId = Number(value);
    setSelectedResumeId(Number.isFinite(nextResumeId) ? nextResumeId : null);
    setSelectedJobId(null);
    setSession(null);
    setAnswerDraft('');
  }

  function handleSubmitAnswer() {
    const answer = answerDraft.trim();
    if (!answer || answerMutation.isPending || !currentTurn) return;
    answerMutation.mutate(answer);
  }

  return (
    <div className="p-6 max-w-320 mx-auto">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[22px] font-bold text-m-text tracking-tight">
            모의면접
          </h1>
          <p className="text-[13px] text-m-muted mt-1">
            공고와 이력서를 바탕으로 한 문제씩 답변해보세요.
          </p>
        </div>
        {session && (
          <button
            type="button"
            onClick={() => {
              setSession(null);
              setAnswerDraft('');
              setError(null);
            }}
            className="h-9 px-3 rounded-lg border border-m-border bg-m-surface text-[12px] font-semibold text-m-muted hover:bg-m-surface-alt"
          >
            새 면접
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-m-danger/20 bg-m-danger-soft px-4 py-3 text-[13px] text-m-danger">
          {error}
        </div>
      )}

      {!session ? (
        <StartPanel
          resumes={readyResumes}
          applications={resumeApplications}
          selectedResumeId={activeResumeId}
          selectedJobId={activeJobId}
          isLoading={isLoading}
          isStarting={startMutation.isPending}
          canStart={canStart}
          onResumeChange={handleResumeChange}
          onJobChange={(jobId) => setSelectedJobId(jobId)}
          onStart={() => startMutation.mutate()}
        />
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)_280px] gap-5 max-lg:grid-cols-1">
          <section className="rounded-2xl border border-m-border bg-m-surface overflow-hidden">
            <div className="border-b border-m-border bg-m-surface-alt px-4 py-3">
              <StageStepper stage={session.stage} />
            </div>
            <div className="max-h-[calc(100vh-260px)] min-h-120 overflow-auto p-4 space-y-4">
              {session.turns.map((turn) => (
                <TurnBlock key={turn.turn_id} turn={turn} />
              ))}
              {finishMutation.isPending && (
                <div className="flex items-center gap-2 text-[13px] text-m-muted">
                  <Icon name="sparkle" size={16} className="animate-spin" />
                  종합 리포트를 정리하고 있어요
                </div>
              )}
            </div>
            {session.status === 'IN_PROGRESS' && (
              <div className="border-t border-m-border bg-m-surface-alt p-4">
                {readyToFinish ? (
                  <button
                    type="button"
                    onClick={() => finishMutation.mutate()}
                    disabled={finishMutation.isPending}
                    className="h-10 w-full rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover disabled:opacity-50"
                  >
                    종합 리포트 보기
                  </button>
                ) : (
                  <AnswerBox
                    value={answerDraft}
                    disabled={!currentTurn || answerMutation.isPending}
                    isSubmitting={answerMutation.isPending}
                    onChange={setAnswerDraft}
                    onSubmit={handleSubmitAnswer}
                  />
                )}
              </div>
            )}
          </section>

          <aside className="space-y-4">
            <ProgressPanel session={session} />
            {session.summary && <ReportPanel session={session} />}
          </aside>
        </div>
      )}
    </div>
  );
}

function StartPanel({
  resumes,
  applications,
  selectedResumeId,
  selectedJobId,
  isLoading,
  isStarting,
  canStart,
  onResumeChange,
  onJobChange,
  onStart,
}: {
  resumes: Resume[];
  applications: MyApplication[];
  selectedResumeId: number | null;
  selectedJobId: number | null;
  isLoading: boolean;
  isStarting: boolean;
  canStart: boolean;
  onResumeChange: (value: string) => void;
  onJobChange: (jobId: number) => void;
  onStart: () => void;
}) {
  return (
    <div className="rounded-2xl border border-m-border bg-m-surface p-5">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-semibold text-m-subtle">
            이력서
          </span>
          <select
            value={selectedResumeId ?? ''}
            onChange={(event) => onResumeChange(event.target.value)}
            disabled={isLoading || resumes.length === 0}
            className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary disabled:opacity-60"
          >
            {resumes.length === 0 ? (
              <option value="">분석 완료 이력서 없음</option>
            ) : (
              resumes.map((resume) => (
                <option key={resume.resume_id} value={resume.resume_id}>
                  {resume.title}
                </option>
              ))
            )}
          </select>
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-semibold text-m-subtle">
            지원 공고
          </span>
          <select
            value={selectedJobId ?? ''}
            onChange={(event) => onJobChange(Number(event.target.value))}
            disabled={isLoading || applications.length === 0}
            className="h-10 w-full rounded-lg border border-m-border bg-m-surface-alt px-3 text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary disabled:opacity-60"
          >
            {applications.length === 0 ? (
              <option value="">지원한 공고 없음</option>
            ) : (
              applications.map((application) => (
                <option
                  key={application.application_id}
                  value={application.job_id}
                >
                  {application.job_title} · {application.company_name ?? '기업명 미상'}
                </option>
              ))
            )}
          </select>
        </label>
      </div>
      <button
        type="button"
        onClick={onStart}
        disabled={!canStart || isStarting}
        className="mt-5 h-10 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
      >
        <Icon
          name="target"
          size={15}
          className={isStarting ? 'animate-spin' : undefined}
        />
        {isStarting ? '시작 중' : '면접 시작'}
      </button>
    </div>
  );
}

function StageStepper({ stage }: { stage: MockInterviewStage }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {STAGE_ORDER.map((item) => {
        const active = stage === item;
        const meta = STAGE_META[item];
        return (
          <div
            key={item}
            className={`rounded-lg border px-3 py-2 ${
              active
                ? 'border-m-primary bg-m-primary-soft'
                : 'border-m-border bg-m-surface'
            }`}
          >
            <p
              className={`text-[12px] font-semibold ${
                active ? 'text-m-primary' : 'text-m-muted'
              }`}
            >
              {meta.label}
            </p>
            <p className="text-[11px] text-m-subtle mt-0.5">{meta.short}</p>
          </div>
        );
      })}
    </div>
  );
}

function TurnBlock({ turn }: { turn: MockInterviewTurn }) {
  const meta = STAGE_META[turn.stage];
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-m-primary-soft text-m-primary flex items-center justify-center">
          <Icon name="target" size={15} />
        </div>
        <div className="min-w-0 max-w-[78%] rounded-2xl rounded-tl-md border border-m-border bg-m-surface-alt px-4 py-3">
          <span
            className={`inline-flex mb-2 rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}
          >
            {turn.turn_index}. {meta.label}
          </span>
          <p className="text-[14px] leading-relaxed text-m-text break-words">
            {turn.question}
          </p>
        </div>
      </div>

      {turn.user_answer && (
        <div className="flex justify-end">
          <div className="min-w-0 max-w-[78%] rounded-2xl rounded-tr-md bg-m-primary px-4 py-3 text-white">
            <p className="text-[13px] leading-relaxed whitespace-pre-wrap break-words">
              {turn.user_answer}
            </p>
          </div>
        </div>
      )}

      {turn.feedback && (
        <div className="ml-11 rounded-xl border border-m-border bg-m-surface px-3 py-2">
          <p className="text-[11px] font-semibold text-m-subtle mb-1">피드백</p>
          <p className="text-[12px] leading-relaxed text-m-muted">
            {turn.feedback}
          </p>
        </div>
      )}
    </div>
  );
}

function AnswerBox({
  value,
  disabled,
  isSubmitting,
  onChange,
  onSubmit,
}: {
  value: string;
  disabled: boolean;
  isSubmitting: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="flex gap-3">
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        rows={3}
        placeholder="답변을 입력하세요"
        className="min-h-20 flex-1 resize-none rounded-xl border border-m-border bg-m-surface px-3 py-2 text-[13px] leading-relaxed text-m-text placeholder:text-m-subtle focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary disabled:opacity-60"
      />
      <button
        type="button"
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
        className="w-24 rounded-xl bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? '제출 중' : '답변'}
      </button>
    </div>
  );
}

function ProgressPanel({ session }: { session: MockInterviewSession }) {
  const answered = session.turns.filter((turn) => turn.user_answer).length;
  return (
    <div className="rounded-2xl border border-m-border bg-m-surface p-4">
      <p className="text-[13px] font-semibold text-m-text">진행 상태</p>
      <div className="mt-3 h-2 rounded-full bg-m-surface-alt overflow-hidden">
        <div
          className="h-full rounded-full bg-m-primary transition-all"
          style={{ width: `${Math.min(100, (answered / 6) * 100)}%` }}
        />
      </div>
      <p className="mt-2 text-[12px] text-m-muted">{answered}/6 답변 완료</p>
      <div className="mt-4 space-y-2">
        {STAGE_ORDER.map((stage) => {
          const count = session.turns.filter((turn) => turn.stage === stage).length;
          return (
            <div key={stage} className="flex items-center justify-between text-[12px]">
              <span className="text-m-muted">{STAGE_META[stage].label}</span>
              <span className="font-semibold text-m-text">{count}문항</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ReportPanel({ session }: { session: MockInterviewSession }) {
  if (!session.summary) return null;
  const report = session.summary;
  return (
    <div className="rounded-2xl border border-m-border bg-m-surface p-4">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold text-m-text">종합 리포트</p>
        <span className="text-[24px] font-bold text-m-primary">
          {report.total_score}
        </span>
      </div>
      <p className="mt-3 text-[12px] leading-relaxed text-m-muted">
        {report.summary}
      </p>
      <ReportList title="강점" items={report.strengths} />
      <ReportList title="보완점" items={report.improvements} />
      <ReportList title="다음 연습" items={report.next_steps} />
    </div>
  );
}

function ReportList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-4">
      <p className="text-[12px] font-semibold text-m-text mb-2">{title}</p>
      <ul className="space-y-1.5">
        {items.map((item) => (
          <li key={item} className="text-[12px] leading-relaxed text-m-muted">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
