'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { resumesApi, type UploadResumeParams } from '../../api/resumes';
import type {
  ApiError,
  InterviewAnswerResponse,
  InterviewQuestionResponse,
  InterviewQuestionType,
  InterviewQuestionSource,
  InterviewSessionStatus,
  InterviewSessionResponse,
  Resume,
} from '../../api/types';

const MAX_RESUME_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.docx', '.txt'];

type UploadFlowStatus = 'idle' | 'uploading' | 'analyzing' | 'matching' | 'complete' | 'error';

interface UploadFlow {
  status: UploadFlowStatus;
  progress: number;
  fileName: string;
  fileSize: number;
}

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`;
  return `${(size / 1024 / 1024).toFixed(1)}MB`;
}

function statusLabel(status: Resume['parse_status']): string {
  if (status === 'COMPLETED') return '준비 완료';
  if (status === 'FAILED') return '확인 필요';
  return '처리 중';
}

function statusClass(status: Resume['parse_status']): string {
  if (status === 'COMPLETED') return 'bg-m-success-soft text-m-success';
  if (status === 'FAILED') return 'bg-m-danger-soft text-m-danger';
  return 'bg-m-warn-soft text-m-warn';
}

export default function ResumesPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [drag, setDrag] = useState(false);
  const [title, setTitle] = useState('');
  const [isDefault, setIsDefault] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Resume | null>(null);
  const [interviewSession, setInterviewSession] = useState<InterviewSessionResponse | null>(null);
  const [answerDrafts, setAnswerDrafts] = useState<Record<number, string>>({});
  const [uploadFlow, setUploadFlow] = useState<UploadFlow>({
    status: 'idle',
    progress: 0,
    fileName: '',
    fileSize: 0,
  });

  const { data: resumes = [], isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: resumesApi.getResumes,
  });

  const selectedId = selected?.resume_id ?? resumes[0]?.resume_id ?? null;

  const { data: selectedDetail } = useQuery({
    queryKey: ['resume', selectedId],
    queryFn: () => resumesApi.getResume(selectedId as number),
    enabled: selectedId !== null,
  });

  const uploadMutation = useMutation<Resume, ApiError, UploadResumeParams>({
    mutationFn: resumesApi.uploadResume,
    onSuccess: (resume) => {
      setTitle('');
      setError(null);
      setSelected(resume);
      setInterviewSession(null);
      setAnswerDrafts({});
      setUploadFlow((prev) => ({
        ...prev,
        status: 'complete',
        progress: 100,
      }));
      queryClient.setQueryData(['resume', resume.resume_id], resume);
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
    onError: (err: ApiError) => {
      setError(err.message || '이력서 업로드에 실패했습니다.');
      setUploadFlow((prev) => ({
        ...prev,
        status: 'error',
        progress: Math.max(prev.progress, 16),
      }));
    },
  });

  const deleteMutation = useMutation<void, ApiError, number>({
    mutationFn: resumesApi.deleteResume,
    onSuccess: (_, deletedResumeId) => {
      setSelected(null);
      setInterviewSession(null);
      setAnswerDrafts({});
      queryClient.removeQueries({ queryKey: ['resume', deletedResumeId] });
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
    onError: (err: ApiError) => {
      setError(err.message || '이력서 삭제에 실패했습니다.');
    },
  });

  const createInterviewSessionMutation = useMutation<InterviewSessionResponse, ApiError, number>({
    mutationFn: resumesApi.createInterviewSession,
    onSuccess: (session) => {
      setError(null);
      setInterviewSession(session);
      setAnswerDrafts({});
    },
    onError: (err: ApiError) => {
      setError(err.message || '면접 연습을 시작하지 못했습니다.');
    },
  });

  const submitAnswerMutation = useMutation<
    InterviewAnswerResponse,
    ApiError,
    { resumeId: number; questionId: number; answer: string }
  >({
    mutationFn: resumesApi.submitInterviewAnswer,
    onSuccess: (answer) => {
      setError(null);
      setInterviewSession((session) => {
        if (!session) return session;
        const questions = session.questions.map((question) =>
          question.question_id === answer.question_id ? { ...question, answer } : question,
        );
        const answeredScore = questions.reduce(
          (total, question) => total + (question.answer?.score ?? 0),
          0,
        );
        const allAnswered = questions.every((question) => question.answer);
        return {
          ...session,
          questions,
          total_score: answeredScore,
          status: allAnswered ? 'COMPLETED' : 'IN_PROGRESS',
        };
      });
    },
    onError: (err: ApiError) => {
      setError(err.message || '답변 평가에 실패했습니다.');
    },
  });

  const activeResume = selectedDetail ?? selected ?? resumes[0] ?? null;
  const previewResumeId = activeResume?.resume_id ?? null;
  const visibleInterviewSession =
    activeResume && interviewSession?.resume_id === activeResume.resume_id ? interviewSession : null;

  const {
    data: previewBlob,
    isFetching: isPreviewLoading,
    isError: isPreviewError,
  } = useQuery({
    queryKey: ['resume-file', previewResumeId],
    queryFn: () => resumesApi.getResumeFileBlob(previewResumeId as number),
    enabled: previewResumeId !== null,
  });

  const previewUrl = useMemo(() => {
    if (!previewBlob) return null;
    return URL.createObjectURL(previewBlob);
  }, [previewBlob]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const isUploadFlowVisible = uploadFlow.status !== 'idle';

  useEffect(() => {
    if (!uploadMutation.isPending) return;

    const timer = window.setInterval(() => {
      setUploadFlow((prev) => {
        if (!uploadMutation.isPending || prev.status === 'complete' || prev.status === 'error') {
          return prev;
        }

        const nextProgress = Math.min(prev.progress + 4, 92);
        let nextStatus: UploadFlowStatus = 'uploading';
        if (nextProgress >= 76) {
          nextStatus = 'matching';
        } else if (nextProgress >= 38) {
          nextStatus = 'analyzing';
        }

        return {
          ...prev,
          progress: nextProgress,
          status: nextStatus,
        };
      });
    }, 520);

    return () => window.clearInterval(timer);
  }, [uploadMutation.isPending]);

  function upload(file: File | undefined) {
    if (!file) return;
    const lowerName = file.name.toLowerCase();
    const isAllowed = ALLOWED_RESUME_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
    if (!isAllowed) {
      setError('PDF, DOCX, TXT 파일만 지원합니다.');
      setUploadFlow({
        status: 'error',
        progress: 0,
        fileName: file.name,
        fileSize: file.size,
      });
      return;
    }
    if (file.size > MAX_RESUME_UPLOAD_BYTES) {
      setError('이력서 파일은 최대 10MB까지 업로드할 수 있습니다.');
      setUploadFlow({
        status: 'error',
        progress: 0,
        fileName: file.name,
        fileSize: file.size,
      });
      return;
    }
    setError(null);
    setUploadFlow({
      status: 'uploading',
      progress: 8,
      fileName: file.name,
      fileSize: file.size,
    });
    uploadMutation.mutate({
      file,
      title: title.trim() || undefined,
      isDefault,
    });
  }

  return (
    <div className="p-6 max-w-[1060px] mx-auto">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-[20px] font-bold text-m-text tracking-tight mb-1">이력서</h1>
          <p className="text-[13px] text-m-muted">
            PDF, DOCX, TXT 이력서를 업로드하고 저장된 원본 파일을 확인하세요.
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="h-9 px-4 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors inline-flex items-center gap-2"
        >
          <Icon name="upload" size={15} />
          파일 선택
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-m-danger bg-m-danger-soft p-3 text-[13px] text-m-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-5">
        <div className="flex flex-col gap-4">
          <div className="bg-m-surface border border-m-border rounded-2xl p-5">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              className="hidden"
              onChange={(e) => {
                upload(e.target.files?.[0]);
                e.currentTarget.value = '';
              }}
            />
            <div className="mb-3">
              <label className="block text-[12px] font-semibold text-m-text mb-1.5">제목</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="백엔드 개발자 이력서"
                className="w-full h-9 px-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
              />
            </div>

            <label className="flex items-center gap-2 mb-4 text-[13px] text-m-muted">
              <input
                type="checkbox"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="w-4 h-4"
              />
              기본 이력서로 설정
            </label>

            <div
              onDragEnter={(e) => {
                e.preventDefault();
                setDrag(true);
              }}
              onDragOver={(e) => e.preventDefault()}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDrag(false);
                upload(e.dataTransfer.files?.[0]);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`rounded-xl border-2 border-dashed py-12 text-center cursor-pointer transition-all ${
                isUploadFlowVisible ? 'hidden' : ''
              } ${
                drag
                  ? 'border-m-primary bg-m-primary-soft'
                  : 'border-m-border-strong bg-m-surface-alt hover:border-m-primary hover:bg-m-primary-soft'
              }`}
            >
              <div className="w-14 h-14 rounded-2xl bg-m-primary-soft text-m-primary flex items-center justify-center mx-auto mb-4">
                <Icon name="upload" size={26} />
              </div>
              <p className="text-[15px] font-semibold text-m-text mb-1">
                {uploadMutation.isPending ? '업로드 및 파싱 중...' : '파일을 끌어오거나 클릭하세요'}
              </p>
              <p className="text-[13px] text-m-muted">PDF, DOCX, TXT, 최대 10MB</p>
            </div>

            {isUploadFlowVisible && (
              <ResumeAnalysisProgress
                flow={uploadFlow}
                onChooseFile={() => fileInputRef.current?.click()}
                onReset={() => {
                  setUploadFlow({
                    status: 'idle',
                    progress: 0,
                    fileName: '',
                    fileSize: 0,
                  });
                  setError(null);
                }}
              />
            )}
          </div>

          <div>
            <h2 className="text-[14px] font-semibold text-m-text mb-3">등록된 이력서</h2>
            <div className="flex flex-col gap-2.5">
              {isLoading ? (
                <div className="bg-m-surface border border-m-border rounded-xl p-4 text-[13px] text-m-subtle">
                  이력서를 불러오는 중...
                </div>
              ) : resumes.length === 0 ? (
                <div className="bg-m-surface border border-m-border rounded-xl p-4 text-[13px] text-m-subtle">
                  아직 등록된 이력서가 없습니다.
                </div>
              ) : (
                resumes.map((resume) => (
                  <button
                    key={resume.resume_id}
                    onClick={() => {
                      setSelected(resume);
                      setInterviewSession(null);
                      setAnswerDrafts({});
                    }}
                    className={`bg-m-surface border rounded-xl p-4 flex items-center gap-4 text-left transition-colors ${
                      activeResume?.resume_id === resume.resume_id
                        ? 'border-m-primary bg-m-primary-soft'
                        : 'border-m-border hover:bg-m-surface-alt'
                    }`}
                  >
                    <div className="w-10 h-10 rounded-lg bg-m-primary-soft text-m-primary flex items-center justify-center flex-shrink-0">
                      <Icon name="pdf" size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-m-text truncate">
                        {resume.title}
                        {resume.is_default && (
                          <span className="ml-2 text-[11px] px-1.5 py-0.5 bg-m-primary text-white rounded font-medium">
                            기본
                          </span>
                        )}
                      </p>
                      <p className="text-[12px] text-m-muted mt-0.5 truncate">
                        {resume.original_filename} - {formatFileSize(resume.file_size)}
                      </p>
                    </div>
                    <span className={`text-[11px] font-semibold px-2 py-1 rounded-full ${statusClass(resume.parse_status)}`}>
                      {statusLabel(resume.parse_status)}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="bg-m-surface border border-m-border rounded-2xl min-h-[520px]">
          {activeResume ? (
            <div className="p-5">
              <div className="flex items-start justify-between gap-4 mb-5">
                <div>
                  <h2 className="text-[18px] font-bold text-m-text">{activeResume.title}</h2>
                  <p className="text-[13px] text-m-muted mt-1">
                    {activeResume.original_filename} - 등록일{' '}
                    {new Date(activeResume.created_at).toLocaleDateString('ko-KR')}
                  </p>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(activeResume.resume_id)}
                  disabled={deleteMutation.isPending}
                  className="h-8 px-3 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt disabled:opacity-50 flex-shrink-0"
                >
                  삭제
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
                <SummaryTile label="상태" value={statusLabel(activeResume.parse_status)} />
                <SummaryTile label="파일 크기" value={formatFileSize(activeResume.file_size)} />
                <SummaryTile
                  label="파일 형식"
                  value={activeResume.content_type.split('/')[1]?.toUpperCase() || '문서'}
                />
              </div>

              {activeResume.parse_error && (
                <div className="mb-5 rounded-xl border border-m-warn bg-m-warn-soft p-3 text-[13px] text-m-warn">
                  {activeResume.parse_error}
                </div>
              )}

              <InterviewPracticePanel
                resume={activeResume}
                session={visibleInterviewSession}
                answerDrafts={answerDrafts}
                isCreating={createInterviewSessionMutation.isPending}
                submittingQuestionId={submitAnswerMutation.variables?.questionId ?? null}
                isSubmitting={submitAnswerMutation.isPending}
                onStart={() => createInterviewSessionMutation.mutate(activeResume.resume_id)}
                onDraftChange={(questionId, value) =>
                  setAnswerDrafts((prev) => ({ ...prev, [questionId]: value }))
                }
                onSubmit={(questionId) => {
                  const answer = (answerDrafts[questionId] || '').trim();
                  if (!answer) return;
                  submitAnswerMutation.mutate({
                    resumeId: activeResume.resume_id,
                    questionId,
                    answer,
                  });
                }}
              />

              <div className="mb-4">
                <h3 className="text-[14px] font-semibold text-m-text">파일 미리보기</h3>
              </div>

              <div className="rounded-2xl border border-m-border bg-m-surface-alt overflow-hidden aspect-[1/1.4] relative">
                {isPreviewLoading ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex flex-col items-center gap-3">
                      <Icon name="sparkle" size={32} className="animate-spin text-m-primary" />
                      <p className="text-[13px] text-m-muted font-medium">문서를 불러오는 중...</p>
                    </div>
                  </div>
                ) : previewUrl && !isPreviewError ? (
                  <iframe
                    src={previewUrl}
                    className="w-full h-full border-none"
                    title="이력서 미리보기"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center p-8 text-center">
                    <div className="max-w-[240px]">
                      <div className="w-12 h-12 rounded-full bg-m-danger-soft text-m-danger flex items-center justify-center mx-auto mb-3">
                        <Icon name="x" size={24} />
                      </div>
                      <p className="text-[14px] font-semibold text-m-text mb-1">
                        미리보기를 불러올 수 없습니다
                      </p>
                      <p className="text-[12px] text-m-muted">
                        파일이 없거나 아직 로딩 중일 수 있습니다. 잠시 후 다시 시도해 주세요.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-[14px] text-m-subtle">
              이력서를 업로드하면 여기에서 미리볼 수 있습니다.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-m-surface-alt p-3">
      <p className="text-[11px] text-m-subtle mb-1">{label}</p>
      <p className="text-[13px] font-semibold text-m-text">{value}</p>
    </div>
  );
}

function InterviewPracticePanel({
  resume,
  session,
  answerDrafts,
  isCreating,
  submittingQuestionId,
  isSubmitting,
  onStart,
  onDraftChange,
  onSubmit,
}: {
  resume: Resume;
  session: InterviewSessionResponse | null;
  answerDrafts: Record<number, string>;
  isCreating: boolean;
  submittingQuestionId: number | null;
  isSubmitting: boolean;
  onStart: () => void;
  onDraftChange: (questionId: number, value: string) => void;
  onSubmit: (questionId: number) => void;
}) {
  const canStart = resume.parse_status === 'COMPLETED';

  return (
    <div className="mb-5 rounded-2xl border border-m-border bg-m-surface-alt p-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-[14px] font-semibold text-m-text">면접 연습</h3>
          <p className="text-[12px] text-m-muted mt-1">
            질문은 한 번만 생성되어 저장됩니다. 이 화면을 다시 열어도 OpenAI를 다시 호출하지 않습니다.
          </p>
        </div>
        <button
          type="button"
          onClick={onStart}
          disabled={isCreating || !canStart}
          className="h-9 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-2"
        >
          <Icon name="sparkle" size={14} className={isCreating ? 'animate-spin' : undefined} />
          {isCreating ? '시작 중...' : session ? '다시 시작' : '면접 연습 시작'}
        </button>
      </div>

      {!canStart && (
        <div className="rounded-xl border border-dashed border-m-border bg-m-surface p-4 text-[13px] text-m-muted">
          이력서 파싱이 완료되어야 면접 연습을 시작할 수 있습니다.
        </div>
      )}

      {canStart && !session && (
        <div className="rounded-xl border border-dashed border-m-border bg-m-surface p-4 text-[13px] text-m-muted">
          면접 연습을 시작하면 이 이력서 기반 질문 5개가 생성됩니다.
        </div>
      )}

      {session && (
        <div className="grid grid-cols-1 gap-3">
          <div className="flex flex-wrap items-center gap-2 text-[12px] text-m-muted">
            <span className="px-2 py-1 rounded-full bg-m-surface text-m-text font-semibold">
              {session.model}
            </span>
            <span>
              점수: {session.total_score ?? 0}/{session.max_score}
            </span>
            <span>상태: {sessionStatusLabel(session.status)}</span>
          </div>
          {session.questions.map((question) => (
            <InterviewQuestionCard
              key={question.question_id}
              question={question}
              draft={answerDrafts[question.question_id] ?? question.answer?.user_answer ?? ''}
              isSubmitting={isSubmitting && submittingQuestionId === question.question_id}
              onDraftChange={(value) => onDraftChange(question.question_id, value)}
              onSubmit={() => onSubmit(question.question_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function InterviewQuestionCard({
  question,
  draft,
  isSubmitting,
  onDraftChange,
  onSubmit,
}: {
  question: InterviewQuestionResponse;
  draft: string;
  isSubmitting: boolean;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="rounded-xl border border-m-border bg-m-surface p-3">
      <div className="flex items-start gap-3">
        <span className="w-7 h-7 rounded-full bg-m-primary-soft text-m-primary text-[12px] font-bold flex items-center justify-center flex-shrink-0">
          {question.display_order}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-m-surface-alt text-m-muted">
              {sourceLabel(question.source)}
            </span>
            <span className="text-[11px] text-m-subtle">{questionTypeLabel(question.question_type)}</span>
            <span className="text-[11px] text-m-subtle">{difficultyLabel(question.difficulty)}</span>
            <span className="text-[11px] text-m-subtle">{question.max_score}점</span>
          </div>
          <p className="text-[13px] font-semibold text-m-text leading-relaxed">
            {question.question}
          </p>
          <p className="text-[12px] text-m-muted mt-1.5 leading-relaxed">
            {question.intent}
          </p>

          {question.expected_keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {question.expected_keywords.map((keyword) => (
                <span
                  key={keyword}
                  className="px-2 py-0.5 rounded-full bg-m-primary-soft text-m-primary text-[11px] font-medium"
                >
                  {keyword}
                </span>
              ))}
            </div>
          )}

          {question.official_references.length > 0 && (
            <div className="mt-2 grid grid-cols-1 gap-1.5">
              {question.official_references.map((ref) => (
                <a
                  key={ref.url}
                  href={ref.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-m-primary hover:underline truncate"
                >
                  {ref.title}
                </a>
              ))}
            </div>
          )}

          <textarea
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            rows={4}
            className="mt-3 w-full resize-y rounded-lg border border-m-border bg-m-surface-alt px-3 py-2 text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            placeholder="답변을 입력하세요."
          />
          <div className="mt-2 flex justify-end">
            <button
              type="button"
              onClick={onSubmit}
              disabled={isSubmitting || !draft.trim()}
              className="h-8 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              <Icon name="check" size={13} />
              {isSubmitting ? '평가 중...' : question.answer ? '다시 평가' : '답변 제출'}
            </button>
          </div>

          {question.answer && <InterviewAnswerResult answer={question.answer} />}
        </div>
      </div>
    </div>
  );
}

function InterviewAnswerResult({ answer }: { answer: InterviewAnswerResponse }) {
  return (
    <div className="mt-3 rounded-lg border border-m-border bg-m-surface-alt p-3">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-[12px] font-bold text-m-text">
          점수: {answer.score}/{answer.max_score}
        </span>
      </div>
      <ResultList title="잘한 점" items={answer.strengths.slice(0, 2)} />
      <ResultList title="아쉬운 점" items={answer.missing_points.slice(0, 2)} />
      <div className="mt-2">
        <p className="text-[11px] font-semibold text-m-subtle mb-1">보완 답변</p>
        <p className="text-[12px] text-m-muted leading-relaxed">{answer.reference_based_answer}</p>
      </div>
      <div className="mt-2">
        <p className="text-[11px] font-semibold text-m-subtle mb-1">맞은 부분 / 다른 부분</p>
        <ul className="space-y-1">
          <li className="text-[12px] text-m-muted leading-relaxed">
            - 맞은 부분: {answer.correct_points[0] || answer.strengths[0] || '명확히 확인된 내용이 없습니다.'}
          </li>
          <li className="text-[12px] text-m-muted leading-relaxed">
            - 다른 부분: {answer.different_points[0] || answer.incorrect_points[0] || '명확한 오류는 확인되지 않았습니다.'}
          </li>
        </ul>
      </div>
    </div>
  );
}

function ResultList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-2">
      <p className="text-[11px] font-semibold text-m-subtle mb-1">{title}</p>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item} className="text-[12px] text-m-muted leading-relaxed">
            - {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResumeAnalysisProgress({
  flow,
  onChooseFile,
  onReset,
}: {
  flow: UploadFlow;
  onChooseFile: () => void;
  onReset: () => void;
}) {
  const currentStep = flow.status === 'uploading' ? 1 : flow.status === 'analyzing' ? 2 : 3;
  const isComplete = flow.status === 'complete';
  const isError = flow.status === 'error';
  const heading = getUploadFlowHeading(flow.status);
  const subtext = getUploadFlowSubtext(flow.status);
  const progress = isComplete ? 100 : Math.max(0, Math.min(100, flow.progress));
  const checklist = [
    { label: '텍스트 추출 완료', done: progress >= 38 || isComplete },
    { label: '이력서 파싱 완료', done: progress >= 76 || isComplete },
    { label: '화면 준비 완료', done: isComplete },
    { label: '미리보기 준비 완료', done: isComplete },
  ];

  return (
    <div className="rounded-xl border border-m-border bg-white p-4">
      <AnalysisStepper currentStep={currentStep} isComplete={isComplete} isError={isError} />

      <div className="mt-5 flex items-start gap-4">
        <div
          className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
            isComplete
              ? 'bg-m-success-soft text-m-success'
              : isError
                ? 'bg-m-danger-soft text-m-danger'
                : 'bg-m-primary-soft text-m-primary'
          }`}
        >
          {isComplete ? (
            <Icon name="check" size={28} strokeWidth={2.5} />
          ) : isError ? (
            <Icon name="x" size={24} strokeWidth={2.5} />
          ) : (
            <Icon name="sparkle" size={25} strokeWidth={2} className="animate-spin" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[15px] font-bold text-m-text">{heading}</p>
              <p className="text-[12px] text-m-muted mt-0.5 truncate">
                {flow.fileName || '이력서 파일'} - {flow.fileSize ? formatFileSize(flow.fileSize) : '대기 중'}
              </p>
            </div>
            <p className="text-[15px] font-bold text-m-primary tabular-nums">{progress}%</p>
          </div>

          <div className="mt-4 h-2 rounded-full bg-m-surface-alt overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isError ? 'bg-m-danger' : isComplete ? 'bg-m-success' : 'bg-m-primary'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>

          <p className="mt-3 text-[12px] text-m-muted">{subtext}</p>

          {!isError && (
            <div className="mt-4 grid grid-cols-1 gap-2">
              {checklist.map((item) => (
                <div key={item.label} className="flex items-center gap-2 text-[12px] text-m-muted">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center ${
                      item.done ? 'bg-m-success text-white' : 'bg-m-surface-alt text-m-subtle'
                    }`}
                  >
                    {item.done ? (
                      <Icon name="check" size={13} strokeWidth={2.4} />
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    )}
                  </span>
                  {item.label}
                </div>
              ))}
            </div>
          )}

          {(isComplete || isError) && (
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={onChooseFile}
                className="h-8 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover transition-colors"
              >
                다른 파일 선택
              </button>
              <button
                type="button"
                onClick={onReset}
                className="h-8 px-3 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
              >
                초기화
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalysisStepper({
  currentStep,
  isComplete,
  isError,
}: {
  currentStep: number;
  isComplete: boolean;
  isError: boolean;
}) {
  const steps = ['업로드', '파싱', '완료'];

  return (
    <div className="flex items-center justify-center gap-2 text-[12px] font-semibold">
      {steps.map((label, index) => {
        const step = index + 1;
        const done = isComplete || step < currentStep;
        const active = !isComplete && step === currentStep && !isError;

        return (
          <div key={label} className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <span
                className={`w-7 h-7 rounded-full flex items-center justify-center ${
                  done
                    ? 'bg-m-success text-white'
                    : active
                      ? 'bg-m-primary text-white'
                      : isError && step === currentStep
                        ? 'bg-m-danger text-white'
                        : 'bg-m-surface-alt text-m-subtle'
                }`}
              >
                {done ? <Icon name="check" size={15} strokeWidth={2.4} /> : step}
              </span>
              <span className={done || active ? 'text-m-text' : 'text-m-muted'}>{label}</span>
            </div>
            {index < steps.length - 1 && <span className="w-8 h-px bg-m-border" />}
          </div>
        );
      })}
    </div>
  );
}

function getUploadFlowHeading(status: UploadFlowStatus): string {
  if (status === 'uploading') return '이력서 업로드 중';
  if (status === 'analyzing') return '이력서 파싱 중';
  if (status === 'matching') return '이력서 데이터 준비 중';
  if (status === 'complete') return '업로드 완료';
  if (status === 'error') return '업로드 실패';
  return '이력서 준비 중';
}

function getUploadFlowSubtext(status: UploadFlowStatus): string {
  if (status === 'uploading') return '파일을 저장하고 텍스트 추출을 시작합니다.';
  if (status === 'analyzing') return '이력서 내용을 구조화된 데이터로 파싱하고 있습니다.';
  if (status === 'matching') return '사용자 화면에 표시할 이력서 데이터를 준비하고 있습니다.';
  if (status === 'complete') return '이력서가 저장되었습니다. 원본 파일을 미리볼 수 있습니다.';
  if (status === 'error') return '파일 형식, 용량, 업로드 상태를 확인한 뒤 다시 시도해 주세요.';
  return '잠시만 기다려 주세요.';
}

function sourceLabel(source: InterviewQuestionSource): string {
  if (source === 'project') return '프로젝트';
  if (source === 'tech_stack') return '기술';
  if (source === 'experience') return '경험';
  if (source === 'cover_letter') return '자기소개서';
  return '이력서';
}

function questionTypeLabel(type: InterviewQuestionType): string {
  if (type === 'PROJECT') return '프로젝트';
  if (type === 'TECH_STACK') return '기술';
  if (type === 'EXPERIENCE') return '경험';
  if (type === 'COVER_LETTER') return '자기소개서';
  return '직무 적합성';
}

function difficultyLabel(difficulty: string): string {
  if (difficulty === 'INTERMEDIATE') return '중급';
  if (difficulty === 'BASIC') return '기초';
  return difficulty;
}

function sessionStatusLabel(status: InterviewSessionStatus): string {
  if (status === 'COMPLETED') return '완료';
  return '진행 중';
}
