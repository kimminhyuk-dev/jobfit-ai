'use client';

import { useState } from 'react';
import type {
  Resume,
  ResumeParsedData,
  ResumeProjectData,
  ResumeProjectResponse,
  ResumeCoverLetterSectionResponse,
  ResumeUpdatePayload,
} from '../../api/types';

interface ResumeParsedDataEditorProps {
  resume: Resume;
  isSaving?: boolean;
  onSave: (payload: ResumeUpdatePayload) => void;
}

// ─── 유틸 ────────────────────────────────────────────────────────────────── //

function toLines(items: string[] | undefined): string {
  return (items ?? []).join('\n');
}

function fromLines(value: string): string[] {
  return value.split('\n').map((s) => s.trim()).filter(Boolean);
}

/** 구버전 string[] 또는 신버전 object[] 프로젝트를 ResumeProjectData[] 로 정규화 */
function normalizeProjects(raw: (ResumeProjectData | string)[] | ResumeProjectResponse[] | undefined): ResumeProjectData[] {
  if (!raw || raw.length === 0) return [];
  return raw.map((item) => {
    if (typeof item === 'string') {
      return { raw_text: item, name: null, period: null, role: null, description: null, review: null, tech_stack: [] };
    }
    return item as ResumeProjectData;
  });
}

/** cover_letter_sections dict → [{title,content}] */
function sectionsFromDict(dict: Record<string, string> | undefined): { title: string; content: string }[] {
  return Object.entries(dict ?? {})
    .filter(([, c]) => c.trim())
    .map(([title, content]) => ({ title, content }));
}

/** ResumeCoverLetterSectionResponse[] → [{title,content}] */
function sectionsFromRows(rows: ResumeCoverLetterSectionResponse[] | undefined): { title: string; content: string }[] {
  return (rows ?? []).map((r) => ({ title: r.title, content: r.content }));
}

const EMPTY_PARSED: ResumeParsedData = {
  profile: {},
  emails: [],
  phones: [],
  urls: [],
  skills: [],
  sections: {},
  education: [],
  training: [],
  experiences: [],
  projects: [],
  certifications: [],
  cover_letter: null,
  cover_letter_sections: {},
  awards: [],
  languages: [],
  highlights: {},
  text_length: 0,
};

// ─── 폼 상태 ────────────────────────────────────────────────────────────── //

interface EditFormState {
  title: string;
  rawText: string;
  name: string;
  birthDate: string;
  address: string;
  emails: string;
  phones: string;
  urls: string;
  skills: string;
  education: string;
  training: string;
  experiences: string;
  certifications: string;
  awards: string;
  languages: string;
  coverLetter: string;
  projects: ResumeProjectData[];
  coverLetterSections: { title: string; content: string }[];
}

function createFormState(resume: Resume): EditFormState {
  const p = resume.parsed_data ?? EMPTY_PARSED;

  // 구조화 테이블 우선, 없으면 parsed_data에서 추출
  const projects: ResumeProjectData[] =
    resume.structured_projects && resume.structured_projects.length > 0
      ? normalizeProjects(resume.structured_projects)
      : normalizeProjects(p.projects as (ResumeProjectData | string)[] | undefined);

  const clSections: { title: string; content: string }[] =
    resume.structured_cover_letter_sections && resume.structured_cover_letter_sections.length > 0
      ? sectionsFromRows(resume.structured_cover_letter_sections)
      : sectionsFromDict(p.cover_letter_sections);

  return {
    title: resume.title,
    rawText: resume.raw_text ?? '',
    name: p.profile?.name ?? '',
    birthDate: p.profile?.birth_date ?? '',
    address: p.profile?.address ?? '',
    emails: toLines(p.emails),
    phones: toLines(p.phones),
    urls: toLines(p.urls),
    skills: toLines(p.skills),
    education: toLines(p.education),
    training: toLines(p.training),
    experiences: toLines(p.experiences),
    certifications: toLines(p.certifications),
    awards: toLines(p.awards),
    languages: toLines(p.languages),
    coverLetter: p.cover_letter ?? '',
    projects,
    coverLetterSections: clSections,
  };
}

// ─── 메인 컴포넌트 ──────────────────────────────────────────────────────── //

export default function ResumeParsedDataEditor({ resume, isSaving = false, onSave }: ResumeParsedDataEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<EditFormState>(() => createFormState(resume));

  const parsed = resume.parsed_data ?? EMPTY_PARSED;

  // 구조화 테이블 우선 사용 (없으면 parsed_data 폴백)
  const displayProjects: ResumeProjectData[] =
    resume.structured_projects && resume.structured_projects.length > 0
      ? normalizeProjects(resume.structured_projects)
      : normalizeProjects(parsed.projects as (ResumeProjectData | string)[] | undefined);

  const displaySections: { title: string; content: string }[] =
    resume.structured_cover_letter_sections && resume.structured_cover_letter_sections.length > 0
      ? sectionsFromRows(resume.structured_cover_letter_sections)
      : sectionsFromDict(parsed.cover_letter_sections);

  function save() {
    const existing = resume.parsed_data ?? EMPTY_PARSED;
    const emails = fromLines(form.emails);
    const phones = fromLines(form.phones);
    const urls = fromLines(form.urls);
    const parsedData: ResumeParsedData = {
      ...existing,
      profile: {
        ...existing.profile,
        name: form.name.trim() || null,
        birth_date: form.birthDate.trim() || null,
        email: emails[0] ?? null,
        phone: phones[0] ?? null,
        urls,
        address: form.address.trim() || null,
      },
      emails,
      phones,
      urls,
      skills: fromLines(form.skills),
      education: fromLines(form.education),
      training: fromLines(form.training),
      experiences: fromLines(form.experiences),
      projects: form.projects,
      certifications: fromLines(form.certifications),
      awards: fromLines(form.awards),
      languages: fromLines(form.languages),
      cover_letter: form.coverLetter.trim() || null,
      cover_letter_sections: Object.fromEntries(
        form.coverLetterSections.map((s) => [s.title, s.content]),
      ),
      text_length: form.rawText.replace(/\s+/g, ' ').trim().length,
    };
    onSave({
      title: form.title.trim() || resume.title,
      raw_text: form.rawText,
      parsed_data: parsedData,
      structured_projects: form.projects,
      structured_cover_letter_sections: form.coverLetterSections,
    });
  }

  if (isEditing) {
    return (
      <EditView
        form={form}
        isSaving={isSaving}
        onChange={setForm}
        onSave={save}
        onCancel={() => { setForm(createFormState(resume)); setIsEditing(false); }}
      />
    );
  }

  return (
    <ReadView
      parsed={parsed}
      projects={displayProjects}
      coverLetterSections={displaySections}
      rawText={resume.raw_text}
      onEdit={() => setIsEditing(true)}
    />
  );
}

// ─── 읽기 뷰 ────────────────────────────────────────────────────────────── //

function ReadView({
  parsed,
  projects,
  coverLetterSections,
  rawText,
  onEdit,
}: {
  parsed: ResumeParsedData;
  projects: ResumeProjectData[];
  coverLetterSections: { title: string; content: string }[];
  rawText?: string | null;
  onEdit: () => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <h3 className="text-[14px] font-semibold text-m-text">파싱 데이터</h3>
        <button
          type="button"
          onClick={onEdit}
          className="h-8 px-3 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt"
        >
          수정
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <InfoBlock label="프로필" items={profileItems(parsed)} />
        <InfoBlock label="이메일" items={parsed.emails} chip />
        <InfoBlock label="연락처" items={parsed.phones} chip />
        <InfoBlock label="링크" items={parsed.urls} />
        <InfoBlock label="기술 키워드" items={parsed.skills} chip />
        <InfoBlock label="학력" items={parsed.education} />
        <InfoBlock label="교육/훈련" items={parsed.training} />
        <InfoBlock label="경력사항" items={parsed.experiences} />
        <InfoBlock label="자격증" items={parsed.certifications} />
        <InfoBlock label="수상" items={parsed.awards} />
        <InfoBlock label="어학" items={parsed.languages} />
      </div>

      {/* 프로젝트 구조화 카드 */}
      <StructuredProjectsBlock projects={projects} />

      {/* 자기소개서 목차 구조화 카드 */}
      <StructuredCoverLetterBlock sections={coverLetterSections} fallbackText={parsed.cover_letter} />

      <div className="mt-4">
        <p className="text-[12px] font-semibold text-m-text mb-2">추출 원문</p>
        <div className="max-h-65 overflow-auto rounded-xl bg-m-surface-alt p-4 text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">
          {rawText || '추출된 텍스트가 없습니다.'}
        </div>
      </div>
    </div>
  );
}

// ─── 수정 뷰 ────────────────────────────────────────────────────────────── //

function EditView({
  form,
  isSaving,
  onChange,
  onSave,
  onCancel,
}: {
  form: EditFormState;
  isSaving: boolean;
  onChange: (f: EditFormState) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  function set<K extends keyof EditFormState>(key: K, value: EditFormState[K]) {
    onChange({ ...form, [key]: value });
  }

  function updateProject(idx: number, field: keyof ResumeProjectData, value: string | string[]) {
    const next = [...form.projects];
    next[idx] = { ...next[idx], [field]: value };
    set('projects', next);
  }

  function addProject() {
    set('projects', [
      ...form.projects,
      { name: '', period: '', role: '', description: '', review: '', tech_stack: [], raw_text: '' },
    ]);
  }

  function removeProject(idx: number) {
    set('projects', form.projects.filter((_, i) => i !== idx));
  }

  function updateSection(idx: number, field: 'title' | 'content', value: string) {
    const next = [...form.coverLetterSections];
    next[idx] = { ...next[idx], [field]: value };
    set('coverLetterSections', next);
  }

  function addSection() {
    set('coverLetterSections', [...form.coverLetterSections, { title: '', content: '' }]);
  }

  function removeSection(idx: number) {
    set('coverLetterSections', form.coverLetterSections.filter((_, i) => i !== idx));
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[14px] font-semibold text-m-text">파싱 정보 수정</h3>
        <div className="flex gap-2">
          <button type="button" onClick={onCancel}
            className="h-8 px-3 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt">
            취소
          </button>
          <button type="button" onClick={onSave} disabled={isSaving}
            className="h-8 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover disabled:opacity-50">
            저장
          </button>
        </div>
      </div>

      {/* 기본 정보 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <InputField label="이력서 제목" value={form.title} onChange={(v) => set('title', v)} />
        <InputField label="이름" value={form.name} onChange={(v) => set('name', v)} />
        <InputField label="생년월일" value={form.birthDate} onChange={(v) => set('birthDate', v)} />
      </div>
      <InputField label="주소" value={form.address} onChange={(v) => set('address', v)} />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <TextAreaField label="이메일" value={form.emails} onChange={(v) => set('emails', v)} />
        <TextAreaField label="연락처" value={form.phones} onChange={(v) => set('phones', v)} />
        <TextAreaField label="링크" value={form.urls} onChange={(v) => set('urls', v)} />
        <TextAreaField label="기술 키워드" value={form.skills} onChange={(v) => set('skills', v)} />
        <TextAreaField label="학력" value={form.education} onChange={(v) => set('education', v)} />
        <TextAreaField label="교육/훈련" value={form.training} onChange={(v) => set('training', v)} />
        <TextAreaField label="경력사항" value={form.experiences} onChange={(v) => set('experiences', v)} />
        <TextAreaField label="자격증" value={form.certifications} onChange={(v) => set('certifications', v)} />
        <TextAreaField label="수상" value={form.awards} onChange={(v) => set('awards', v)} />
        <TextAreaField label="어학" value={form.languages} onChange={(v) => set('languages', v)} />
      </div>

      {/* 프로젝트 편집 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-[12px] font-semibold text-m-text">프로젝트 ({form.projects.length}개)</p>
          <button type="button" onClick={addProject}
            className="h-7 px-2 rounded-lg border border-m-border text-[11px] text-m-muted hover:bg-m-surface-alt">
            + 추가
          </button>
        </div>
        <div className="space-y-3">
          {form.projects.map((p, idx) => (
            <ProjectEditCard key={idx} index={idx} project={p} onChange={updateProject} onRemove={() => removeProject(idx)} />
          ))}
          {form.projects.length === 0 && (
            <p className="text-[12px] text-m-subtle p-3 bg-m-surface-alt rounded-xl">프로젝트가 없습니다.</p>
          )}
        </div>
      </div>

      {/* 자기소개서 목차 편집 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-[12px] font-semibold text-m-text">자기소개서 목차 ({form.coverLetterSections.length}개)</p>
          <button type="button" onClick={addSection}
            className="h-7 px-2 rounded-lg border border-m-border text-[11px] text-m-muted hover:bg-m-surface-alt">
            + 추가
          </button>
        </div>
        <div className="space-y-3">
          {form.coverLetterSections.map((s, idx) => (
            <div key={idx} className="rounded-xl border border-m-border bg-m-surface-alt p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <InputField label="소제목" value={s.title} onChange={(v) => updateSection(idx, 'title', v)} />
                <button type="button" onClick={() => removeSection(idx)}
                  className="mt-5 h-7 px-2 rounded-lg border border-m-border text-[11px] text-m-danger hover:bg-m-danger-soft shrink-0">
                  삭제
                </button>
              </div>
              <TextAreaField label="내용" value={s.content} onChange={(v) => updateSection(idx, 'content', v)} rows={4} />
            </div>
          ))}
          {form.coverLetterSections.length === 0 && (
            <p className="text-[12px] text-m-subtle p-3 bg-m-surface-alt rounded-xl">자기소개서 목차가 없습니다.</p>
          )}
        </div>
      </div>

      <TextAreaField label="자기소개서 전체 원문" value={form.coverLetter} onChange={(v) => set('coverLetter', v)} rows={6} />
      <TextAreaField label="추출 원문" value={form.rawText} onChange={(v) => set('rawText', v)} rows={10} />
    </div>
  );
}

// ─── 프로젝트 편집 카드 ───────────────────────────────────────────────── //

function ProjectEditCard({
  index,
  project,
  onChange,
  onRemove,
}: {
  index: number;
  project: ResumeProjectData;
  onChange: (idx: number, field: keyof ResumeProjectData, value: string | string[]) => void;
  onRemove: () => void;
}) {
  const techStr = (project.tech_stack ?? []).join(', ');

  return (
    <div className="rounded-xl border border-m-border bg-m-surface-alt p-3 space-y-2">
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-m-primary text-[11px] font-semibold text-white">
          {index + 1}
        </span>
        <button type="button" onClick={onRemove}
          className="h-6 px-2 rounded-lg border border-m-border text-[10px] text-m-danger hover:bg-m-danger-soft">
          삭제
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <InputField label="프로젝트명" value={project.name ?? ''} onChange={(v) => onChange(index, 'name', v)} />
        <InputField label="기간" value={project.period ?? ''} onChange={(v) => onChange(index, 'period', v)} />
      </div>
      <TextAreaField label="맡은 역할" value={project.role ?? ''} onChange={(v) => onChange(index, 'role', v)} rows={2} />
      <TextAreaField label="프로젝트 내용" value={project.description ?? ''} onChange={(v) => onChange(index, 'description', v)} rows={3} />
      <TextAreaField label="후기 / 배운 점" value={project.review ?? ''} onChange={(v) => onChange(index, 'review', v)} rows={2} />
      <InputField
        label="기술 스택 (쉼표 구분)"
        value={techStr}
        onChange={(v) => onChange(index, 'tech_stack', v.split(',').map((t) => t.trim()).filter(Boolean))}
      />
    </div>
  );
}

// ─── 구조화 프로젝트 표시 ────────────────────────────────────────────── //

function StructuredProjectsBlock({ projects }: { projects: ResumeProjectData[] }) {
  if (projects.length === 0) return null;
  return (
    <div className="mt-4 rounded-xl bg-m-surface-alt p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[11px] text-m-subtle">프로젝트</p>
        <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-m-muted">
          {projects.length}개
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {projects.map((p, idx) => (
          <div key={idx} className="rounded-lg border border-m-border bg-white p-3">
            <div className="mb-2 flex items-center gap-2">
              <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-m-primary text-[11px] font-semibold text-white">
                {idx + 1}
              </span>
              <p className="text-[12px] font-semibold text-m-text">
                {p.name || (p.raw_text?.split('\n')[0]?.trim()) || `프로젝트 ${idx + 1}`}
              </p>
              {p.period && (
                <span className="ml-auto text-[10px] text-m-muted">{p.period}</span>
              )}
            </div>

            {/* 구조화 필드 */}
            {p.role && (
              <FieldRow label="맡은 역할" value={p.role} />
            )}
            {p.description && (
              <FieldRow label="프로젝트 내용" value={p.description} />
            )}
            {p.review && (
              <FieldRow label="후기 / 배운 점" value={p.review} />
            )}
            {p.tech_stack && p.tech_stack.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {p.tech_stack.map((t) => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-m-primary-soft text-[10px] text-m-primary font-medium">
                    {t}
                  </span>
                ))}
              </div>
            )}
            {/* 구조화 필드가 없으면 raw_text 폴백 */}
            {!p.role && !p.description && !p.review && p.raw_text && (
              <p className="whitespace-pre-wrap text-[12px] leading-relaxed text-m-muted mt-1">
                {p.raw_text.split('\n').slice(1).join('\n').trim()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="mt-2">
      <p className="text-[10px] font-semibold text-m-subtle mb-0.5">{label}</p>
      <p className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">{value}</p>
    </div>
  );
}

// ─── 구조화 자기소개서 목차 표시 ─────────────────────────────────────── //

function StructuredCoverLetterBlock({
  sections,
  fallbackText,
}: {
  sections: { title: string; content: string }[];
  fallbackText?: string | null;
}) {
  if (sections.length === 0 && !fallbackText) return null;
  return (
    <div className="mt-4 rounded-xl bg-m-surface-alt p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[11px] text-m-subtle">자기소개서</p>
        {sections.length > 0 && (
          <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-m-muted">
            {sections.length}개 목차
          </span>
        )}
      </div>
      {sections.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {sections.map((s, idx) => (
            <div key={`${s.title}-${idx}`} className="rounded-lg border border-m-border bg-white p-3">
              <p className="mb-2 text-[12px] font-semibold text-m-text">{s.title}</p>
              <p className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">{s.content}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">{fallbackText}</p>
      )}
    </div>
  );
}

// ─── 공통 UI ─────────────────────────────────────────────────────────── //

function profileItems(parsed: ResumeParsedData): string[] {
  return [
    parsed.profile?.name && `이름: ${parsed.profile.name}`,
    parsed.profile?.birth_date && `생년월일: ${parsed.profile.birth_date}`,
    parsed.profile?.address && `주소: ${parsed.profile.address}`,
  ].filter(Boolean) as string[];
}

function InputField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-m-subtle mb-1.5">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-9 px-3 rounded-lg border border-m-border bg-m-surface-alt text-[12px] text-m-text focus:outline-none focus:border-m-primary"
      />
    </label>
  );
}

function TextAreaField({
  label,
  value,
  rows = 4,
  onChange,
}: {
  label: string;
  value: string;
  rows?: number;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-m-subtle mb-1.5">{label}</span>
      <textarea
        value={value}
        rows={rows}
        onChange={(e) => onChange(e.target.value)}
        className="w-full resize-y px-3 py-2 rounded-lg border border-m-border bg-m-surface-alt text-[12px] leading-relaxed text-m-text focus:outline-none focus:border-m-primary"
      />
    </label>
  );
}

function InfoBlock({ label, items, chip = false }: { label: string; items: string[] | undefined; chip?: boolean }) {
  const values = items ?? [];
  return (
    <div className="rounded-xl bg-m-surface-alt p-3 min-h-21.5">
      <p className="text-[11px] text-m-subtle mb-2">{label}</p>
      {values.length === 0 ? (
        <p className="text-[12px] text-m-subtle">없음</p>
      ) : chip ? (
        <div className="flex flex-wrap gap-1.5">
          {values.map((item) => (
            <span key={`${label}-${item}`} className="px-2 py-1 rounded-full bg-white border border-m-border text-[11px] text-m-muted">
              {item}
            </span>
          ))}
        </div>
      ) : (
        <ul className="space-y-1.5">
          {values.map((item, i) => (
            <li key={`${label}-${i}`} className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
