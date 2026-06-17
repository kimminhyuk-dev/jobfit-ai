'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Icon from '../ui/Icon';
import { showToast } from '../ui/Toast';
import { companyApi } from '../../api/company';
import type { ApplicationStatus, CompanyApplicantResume } from '../../api/types';

const STATUS_META: Record<ApplicationStatus, { label: string; cls: string }> = {
  SUBMITTED: { label: '접수', cls: 'bg-m-primary-soft text-m-primary' },
  VIEWED: { label: '이력서 열람', cls: 'bg-m-warn-soft text-m-warn' },
  ACCEPTED: { label: '합격', cls: 'bg-m-success-soft text-m-success' },
  REJECTED: { label: '불합격', cls: 'bg-m-danger-soft text-m-danger' },
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

export default function ApplicantResumeModal({
  applicationId,
  onClose,
  onViewed,
}: {
  applicationId: number;
  onClose: () => void;
  onViewed: () => void;
}) {
  const [isDownloading, setIsDownloading] = useState(false);

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

  function handleInterviewEmail() {
    showToast('면접 이메일 발송 기능은 준비 중입니다.', 'info');
  }

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
                <ParsedResumeSummary data={data} />
              </aside>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-m-border p-4">
          <p className="truncate text-[11px] text-m-subtle">받는사람: {data?.applicant_email ?? '-'}</p>
          <div className="flex shrink-0 gap-2">
            <button
              onClick={onClose}
              className="h-9 rounded-lg border border-m-border px-4 text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
            >
              닫기
            </button>
            <button
              onClick={handleInterviewEmail}
              className="flex h-9 items-center gap-1.5 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white hover:bg-m-primary-hover transition-colors"
            >
              <Icon name="mail" size={15} />
              면접 이메일 보내기
            </button>
          </div>
        </div>
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
