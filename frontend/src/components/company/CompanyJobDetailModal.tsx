'use client';

import Icon from '../ui/Icon';
import type { CompanyJob } from '../../api/types';

function dateStr(value: string | null): string {
  if (!value) return '-';
  const d = new Date(value);
  return isNaN(d.getTime()) ? '-' : d.toLocaleDateString('ko-KR');
}

function Row({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex gap-3 border-b border-m-border py-2.5 last:border-0">
      <span className="w-24 shrink-0 text-[12px] text-m-subtle">{label}</span>
      <span className="text-[13px] text-m-text">{value}</span>
    </div>
  );
}

export default function CompanyJobDetailModal({
  job,
  onClose,
  onEdit,
  onDelete,
  onToggleHidden,
  deleting,
  togglingHidden,
}: {
  job: CompanyJob;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onToggleHidden: () => void;
  deleting: boolean;
  togglingHidden: boolean;
}) {
  const statusLabel = job.status === 'HIDDEN' ? '숨김' : job.status === 'CLOSED' ? '마감' : '모집중';
  const statusCls =
    job.status === 'HIDDEN'
      ? 'bg-m-warn-soft text-m-warn'
      : job.status === 'CLOSED'
        ? 'bg-m-surface-alt text-m-subtle'
        : 'bg-m-success-soft text-m-success';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[88vh] w-full max-w-2xl flex-col rounded-2xl bg-m-surface shadow-xl">
        <div className="flex items-start justify-between gap-3 border-b border-m-border p-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="truncate text-[16px] font-bold text-m-text">{job.title}</h2>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${statusCls}`}>
                {statusLabel}
              </span>
              {!job.editable && (
                <span className="shrink-0 rounded-full bg-m-surface-alt px-2 py-0.5 text-[11px] font-semibold text-m-subtle">
                  외부 수집
                </span>
              )}
            </div>
            <p className="mt-1 truncate text-[12px] text-m-muted">
              {job.company_name ?? '우리 회사'} · 지원자 {job.applicant_count}명
            </p>
          </div>
          <button onClick={onClose} className="shrink-0 p-1 text-m-subtle hover:text-m-muted" aria-label="닫기">
            <Icon name="x" size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-5 scrollbar-thin">
          <div className="rounded-xl border border-m-border p-4">
            <Row label="근무지역" value={job.location} />
            <Row label="고용형태" value={job.employment_type} />
            <Row label="경력" value={job.career_level} />
            <Row label="학력" value={job.education} />
            <Row label="직종" value={job.ncs_category} />
            <Row label="급여" value={job.salary_text} />
            <Row label="마감일" value={dateStr(job.deadline)} />
            <Row label="등록일" value={dateStr(job.posted_at ?? job.created_at)} />
          </div>

          <div className="mt-4">
            <h3 className="mb-2 text-[13px] font-semibold text-m-text">직무 내용</h3>
            {job.raw_content ? (
              <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-m-muted">{job.raw_content}</p>
            ) : (
              <p className="text-[13px] text-m-subtle">등록된 직무 내용이 없습니다.</p>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-m-border p-4">
          {job.editable ? (
            <div className="flex gap-2">
              <button
                onClick={onToggleHidden}
                disabled={togglingHidden}
                className="flex h-9 items-center gap-1.5 rounded-lg border border-m-border px-4 text-[13px] font-semibold text-m-muted hover:bg-m-surface-alt disabled:opacity-50 transition-colors"
              >
                <Icon name={job.status === 'HIDDEN' ? 'eye' : 'eye-off'} size={14} />
                {togglingHidden ? '처리 중...' : job.status === 'HIDDEN' ? '다시 공개' : '숨김'}
              </button>
              <button
                onClick={onDelete}
                disabled={deleting}
                className="flex h-9 items-center gap-1.5 rounded-lg border border-m-danger/40 px-4 text-[13px] font-semibold text-m-danger hover:bg-m-danger/10 disabled:opacity-50 transition-colors"
              >
                <Icon name="trash" size={14} />
                {deleting ? '삭제 중...' : '삭제'}
              </button>
            </div>
          ) : (
            <span className="text-[11px] text-m-subtle">외부 수집 공고는 수정·삭제할 수 없습니다.</span>
          )}
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="h-9 rounded-lg border border-m-border px-4 text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
            >
              닫기
            </button>
            {job.editable && (
              <button
                onClick={onEdit}
                className="h-9 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white hover:bg-m-primary-hover transition-colors"
              >
                수정
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
