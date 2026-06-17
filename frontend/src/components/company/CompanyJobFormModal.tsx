'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import Icon from '../ui/Icon';
import { showToast } from '../ui/Toast';
import { companyApi } from '../../api/company';
import type { ApiError, CompanyJob, CompanyJobPayload, CompanyJobStatus } from '../../api/types';

interface FormState {
  title: string;
  location: string;
  employment_type: string;
  career_level: string;
  education: string;
  ncs_category: string;
  salary_text: string;
  deadline: string; // YYYY-MM-DD
  raw_content: string;
  status: CompanyJobStatus;
}

function initialForm(job?: CompanyJob): FormState {
  return {
    title: job?.title ?? '',
    location: job?.location ?? '',
    employment_type: job?.employment_type ?? '',
    career_level: job?.career_level ?? '',
    education: job?.education ?? '',
    ncs_category: job?.ncs_category ?? '',
    salary_text: job?.salary_text ?? '',
    deadline: job?.deadline ? job.deadline.slice(0, 10) : '',
    raw_content: job?.raw_content ?? '',
    status: job?.status === 'HIDDEN' ? 'HIDDEN' : job?.status === 'CLOSED' ? 'CLOSED' : 'OPEN',
  };
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-[12px] font-medium text-m-muted">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-10 w-full rounded-lg border border-m-border bg-m-surface px-3 text-[13px] text-m-text focus:border-m-primary focus:outline-none focus:ring-1 focus:ring-m-primary"
      />
    </label>
  );
}

export default function CompanyJobFormModal({
  mode,
  job,
  onClose,
}: {
  mode: 'create' | 'edit';
  job?: CompanyJob;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FormState>(() => initialForm(job));
  const [error, setError] = useState('');

  type StringField = Exclude<keyof FormState, 'status'>;
  const set = (key: StringField) => (v: string) =>
    setForm((p) => ({ ...p, [key]: v }) as FormState);

  const mutation = useMutation({
    mutationFn: () => {
      const payload: CompanyJobPayload = {
        title: form.title.trim(),
        location: form.location.trim() || null,
        employment_type: form.employment_type.trim() || null,
        career_level: form.career_level.trim() || null,
        education: form.education.trim() || null,
        ncs_category: form.ncs_category.trim() || null,
        salary_text: form.salary_text.trim() || null,
        raw_content: form.raw_content.trim() || null,
        deadline: form.deadline ? `${form.deadline}T23:59:59` : null,
        status: form.status,
      };
      return mode === 'create'
        ? companyApi.createJob(payload)
        : companyApi.updateJob(job!.job_id, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', 'jobs'] });
      queryClient.invalidateQueries({ queryKey: ['company', 'dashboard'] });
      showToast(mode === 'create' ? '공고를 등록했습니다.' : '공고를 수정했습니다.', 'success');
      onClose();
    },
    onError: (e: ApiError) => setError(e.message || '저장에 실패했습니다.'),
  });

  function handleSubmit() {
    setError('');
    if (!form.title.trim()) {
      setError('공고 제목을 입력하세요.');
      return;
    }
    mutation.mutate();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col rounded-2xl bg-m-surface shadow-xl">
        <div className="flex items-center justify-between border-b border-m-border p-5">
          <h2 className="text-[16px] font-bold text-m-text">
            {mode === 'create' ? '새 공고 등록' : '공고 수정'}
          </h2>
          <button onClick={onClose} className="p-1 text-m-subtle hover:text-m-muted" aria-label="닫기">
            <Icon name="x" size={18} />
          </button>
        </div>

        <div className="flex-1 space-y-3 overflow-auto p-5 scrollbar-thin">
          <Field label="공고 제목 *" value={form.title} onChange={set('title')} placeholder="예: 프론트엔드 개발자 채용" />
          <div className="grid grid-cols-2 gap-3">
            <Field label="근무지역" value={form.location} onChange={set('location')} placeholder="예: 서울 강남구" />
            <Field label="고용형태" value={form.employment_type} onChange={set('employment_type')} placeholder="예: 정규직" />
            <Field label="경력" value={form.career_level} onChange={set('career_level')} placeholder="예: 신입 / 경력 3년" />
            <Field label="학력" value={form.education} onChange={set('education')} placeholder="예: 학력무관" />
            <Field label="직종(NCS)" value={form.ncs_category} onChange={set('ncs_category')} placeholder="예: 정보기술" />
            <Field label="급여" value={form.salary_text} onChange={set('salary_text')} placeholder="예: 면접 후 협의" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="mb-1 block text-[12px] font-medium text-m-muted">마감일</span>
              <input
                type="date"
                value={form.deadline}
                onChange={(e) => set('deadline')(e.target.value)}
                className="h-10 w-full rounded-lg border border-m-border bg-m-surface px-3 text-[13px] text-m-text focus:border-m-primary focus:outline-none focus:ring-1 focus:ring-m-primary"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-[12px] font-medium text-m-muted">모집 상태</span>
              <select
                value={form.status}
                onChange={(e) => setForm((p) => ({ ...p, status: e.target.value as CompanyJobStatus }))}
                className="h-10 w-full rounded-lg border border-m-border bg-m-surface px-3 text-[13px] text-m-text focus:border-m-primary focus:outline-none focus:ring-1 focus:ring-m-primary"
              >
                <option value="OPEN">모집중</option>
                <option value="CLOSED">마감</option>
                <option value="HIDDEN">숨김</option>
              </select>
            </label>
          </div>
          <label className="block">
            <span className="mb-1 block text-[12px] font-medium text-m-muted">직무 내용</span>
            <textarea
              value={form.raw_content}
              onChange={(e) => set('raw_content')(e.target.value)}
              rows={6}
              placeholder="담당 업무, 자격 요건, 우대 사항 등을 입력하세요."
              className="w-full rounded-lg border border-m-border bg-m-surface px-3 py-2 text-[13px] text-m-text focus:border-m-primary focus:outline-none focus:ring-1 focus:ring-m-primary"
            />
          </label>

          {error && (
            <p className="rounded-lg bg-m-danger/10 px-3 py-2 text-[12px] text-m-danger">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-m-border p-4">
          <button
            onClick={onClose}
            className="h-9 rounded-lg border border-m-border px-4 text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={mutation.isPending}
            className="h-9 rounded-lg bg-m-primary px-4 text-[13px] font-semibold text-white hover:bg-m-primary-hover disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? '저장 중...' : mode === 'create' ? '등록' : '수정 저장'}
          </button>
        </div>
      </div>
    </div>
  );
}
