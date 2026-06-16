'use client';

import { useRef, useState } from 'react';
import Icon from '../ui/Icon';
import { openPostcodeSearch } from '../../lib/postcode';

interface AddressValue {
  zipcode: string;
  address1: string;
  address2: string;
}

export default function AddressFields({
  value,
  onChange,
}: {
  value: AddressValue;
  onChange: (next: Partial<AddressValue>) => void;
}) {
  const [error, setError] = useState('');
  const detailRef = useRef<HTMLInputElement>(null);

  async function handleSearch() {
    setError('');
    try {
      await openPostcodeSearch(({ zonecode, address }) => {
        onChange({ zipcode: zonecode, address1: address });
        // 선택 후 상세주소 입력으로 포커스 이동
        setTimeout(() => detailRef.current?.focus(), 0);
      });
    } catch {
      setError('주소검색 서비스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-[12px] font-medium text-m-muted">주소</label>
      <div className="flex gap-2">
        <input
          value={value.zipcode}
          readOnly
          placeholder="우편번호"
          className="w-28 h-10 px-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] text-m-text"
        />
        <button
          type="button"
          onClick={handleSearch}
          className="h-10 px-4 rounded-lg border border-m-border text-[13px] font-medium text-m-muted hover:bg-m-surface-alt transition-colors flex items-center gap-1.5"
        >
          <Icon name="search" size={14} />
          주소검색
        </button>
      </div>
      <input
        value={value.address1}
        readOnly
        placeholder="기본주소 (주소검색으로 입력)"
        className="w-full h-10 px-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] text-m-text"
      />
      <input
        ref={detailRef}
        value={value.address2}
        onChange={(e) => onChange({ address2: e.target.value })}
        maxLength={255}
        placeholder="상세주소 (동/호수 등)"
        className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
      />
      {error && <p className="text-[12px] text-m-danger">{error}</p>}
    </div>
  );
}
