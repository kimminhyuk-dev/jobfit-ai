'use client';

import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Icon from '../../components/ui/Icon';
import { resumesApi, type UploadResumeParams } from '../../api/resumes';
import type { ApiError, Resume } from '../../api/types';

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`;
  return `${(size / 1024 / 1024).toFixed(1)}MB`;
}

function statusLabel(status: Resume['parse_status']): string {
  if (status === 'COMPLETED') return '파싱 완료';
  if (status === 'FAILED') return '파싱 실패';
  return '대기 중';
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
      queryClient.setQueryData(['resume', resume.resume_id], resume);
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
    onError: (err: ApiError) => {
      setError(err.message || '이력서 업로드에 실패했습니다.');
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

  function upload(file: File | undefined) {
    if (!file) return;
    setError(null);
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
            PDF, DOCX, TXT 파일을 저장하고 서버에서 기본 파싱 결과를 관리합니다.
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
                  <p className="text-[11px] text-m-subtle mb-1">추출 길이</p>
                  <p className="text-[13px] font-semibold text-m-text">
                    {activeResume.parsed_data?.text_length ?? 0}자
                  </p>
                </div>
              </div>

              {activeResume.parse_error && (
                <div className="mb-5 rounded-xl border border-m-warn bg-m-warn-soft p-3 text-[13px] text-m-warn">
                  {activeResume.parse_error}
                </div>
              )}

              <div className="mb-5">
                <h3 className="text-[14px] font-semibold text-m-text mb-3">기본 파싱 결과</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[13px]">
                  <ParsedBlock label="이메일" items={activeResume.parsed_data?.emails ?? []} />
                  <ParsedBlock label="전화번호" items={activeResume.parsed_data?.phones ?? []} />
                  <ParsedBlock label="링크" items={activeResume.parsed_data?.urls ?? []} />
                  <ParsedBlock label="기술 키워드" items={activeResume.parsed_data?.skills ?? []} />
                </div>
              </div>

              <div>
                <h3 className="text-[14px] font-semibold text-m-text mb-3">추출 텍스트</h3>
                <div className="max-h-[240px] overflow-auto scrollbar-thin rounded-xl bg-m-surface-alt p-4 text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">
                  {activeResume.raw_text || '추출된 텍스트가 없습니다.'}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-[14px] text-m-subtle">
              이력서를 등록하면 파싱 결과가 표시됩니다.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ParsedBlock({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="rounded-xl bg-m-surface-alt p-3 min-h-[86px]">
      <p className="text-[11px] text-m-subtle mb-2">{label}</p>
      {items.length === 0 ? (
        <p className="text-[12px] text-m-subtle">없음</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item) => (
            <span key={item} className="px-2 py-1 rounded-full bg-white border border-m-border text-[11px] text-m-muted">
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
