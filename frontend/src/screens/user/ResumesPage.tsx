'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { resumesApi, type UploadResumeParams } from '../../api/resumes';
import type { ApiError, Resume } from '../../api/types';

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
  if (status === 'COMPLETED') return '처리 완료';
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
      queryClient.removeQueries({ queryKey: ['resume', deletedResumeId] });
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
    onError: (err: ApiError) => {
      setError(err.message || '이력서 삭제에 실패했습니다.');
    },
  });

  const activeResume = selectedDetail ?? selected ?? resumes[0] ?? null;
  const previewResumeId = activeResume?.resume_id ?? null;

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
      setError('PDF, DOCX, TXT 파일만 업로드할 수 있습니다.');
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
          <h1 className="text-[20px] font-bold text-m-text tracking-tight mb-1">내 이력서</h1>
          <p className="text-[13px] text-m-muted">
            PDF, DOCX, TXT 파일을 저장하고 원본 문서를 미리 확인합니다.
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
              <label className="block text-[12px] font-semibold text-m-text mb-1.5">이력서 제목</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="예: 백엔드 개발자 이력서"
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
                isUploadFlowVisible
                  ? 'hidden'
                  : ''
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
                {uploadMutation.isPending ? '업로드 및 파싱 중...' : '파일을 끌어다 놓거나 클릭하세요'}
              </p>
              <p className="text-[13px] text-m-muted">PDF · DOCX · TXT · 최대 10MB</p>
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
            <h2 className="text-[14px] font-semibold text-m-text mb-3">등록한 이력서</h2>
            <div className="flex flex-col gap-2.5">
              {isLoading ? (
                <div className="bg-m-surface border border-m-border rounded-xl p-4 text-[13px] text-m-subtle">
                  불러오는 중...
                </div>
              ) : resumes.length === 0 ? (
                <div className="bg-m-surface border border-m-border rounded-xl p-4 text-[13px] text-m-subtle">
                  아직 등록한 이력서가 없습니다.
                </div>
              ) : (
                resumes.map((resume) => (
                  <button
                    key={resume.resume_id}
                    onClick={() => setSelected(resume)}
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
                        {resume.original_filename} · {formatFileSize(resume.file_size)}
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
                    {activeResume.original_filename} · 등록일{' '}
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
                <div className="rounded-xl bg-m-surface-alt p-3">
                  <p className="text-[11px] text-m-subtle mb-1">상태</p>
                  <p className="text-[13px] font-semibold text-m-text">{statusLabel(activeResume.parse_status)}</p>
                </div>
                <div className="rounded-xl bg-m-surface-alt p-3">
                  <p className="text-[11px] text-m-subtle mb-1">파일 크기</p>
                  <p className="text-[13px] font-semibold text-m-text">{formatFileSize(activeResume.file_size)}</p>
                </div>
                <div className="rounded-xl bg-m-surface-alt p-3">
                  <p className="text-[11px] text-m-subtle mb-1">파일 형식</p>
                  <p className="text-[13px] font-semibold text-m-text">
                    {activeResume.content_type.split('/')[1]?.toUpperCase() || 'DOCUMENT'}
                  </p>
                </div>
              </div>

              {activeResume.parse_error && (
                <div className="mb-5 rounded-xl border border-m-warn bg-m-warn-soft p-3 text-[13px] text-m-warn">
                  {activeResume.parse_error}
                </div>
              )}

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
                    title="Resume Preview"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center p-8 text-center">
                    <div className="max-w-[240px]">
                      <div className="w-12 h-12 rounded-full bg-m-danger-soft text-m-danger flex items-center justify-center mx-auto mb-3">
                        <Icon name="x" size={24} />
                      </div>
                      <p className="text-[14px] font-semibold text-m-text mb-1">미리보기를 불러올 수 없음</p>
                      <p className="text-[12px] text-m-muted">
                        파일이 없거나 불러오는 중 에러가 발생했습니다. 나중에 다시 시도해 주세요.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-[14px] text-m-subtle">
              이력서를 등록하면 파일 미리보기가 표시됩니다.
            </div>
          )}
        </div>
      </div>
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
    { label: '경력 및 스킬 파싱 완료', done: progress >= 76 || isComplete },
    { label: '맞춤 채용공고 준비 중', done: isComplete },
    { label: '강점/약점 분석', done: isComplete },
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
                {flow.fileName || '이력서 파일'} · {flow.fileSize ? formatFileSize(flow.fileSize) : '대기 중'}
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
                    {item.done ? <Icon name="check" size={13} strokeWidth={2.4} /> : <span className="w-1.5 h-1.5 rounded-full bg-current" />}
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
                닫기
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
  const steps = ['이력서 업로드', 'AI 분석', '맞춤 채용공고'];

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
  if (status === 'uploading') return '이력서를 업로드하고 있어요';
  if (status === 'analyzing') return '이력서를 처리하고 있어요';
  if (status === 'matching') return '맞춤 채용공고를 준비하고 있어요';
  if (status === 'complete') return '업로드 완료!';
  if (status === 'error') return '업로드를 완료하지 못했어요';
  return '이력서를 준비하고 있어요';
}

function getUploadFlowSubtext(status: UploadFlowStatus): string {
  if (status === 'uploading') return '파일을 서버에 저장하고 텍스트 추출을 준비하는 중입니다.';
  if (status === 'analyzing') return '문서 내용을 읽고 서비스에서 사용할 정보를 정리하는 중입니다.';
  if (status === 'matching') return '매칭 화면에서 사용할 이력서 정보를 준비하는 중입니다.';
  if (status === 'complete') return '이력서 파일이 저장되었습니다. 미리보기에서 원본을 확인해 보세요.';
  if (status === 'error') return '파일 형식, 용량 또는 업로드 오류를 확인한 뒤 다시 시도해 주세요.';
  return '잠시만 기다려 주세요.';
}
