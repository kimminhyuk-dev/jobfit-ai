'use client';

import { useState } from 'react';
import type { Resume, ResumeParsedData, ResumeUpdatePayload } from '../../api/types';

interface ResumeParsedDataEditorProps {
  resume: Resume;
  isSaving?: boolean;
  onSave: (payload: ResumeUpdatePayload) => void;
}

interface ParsedFormState {
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
  projects: string;
  certifications: string;
  awards: string;
  languages: string;
  coverLetter: string;
  coverLetterSections: string;
}

const EMPTY_PARSED_DATA: ResumeParsedData = {
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

function toLines(items: string[] | undefined): string {
  return (items ?? []).join('\n');
}

function toBlocks(items: string[] | undefined): string {
  return (items ?? []).join('\n\n');
}

function fromLines(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}

function fromBlocks(value: string): string[] {
  const blockItems = value
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
  return blockItems.length > 1 ? blockItems : fromLines(value);
}

function sectionsToText(sections: Record<string, string> | undefined): string {
  return normalizeCoverLetterSections(undefined, sections)
    .map(([title, content]) => `${title}\n${content}`)
    .join('\n\n');
}

function textToSections(value: string): Record<string, string> {
  const normalized = normalizeCoverLetterSections(value, undefined);
  if (normalized.length > 0) {
    return Object.fromEntries(normalized);
  }

  const result: Record<string, string> = {};
  value
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .forEach((block) => {
      const [title, ...contentLines] = block.split('\n');
      const key = title.trim();
      const content = contentLines.join('\n').trim();
      if (key && content) {
        result[key] = content;
      }
    });
  return result;
}

const PROJECT_ITEM_START_RE = /^(?:프로젝트\s*)?(?:\d+\s*차|[0-9]+[.)]|[①-⑳])(?:\s|[:：.-]|$)|^프로젝트\s*\d+/i;

const COVER_LETTER_HEADINGS = [
  '지원동기',
  '지원 동기',
  '성장과정',
  '성장 과정',
  '성격의 장단점',
  '성격 장단점',
  '장점 및 단점',
  '입사 후 포부',
  '입사후포부',
  '입사 후 계획',
  '기술역량 및 프로젝트',
  '기술 역량 및 프로젝트',
  '프로젝트 후기',
  '직무역량',
  '직무 역량',
  '보유역량',
  '가치관',
  '생활신조',
  '기타사항',
];

function normalizeHeading(text: string): string {
  return text.replace(/[^0-9A-Za-z가-힣]/g, '').toLowerCase();
}

function matchCoverLetterHeading(line: string): string | null {
  const cleaned = line
    .trim()
    .replace(/^\d{1,2}\s*[.)、:：-]\s*/, '')
    .replace(/^[가-하]\s*[.)、:：-]\s*/, '');
  const compact = normalizeHeading(cleaned);
  return COVER_LETTER_HEADINGS.find((heading) => normalizeHeading(heading) === compact) ?? null;
}

function splitProjectItems(items: string[] | undefined): string[] {
  const result: string[] = [];
  (items ?? []).forEach((item) => {
    const groups: string[] = [];
    let current: string[] = [];
    item.split('\n').forEach((line) => {
      const stripped = line.trim();
      if (!stripped) {
        if (current.length > 0) {
          groups.push(current.join('\n'));
          current = [];
        }
        return;
      }
      if (current.length > 0 && PROJECT_ITEM_START_RE.test(stripped)) {
        groups.push(current.join('\n'));
        current = [stripped];
        return;
      }
      current.push(stripped);
    });
    if (current.length > 0) {
      groups.push(current.join('\n'));
    }
    result.push(...(groups.length > 0 ? groups : [item]));
  });
  return result.map((item) => item.trim()).filter(Boolean);
}

function splitProjectText(value: string): string[] {
  return splitProjectItems(fromBlocks(value));
}

function collectProjectItems(parsed: ResumeParsedData): string[] {
  const candidates = [
    ...splitProjectItems(parsed.projects),
    ...splitProjectItems(parsed.sections?.projects ? [parsed.sections.projects] : []),
  ];
  return dedupeItems(candidates);
}

function dedupeItems(items: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  items.forEach((item) => {
    const key = normalizeHeading(item);
    if (!key || seen.has(key)) return;
    seen.add(key);
    result.push(item);
  });
  return result;
}

function normalizeCoverLetterSections(
  coverLetter?: string | null,
  sections?: Record<string, string>,
): [string, string][] {
  const entries = Object.entries(sections ?? {}).filter(([, content]) => content.trim());
  const sourceBlocks = entries.length > 0
    ? entries.map(([title, content]) => `${title}\n${content}`)
    : [coverLetter ?? ''];
  const result: [string, string][] = [];

  sourceBlocks.forEach((block, blockIndex) => {
    let currentTitle: string | null = entries[blockIndex]?.[0] ?? null;
    let currentLines: string[] = [];

    block.split('\n').forEach((line, lineIndex) => {
      const stripped = line.trim();
      if (!stripped) return;
      const heading = matchCoverLetterHeading(stripped);
      if (heading || (lineIndex === 0 && entries[blockIndex]?.[0] === stripped)) {
        if (currentTitle && currentLines.length > 0) {
          result.push([currentTitle, currentLines.join('\n').trim()]);
        }
        currentTitle = heading ?? stripped;
        currentLines = [];
        return;
      }
      if (currentTitle) {
        currentLines.push(stripped);
      }
    });

    if (currentTitle && currentLines.length > 0) {
      result.push([currentTitle, currentLines.join('\n').trim()]);
    }
  });

  if (result.length > 0) return result;
  if (coverLetter?.trim()) return [['자기소개서', coverLetter.trim()]];
  return entries;
}

function upsertSection(
  sections: Record<string, string> | undefined,
  key: string,
  value: string,
): Record<string, string> {
  const next = { ...(sections ?? {}) };
  const trimmed = value.trim();
  if (trimmed) {
    next[key] = trimmed;
  } else {
    delete next[key];
  }
  return next;
}

function createFormState(resume: Resume): ParsedFormState {
  const parsed = resume.parsed_data ?? EMPTY_PARSED_DATA;
  const projectItems = collectProjectItems(parsed);
  return {
    title: resume.title,
    rawText: resume.raw_text ?? '',
    name: parsed.profile?.name ?? '',
    birthDate: parsed.profile?.birth_date ?? '',
    address: parsed.profile?.address ?? '',
    emails: toLines(parsed.emails),
    phones: toLines(parsed.phones),
    urls: toLines(parsed.urls),
    skills: toLines(parsed.skills),
    education: toLines(parsed.education),
    training: toLines(parsed.training),
    experiences: toLines(parsed.experiences),
    projects: toBlocks(projectItems),
    certifications: toLines(parsed.certifications),
    awards: toLines(parsed.awards),
    languages: toLines(parsed.languages),
    coverLetter: parsed.cover_letter ?? '',
    coverLetterSections: sectionsToText(parsed.cover_letter_sections),
  };
}

export default function ResumeParsedDataEditor({
  resume,
  isSaving = false,
  onSave,
}: ResumeParsedDataEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<ParsedFormState>(() => createFormState(resume));

  const parsed = resume.parsed_data ?? EMPTY_PARSED_DATA;

  function updateField<K extends keyof ParsedFormState>(key: K, value: ParsedFormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function save() {
    const existing = resume.parsed_data ?? EMPTY_PARSED_DATA;
    const emails = fromLines(form.emails);
    const phones = fromLines(form.phones);
    const urls = fromLines(form.urls);
    const projectBlocks = splitProjectText(form.projects);
    const coverLetterSections = textToSections(form.coverLetterSections);
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
      sections: upsertSection(existing.sections, 'projects', form.projects),
      education: fromLines(form.education),
      training: fromLines(form.training),
      experiences: fromLines(form.experiences),
      projects: projectBlocks,
      certifications: fromLines(form.certifications),
      awards: fromLines(form.awards),
      languages: fromLines(form.languages),
      cover_letter: form.coverLetter.trim() || null,
      cover_letter_sections: coverLetterSections,
      text_length: form.rawText.replace(/\s+/g, ' ').trim().length,
    };
    onSave({
      title: form.title.trim() || resume.title,
      raw_text: form.rawText,
      parsed_data: parsedData,
    });
  }

  if (isEditing) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-[14px] font-semibold text-m-text">파싱 정보 수정</h3>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setForm(createFormState(resume));
                setIsEditing(false);
              }}
              className="h-8 px-3 rounded-lg border border-m-border text-[12px] font-medium text-m-muted hover:bg-m-surface-alt"
            >
              취소
            </button>
            <button
              type="button"
              onClick={save}
              disabled={isSaving}
              className="h-8 px-3 rounded-lg bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover disabled:opacity-50"
            >
              저장
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <InputField label="이력서 제목" value={form.title} onChange={(value) => updateField('title', value)} />
          <InputField label="이름" value={form.name} onChange={(value) => updateField('name', value)} />
          <InputField label="생년월일" value={form.birthDate} onChange={(value) => updateField('birthDate', value)} />
        </div>
        <InputField label="주소" value={form.address} onChange={(value) => updateField('address', value)} />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <TextAreaField label="이메일" value={form.emails} onChange={(value) => updateField('emails', value)} />
          <TextAreaField label="연락처" value={form.phones} onChange={(value) => updateField('phones', value)} />
          <TextAreaField label="링크" value={form.urls} onChange={(value) => updateField('urls', value)} />
          <TextAreaField label="기술 키워드" value={form.skills} onChange={(value) => updateField('skills', value)} />
          <TextAreaField label="학력" value={form.education} onChange={(value) => updateField('education', value)} />
          <TextAreaField label="교육/훈련" value={form.training} onChange={(value) => updateField('training', value)} />
          <TextAreaField label="경력사항" value={form.experiences} onChange={(value) => updateField('experiences', value)} />
          <TextAreaField label="프로젝트" value={form.projects} onChange={(value) => updateField('projects', value)} />
          <TextAreaField label="자격증" value={form.certifications} onChange={(value) => updateField('certifications', value)} />
          <TextAreaField label="수상" value={form.awards} onChange={(value) => updateField('awards', value)} />
          <TextAreaField label="어학" value={form.languages} onChange={(value) => updateField('languages', value)} />
          <TextAreaField
            label="자기소개서 목차"
            value={form.coverLetterSections}
            onChange={(value) => updateField('coverLetterSections', value)}
            rows={8}
          />
        </div>
        <TextAreaField label="자기소개서 전체" value={form.coverLetter} onChange={(value) => updateField('coverLetter', value)} rows={8} />
        <TextAreaField label="추출 원문" value={form.rawText} onChange={(value) => updateField('rawText', value)} rows={10} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <h3 className="text-[14px] font-semibold text-m-text">파싱 데이터</h3>
        <button
          type="button"
          onClick={() => setIsEditing(true)}
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
        <ProjectBlock items={collectProjectItems(parsed)} />
        <InfoBlock label="자격증" items={parsed.certifications} />
        <InfoBlock label="수상" items={parsed.awards} />
        <InfoBlock label="어학" items={parsed.languages} />
      </div>

      <CoverLetterBlock
        coverLetter={parsed.cover_letter}
        sections={parsed.cover_letter_sections}
      />

      <div className="mt-4">
        <p className="text-[12px] font-semibold text-m-text mb-2">추출 원문</p>
        <div className="max-h-[260px] overflow-auto rounded-xl bg-m-surface-alt p-4 text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">
          {resume.raw_text || '추출된 텍스트가 없습니다.'}
        </div>
      </div>
    </div>
  );
}

function profileItems(parsed: ResumeParsedData): string[] {
  return [
    parsed.profile?.name && `이름: ${parsed.profile.name}`,
    parsed.profile?.birth_date && `생년월일: ${parsed.profile.birth_date}`,
    parsed.profile?.address && `주소: ${parsed.profile.address}`,
  ].filter(Boolean) as string[];
}

function InputField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-m-subtle mb-1.5">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
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
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold text-m-subtle mb-1.5">{label}</span>
      <textarea
        value={value}
        rows={rows}
        onChange={(event) => onChange(event.target.value)}
        className="w-full resize-y px-3 py-2 rounded-lg border border-m-border bg-m-surface-alt text-[12px] leading-relaxed text-m-text focus:outline-none focus:border-m-primary"
      />
    </label>
  );
}

function InfoBlock({
  label,
  items,
  chip = false,
}: {
  label: string;
  items: string[] | undefined;
  chip?: boolean;
}) {
  const values = items ?? [];
  return (
    <div className="rounded-xl bg-m-surface-alt p-3 min-h-[86px]">
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
          {values.map((item, index) => (
            <li key={`${label}-${index}`} className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ProjectBlock({ items }: { items: string[] | undefined }) {
  const values = items ?? [];
  return (
    <div className="sm:col-span-2 rounded-xl bg-m-surface-alt p-3">
      <p className="text-[11px] text-m-subtle mb-3">프로젝트</p>
      {values.length === 0 ? (
        <p className="text-[12px] text-m-subtle">없음</p>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {values.map((item, index) => (
            <div key={`project-${index}`} className="rounded-lg border border-m-border bg-white p-3">
              <div className="mb-2 flex items-center gap-2">
                <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-m-primary text-[11px] font-semibold text-white">
                  {index + 1}
                </span>
                <p className="text-[12px] font-semibold text-m-text">
                  {extractFirstLine(item) || `프로젝트 ${index + 1}`}
                </p>
              </div>
              {dropFirstLine(item) && (
                <p className="whitespace-pre-wrap text-[12px] leading-relaxed text-m-muted">
                  {dropFirstLine(item)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function extractFirstLine(text: string): string {
  return text.split('\n').find((line) => line.trim())?.trim() ?? '';
}

function dropFirstLine(text: string): string {
  const lines = text.split('\n');
  return lines.slice(1).join('\n').trim();
}

function CoverLetterBlock({
  coverLetter,
  sections,
}: {
  coverLetter?: string | null;
  sections?: Record<string, string>;
}) {
  const entries = normalizeCoverLetterSections(coverLetter, sections);
  if (!coverLetter && entries.length === 0) return null;
  return (
    <div className="mt-4 rounded-xl bg-m-surface-alt p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[11px] text-m-subtle">자기소개서</p>
        {entries.length > 0 && (
          <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-m-muted">
            {entries.length}개 목차
          </span>
        )}
      </div>
      {entries.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {entries.map(([title, content]) => (
            <div key={title} className="rounded-lg border border-m-border bg-white p-3">
              <p className="mb-2 text-[12px] font-semibold text-m-text">{title}</p>
              <p className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">{content}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[12px] leading-relaxed text-m-muted whitespace-pre-wrap">{coverLetter}</p>
      )}
    </div>
  );
}
