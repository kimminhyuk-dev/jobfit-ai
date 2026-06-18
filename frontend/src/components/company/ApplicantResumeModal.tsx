'use client';

import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Icon from '../ui/Icon';
import { showToast } from '../ui/Toast';
import { Alert } from '../ui/alert';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { companyApi } from '../../api/company';
import type { ApiError } from '../../api/client';
import type {
  ApplicationStatus,
  CompanyApplicantResume,
  InterviewEmailPayload,
} from '../../api/types';

const STATUS_META: Record<ApplicationStatus, { label: string; cls: string }> = {
  SUBMITTED: { label: '접수', cls: 'bg-m-primary-soft text-m-primary' },
  VIEWED: { label: '이력서 열람', cls: 'bg-m-warn-soft text-m-warn' },
  REJECTED: { label: '불합격', cls: 'bg-m-danger-soft text-m-danger' },
  INTERVIEW: { label: '면접', cls: 'bg-m-success-soft text-m-success' },
  CANCELED: { label: '지원취소', cls: 'bg-m-surface-alt text-m-subtle' },
};

function dateStr(value: string | null): string {
  if (!value) return '';
  const d = new Date(value);
  return isNaN(d.getTime())
    ? ''
    : d.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}

function isPdf(data: CompanyApplicantResume, blob?: Blob): boolean {
  const name = data.original_filename.toLowerCase();
  return data.content_type === 'application/pdf' || blob?.type === 'application/pdf' || name.endsWith('.pdf');
}

function isImage(data: CompanyApplicantResume, blob?: Blob): boolean {
  const name = data.original_filename.toLowerCase();
  const type = blob?.type || data.content_type;
  return (
    type.startsWith('image/') ||
    name.endsWith('.png') ||
    name.endsWith('.jpg') ||
    name.endsWith('.jpeg') ||
    name.endsWith('.gif')
  );
}

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`;
  return `${(size / 1024 / 1024).toFixed(1)}MB`;
}

function getMatchScoreClass(grade?: string): string {
  if (grade === 'A') return 'bg-m-success-soft text-m-success';
  if (grade === 'B') return 'bg-m-primary-soft text-m-primary';
  if (grade === 'C') return 'bg-m-warn-soft text-m-warn';
  return 'bg-m-surface-alt text-m-subtle';
}

function toDateTimeLocalValue(value: Date): string {
  const pad = (num: number) => String(num).padStart(2, '0');
  return [
    value.getFullYear(),
    pad(value.getMonth() + 1),
    pad(value.getDate()),
  ].join('-') + `T${pad(value.getHours())}:${pad(value.getMinutes())}`;
}

function getMinInterviewAt(): string {
  const date = new Date(Date.now() + 60 * 1000);
  date.setSeconds(0, 0);
  return toDateTimeLocalValue(date);
}

function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as ApiError).message;
    if (typeof message === 'string' && message.trim()) return message;
  }
  return '면접 안내 메일 발송에 실패했습니다.';
}

export default function ApplicantResumeModal({
  applicationId,
  companyAddress,
  onClose,
  onViewed,
  onInterviewSent,
}: {
  applicationId: number;
  companyAddress?: string | null;
  onClose: () => void;
  onViewed: () => void;
  onInterviewSent?: () => void;
}) {
  const queryClient = useQueryClient();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isInterviewFormOpen, setIsInterviewFormOpen] = useState(false);
  const [interviewAt, setInterviewAt] = useState('');
  const [locationAddress, setLocationAddress] = useState(companyAddress?.trim() ?? '');
  const [message, setMessage] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, isError, isSuccess } = useQuery({
    queryKey: ['company', 'applicant-resume', applicationId],
    queryFn: () => companyApi.viewApplicantResume(applicationId),
    staleTime: 0,
  });

  const {
    data: previewBlob,
    isFetching: isPreviewLoading,
    isError: isPreviewError,
  } = useQuery({
    queryKey: ['company', 'applicant-resume-file', applicationId],
    queryFn: () => companyApi.getApplicantResumeFileBlob(applicationId),
    enabled: Boolean(data),
  });

  useEffect(() => {
    if (isSuccess) onViewed();
  }, [isSuccess, onViewed]);

  const previewUrl = useMemo(() => {
    if (!previewBlob) return null;
    return URL.createObjectURL(previewBlob);
  }, [previewBlob]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function handleDownload() {
    if (!data || isDownloading) return;
    setIsDownloading(true);
    try {
      const blob = await companyApi.getApplicantResumeFileBlob(applicationId, true);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = data.original_filename || `${data.resume_title}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      showToast('이력서 파일 다운로드에 실패했습니다.', 'error');
    } finally {
      setIsDownloading(false);
    }
  }

  const interviewMutation = useMutation({
    mutationFn: (payload: InterviewEmailPayload) =>
      companyApi.sendInterviewEmail(applicationId, payload),
    onSuccess: (response) => {
      setIsInterviewFormOpen(false);
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['company', 'applicant-resume', applicationId] });
      onInterviewSent?.();
      showToast(response.message || '면접 안내 메일을 발송했습니다.', 'success');
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error');
    },
  });

  function handleInterviewEmail() {
    if (!data) return;
    setFormError(null);
    if (!locationAddress.trim() && companyAddress?.trim()) {
      setLocationAddress(companyAddress.trim());
    }
    setIsInterviewFormOpen(true);
  }

  function handleInterviewSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    if (!interviewAt) {
      setFormError('면접 날짜와 시간을 입력해 주세요.');
      return;
    }

    const selectedAt = new Date(interviewAt);
    if (Number.isNaN(selectedAt.getTime())) {
      setFormError('면접 날짜와 시간을 다시 확인해 주세요.');
      return;
    }
    if (selectedAt.getTime() <= Date.now()) {
      setFormError('현재 시각 이후의 면접 일정을 선택해 주세요.');
      return;
    }

    const normalizedAddress = locationAddress.trim();
    if (!normalizedAddress) {
      setFormError('면접 장소 주소를 입력해 주세요.');
      return;
    }

    interviewMutation.mutate({
      interview_at: selectedAt.toISOString(),
      location_address: normalizedAddress,
      message: message.trim() || null,
    });
  }

  const minInterviewAt = getMinInterviewAt();
  const canPreview = data && previewUrl && (isPdf(data, previewBlob) || isImage(data, previewBlob));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4">
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col rounded-2xl bg-m-surface shadow-xl">
        <div className="flex items-start justify-between gap-3 border-b border-m-border p-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="truncate text-[17px] font-bold text-m-text">
                {data?.applicant_name ?? '지원자'} 님의 이력서
              </h2>
              {data && (
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS_META[data.status].cls}`}>
                  {STATUS_META[data.status].label}
                </span>
              )}
            </div>
            <p className="mt-1 truncate text-[12px] text-m-muted">
              {data?.applicant_email}
              {data?.job_title ? ` · ${data.job_title}` : ''}
            </p>
          </div>
          <button onClick={onClose} className="shrink-0 p-1 text-m-subtle hover:text-m-muted" aria-label="닫기">
            <Icon name="x" size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto bg-m-surface-alt p-5 scrollbar-thin">
          {isLoading ? (
            <div className="flex min-h-[520px] items-center justify-center text-[13px] text-m-subtle">
              이력서를 불러오는 중...
            </div>
          ) : isError || !data ? (
            <div className="flex min-h-[520px] items-center justify-center text-[13px] text-m-subtle">
              이력서를 불러오지 못했습니다.
            </div>
          ) : (
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
              <div className="min-h-[560px] overflow-hidden rounded-xl border border-m-border bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-m-border bg-m-surface px-4 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-[12px] font-semibold text-m-text">{data.original_filename}</p>
                    <p className="text-[11px] text-m-subtle">
                      {data.content_type} · {formatFileSize(data.file_size)}
                    </p>
                  </div>
                  <button
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-m-border px-3 text-[12px] font-semibold text-m-muted hover:bg-m-surface-alt disabled:opacity-50"
                  >
                    <Icon name="download" size={14} />
                    다운로드
                  </button>
                </div>

                <div className="h-[calc(88vh-210px)] min-h-[500px] bg-[#eef1f5]">
                  {isPreviewLoading ? (
                    <div className="flex h-full items-center justify-center">
                      <Icon name="sparkle" size={24} className="animate-spin text-m-primary" />
                    </div>
                  ) : canPreview && isPdf(data, previewBlob) ? (
                    <iframe src={previewUrl} className="h-full w-full border-0 bg-white" title="이력서 PDF 미리보기" />
                  ) : canPreview && isImage(data, previewBlob) ? (
                    <div className="flex h-full items-start justify-center overflow-auto p-5">
                      <img
                        src={previewUrl}
                        alt={data.original_filename}
                        className="max-h-none max-w-full rounded-sm bg-white shadow-sm"
                      />
                    </div>
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
                      <Icon name="file" size={30} className="text-m-subtle" />
                      <p className="text-[13px] font-semibold text-m-text">
                        {isPreviewError ? '미리보기를 불러오지 못했습니다.' : '미리보기를 지원하지 않는 파일입니다.'}
                      </p>
                      <p className="text-[12px] text-m-muted">다운로드해서 원본 이력서를 확인해 주세요.</p>
                    </div>
                  )}
                </div>
              </div>

              <aside className="space-y-3">
                <div className="rounded-xl border border-m-border bg-m-surface p-4">
                  <p className="text-[13px] font-semibold text-m-text">{data.resume_title}</p>
                  <div className="mt-3 space-y-1 text-[12px] text-m-muted">
                    <p>지원일 {dateStr(data.applied_at)}</p>
                    <p>열람일 {data.viewed_at ? dateStr(data.viewed_at) : '방금'}</p>
                  </div>
                </div>
                <MatchScorePanel data={data} />
                <ParsedResumeSummary data={data} />
              </aside>
            </div>
          )}
        </div>

        {data && isInterviewFormOpen && (
          <form
            onSubmit={handleInterviewSubmit}
            className="border-t border-m-border bg-m-surface px-5 py-4"
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-[14px] font-bold text-m-text">면접 안내 메일</h3>
                <p className="mt-0.5 text-[12px] text-m-muted">
                  입력한 일정과 장소가 지원자에게 메일로 발송됩니다.
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsInterviewFormOpen(false);
                  setFormError(null);
                }}
                disabled={interviewMutation.isPending}
              >
                접기
              </Button>
            </div>
            <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
              <label className="block">
                <span className="mb-1 block text-[12px] font-semibold text-m-muted">면접 날짜/시간</span>
                <Input
                  type="datetime-local"
                  value={interviewAt}
                  min={minInterviewAt}
                  onChange={(event) => setInterviewAt(event.target.value)}
                  disabled={interviewMutation.isPending}
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-[12px] font-semibold text-m-muted">장소 주소</span>
                <Input
                  value={locationAddress}
                  onChange={(event) => setLocationAddress(event.target.value)}
                  placeholder="회사 등록 주소 또는 면접 장소 주소"
                  disabled={interviewMutation.isPending}
                  required
                />
              </label>
              <label className="block md:col-span-2">
                <span className="mb-1 block text-[12px] font-semibold text-m-muted">선택 메시지</span>
                <textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  maxLength={2000}
                  rows={3}
                  disabled={interviewMutation.isPending}
                  placeholder="준비물, 도착 안내 등 추가로 전달할 내용을 입력하세요."
                  className="w-full resize-none rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[14px] text-m-text transition-colors placeholder:text-m-subtle focus:outline-none focus:ring-1 focus:ring-m-primary disabled:cursor-not-allowed disabled:opacity-60"
                />
              </label>
            </div>
            {formError && <Alert variant="danger" className="mt-3">{formError}</Alert>}
            <div className="mt-3 flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsInterviewFormOpen(false);
                  setFormError(null);
                }}
                disabled={interviewMutation.isPending}
              >
                취소
              </Button>
              <Button type="submit" size="sm" disabled={interviewMutation.isPending}>
                <Icon name="mail" size={15} />
                {interviewMutation.isPending ? '발송 중' : '보내기'}
              </Button>
            </div>
          </form>
        )}

        <div className="flex items-center justify-between gap-3 border-t border-m-border p-4">
          <p className="truncate text-[11px] text-m-subtle">받는사람: {data?.applicant_email ?? '-'}</p>
          <div className="flex shrink-0 gap-2">
            <Button
              onClick={onClose}
              variant="outline"
              size="sm"
            >
              닫기
            </Button>
            {!isInterviewFormOpen && (
              <Button
                onClick={handleInterviewEmail}
                size="sm"
                disabled={!data || interviewMutation.isPending}
              >
                <Icon name="mail" size={15} />
                면접 이메일 보내기
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MatchScorePanel({ data }: { data: CompanyApplicantResume }) {
  const match = data.match_score;
  if (!match) {
    return (
      <div className="rounded-xl border border-m-border bg-m-surface p-4 text-[12px] text-m-subtle">
        매칭 점수 산출을 기다리고 있습니다.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-m-border bg-m-surface p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-[13px] font-semibold text-m-text">매칭 점수</h3>
          <p className="mt-1 text-[12px] leading-5 text-m-muted">{match.summary}</p>
        </div>
        <span
          className={`shrink-0 rounded-lg px-2.5 py-1 text-[12px] font-bold ${getMatchScoreClass(match.grade)}`}
          title={`${match.model} ${match.algorithm_version}`}
        >
          {match.grade} · {match.score}
        </span>
      </div>

      {match.matched_skills.length > 0 && (
        <div className="mb-3">
          <p className="mb-1.5 text-[11px] font-semibold text-m-subtle">일치 기술</p>
          <div className="flex flex-wrap gap-1.5">
            {match.matched_skills.slice(0, 8).map((skill) => (
              <span key={skill} className="rounded-md bg-m-success-soft px-2 py-0.5 text-[11px] font-medium text-m-success">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {match.missing_skills.length > 0 && (
        <div className="mb-3">
          <p className="mb-1.5 text-[11px] font-semibold text-m-subtle">보완 키워드</p>
          <div className="flex flex-wrap gap-1.5">
            {match.missing_skills.slice(0, 8).map((skill) => (
              <span key={skill} className="rounded-md bg-m-warn-soft px-2 py-0.5 text-[11px] font-medium text-m-warn">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        {match.strengths.slice(0, 2).map((item) => (
          <p key={item} className="rounded-lg bg-m-surface-alt p-2 text-[11px] leading-5 text-m-muted">
            {item}
          </p>
        ))}
        {match.gaps.slice(0, 2).map((item) => (
          <p key={item} className="rounded-lg bg-m-surface-alt p-2 text-[11px] leading-5 text-m-muted">
            {item}
          </p>
        ))}
      </div>
    </div>
  );
}

function ParsedResumeSummary({ data }: { data: CompanyApplicantResume }) {
  const skills = data.parsed_data?.skills ?? [];
  const projects = data.structured_projects ?? [];

  if (skills.length === 0 && projects.length === 0) {
    return (
      <div className="rounded-xl border border-m-border bg-m-surface p-4 text-[12px] text-m-subtle">
        원본 파일 중심으로 확인할 수 있습니다.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-m-border bg-m-surface p-4">
      <h3 className="mb-3 text-[13px] font-semibold text-m-text">요약 정보</h3>
      {skills.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-[11px] font-semibold text-m-subtle">보유 기술</p>
          <div className="flex flex-wrap gap-1.5">
            {skills.slice(0, 12).map((skill) => (
              <span key={skill} className="rounded-md bg-m-primary-soft px-2 py-0.5 text-[11px] font-medium text-m-primary">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
      {projects.length > 0 && (
        <div>
          <p className="mb-2 text-[11px] font-semibold text-m-subtle">프로젝트</p>
          <div className="space-y-2">
            {projects.slice(0, 3).map((project) => (
              <div key={project.project_id} className="rounded-lg bg-m-surface-alt p-3">
                <p className="truncate text-[12px] font-semibold text-m-text">{project.name ?? '프로젝트'}</p>
                {project.period && <p className="mt-0.5 text-[11px] text-m-subtle">{project.period}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
