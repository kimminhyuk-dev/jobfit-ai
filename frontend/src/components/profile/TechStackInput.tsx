'use client';

import { useState } from 'react';
import Icon from '../ui/Icon';

const MAX_ITEM_LEN = 30;
const MAX_COUNT = 50;
// 백엔드 정규식과 동일: 영문/숫자/한글/+ # . / - 공백
const ALLOWED = /^[\w가-힣+#./\- ]+$/;

export default function TechStackInput({
  value,
  onChange,
}: {
  value: string[];
  onChange: (next: string[]) => void;
}) {
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');

  function addToken(raw: string) {
    const token = raw.trim();
    if (!token) return;
    if (token.length > MAX_ITEM_LEN) {
      setError(`항목은 ${MAX_ITEM_LEN}자 이하여야 합니다.`);
      return;
    }
    if (!ALLOWED.test(token)) {
      setError('사용할 수 없는 문자가 있습니다.');
      return;
    }
    if (value.some((t) => t.toLowerCase() === token.toLowerCase())) {
      setError('이미 추가된 기술입니다.');
      setDraft('');
      return;
    }
    if (value.length >= MAX_COUNT) {
      setError(`최대 ${MAX_COUNT}개까지 추가할 수 있습니다.`);
      return;
    }
    setError('');
    onChange([...value, token]);
    setDraft('');
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addToken(draft);
    } else if (e.key === 'Backspace' && !draft && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[12px] font-medium text-m-muted">기술스택</label>
      <div className="flex flex-wrap items-center gap-1.5 min-h-10 px-2 py-1.5 rounded-lg border border-m-border focus-within:border-m-primary focus-within:ring-1 focus-within:ring-m-primary">
        {value.map((tech) => (
          <span
            key={tech}
            className="inline-flex items-center gap-1 h-6 pl-2 pr-1 rounded-md bg-m-primary-soft text-m-primary text-[12px] font-medium"
          >
            {tech}
            <button
              type="button"
              onClick={() => onChange(value.filter((t) => t !== tech))}
              className="hover:bg-m-primary/10 rounded p-0.5"
              aria-label={`${tech} 삭제`}
            >
              <Icon name="x" size={12} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => { setDraft(e.target.value); setError(''); }}
          onKeyDown={handleKeyDown}
          onBlur={() => addToken(draft)}
          maxLength={MAX_ITEM_LEN}
          placeholder={value.length === 0 ? '예: React, TypeScript (Enter로 추가)' : '추가...'}
          className="flex-1 min-w-32 h-6 px-1 text-[13px] text-m-text bg-transparent focus:outline-none"
        />
      </div>
      {error && <p className="text-[12px] text-m-danger">{error}</p>}
    </div>
  );
}
