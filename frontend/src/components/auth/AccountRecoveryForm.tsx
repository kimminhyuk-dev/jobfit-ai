'use client';

import Link from 'next/link';
import { useState } from 'react';
import { authApi } from '../../api/auth';
import { formatPhoneNumber } from '../../lib/utils';
import { Alert } from '../ui/alert';
import { Button } from '../ui/button';
import Icon from '../ui/Icon';
import { Input } from '../ui/input';

export type RecoveryMode = 'find-email' | 'reset-password';
export type RecoveryAudience = 'user' | 'company';

type ResetStep = 'request' | 'confirm' | 'done';

interface RecoveryValues {
  name: string;
  phone: string;
  businessNumber: string;
  email: string;
  code: string;
}

interface AccountRecoveryFormProps {
  mode: RecoveryMode;
  initialAudience?: RecoveryAudience;
}

const INITIAL_RECOVERY_VALUES: RecoveryValues = {
  name: '',
  phone: '',
  businessNumber: '',
  email: '',
  code: '',
};

const FIND_EMAIL_MESSAGE =
  '입력하신 정보와 일치하는 계정이 있으면 가입 이메일로 아이디를 보내드렸습니다.';
const FIND_EMAIL_NOT_FOUND_MESSAGE = '일치하는 정보를 찾을 수 없습니다. 입력한 정보를 다시 확인해 주세요.';
const RESET_REQUEST_MESSAGE =
  '가입된 이메일이면 인증 코드를 보내드렸습니다. 메일을 확인해 주세요.';
const RESET_CONFIRM_MESSAGE =
  '임시 비밀번호를 이메일로 보내드렸습니다. 로그인 후 비밀번호를 변경해 주세요.';

function normalizeBusinessNumber(value: string): string {
  return value.replace(/\D/g, '');
}

export default function AccountRecoveryForm({
  mode,
  initialAudience = 'user',
}: AccountRecoveryFormProps) {
  const audience = initialAudience;
  const [resetStep, setResetStep] = useState<ResetStep>('request');
  const [values, setValues] = useState<RecoveryValues>(INITIAL_RECOVERY_VALUES);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [maskedEmail, setMaskedEmail] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isFindEmail = mode === 'find-email';

  const setField = (field: keyof RecoveryValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setMaskedEmail(null);
  };

  const validateBusinessNumber = () => {
    if (normalizeBusinessNumber(values.businessNumber).length !== 10) {
      setError('사업자등록번호 10자리를 입력하세요.');
      return false;
    }
    return true;
  };

  const handleFindEmail = async () => {
    setError(null);
    setMessage(null);
    setMaskedEmail(null);

    if (audience === 'user') {
      if (!values.name.trim() || !values.phone.trim()) {
        setError('이름과 휴대폰 번호를 입력하세요.');
        return;
      }
      setIsSubmitting(true);
      try {
        const res = await authApi.findEmail({
          name: values.name,
          phone: values.phone,
        });
        if (res.masked_email) {
          setMaskedEmail(res.masked_email);
          setMessage(res.message || FIND_EMAIL_MESSAGE);
        } else {
          setMessage(res.message || FIND_EMAIL_NOT_FOUND_MESSAGE);
        }
      } catch (err) {
        setError(getRecoveryErrorMessage(err));
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    if (!values.name.trim()) {
      setError('담당자명을 입력하세요.');
      return;
    }
    if (!validateBusinessNumber()) {
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await authApi.findCompanyEmail({
        name: values.name,
        business_number: normalizeBusinessNumber(values.businessNumber),
      });
      if (res.masked_email) {
        setMaskedEmail(res.masked_email);
        setMessage(res.message || FIND_EMAIL_MESSAGE);
      } else {
        setMessage(res.message || FIND_EMAIL_NOT_FOUND_MESSAGE);
      }
    } catch (err) {
      setError(getRecoveryErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestReset = async () => {
    setError(null);
    setMessage(null);
    setMaskedEmail(null);

    if (audience === 'user') {
      if (!values.email.trim()) {
        setError('이메일을 입력하세요.');
        return;
      }
      setIsSubmitting(true);
      try {
        const res = await authApi.requestPasswordReset({ email: values.email });
        setMessage(res.message || RESET_REQUEST_MESSAGE);
        setResetStep('confirm');
      } catch (err) {
        setError(getRecoveryErrorMessage(err));
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    if (!values.name.trim() || !values.email.trim()) {
      setError('담당자명과 이메일을 입력하세요.');
      return;
    }
    if (!validateBusinessNumber()) {
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await authApi.requestCompanyPasswordReset({
        name: values.name,
        business_number: normalizeBusinessNumber(values.businessNumber),
        email: values.email,
      });
      setMessage(res.message || RESET_REQUEST_MESSAGE);
      setResetStep('confirm');
    } catch (err) {
      setError(getRecoveryErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmReset = async () => {
    setError(null);
    setMessage(null);
    setMaskedEmail(null);

    if (!values.code.trim()) {
      setError('인증 코드를 입력하세요.');
      return;
    }

    if (!values.email.trim()) {
      setError('이메일을 입력하세요.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await authApi.confirmPasswordReset({
        email: values.email,
        code: values.code,
      });
      setMessage(res.message || RESET_CONFIRM_MESSAGE);
      setResetStep('done');
    } catch (err) {
      setError(getRecoveryErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <AudienceTabs mode={mode} audience={audience} />
      <RecoveryModeTabs mode={mode} audience={audience} />

      {isFindEmail ? (
        <FindAccountForm audience={audience} values={values} onFieldChange={setField} />
      ) : (
        <ResetPasswordForm
          audience={audience}
          resetStep={resetStep}
          values={values}
          onFieldChange={setField}
        />
      )}

      {error && <Alert variant="danger">{error}</Alert>}
      {(message || maskedEmail) && (
        <ResultPanel
          message={message}
          maskedEmail={isFindEmail ? maskedEmail : null}
        />
      )}

      {isFindEmail ? (
        <Button type="button" onClick={handleFindEmail} disabled={isSubmitting}>
          {isSubmitting ? '처리 중...' : '아이디 안내 받기'}
          {!isSubmitting && <Icon name="arrow" size={16} />}
        </Button>
      ) : resetStep === 'request' ? (
        <Button type="button" onClick={handleRequestReset} disabled={isSubmitting}>
          {isSubmitting ? '발송 중...' : '인증 코드 받기'}
          {!isSubmitting && <Icon name="arrow" size={16} />}
        </Button>
      ) : (
        <Button type="button" onClick={handleConfirmReset} disabled={isSubmitting || resetStep === 'done'}>
          {resetStep === 'done' ? '요청 완료' : isSubmitting ? '확인 중...' : '임시 비밀번호 받기'}
          {resetStep !== 'done' && !isSubmitting && <Icon name="arrow" size={16} />}
        </Button>
      )}

      {audience === 'company' && !isFindEmail && resetStep !== 'request' && (
        <p className="text-[12px] leading-relaxed text-m-subtle">
          인증 코드는 담당자명, 사업자등록번호, 이메일이 일치하는 경우에만 발송됩니다.
        </p>
      )}
    </div>
  );
}

function AudienceTabs({
  mode,
  audience,
}: {
  mode: RecoveryMode;
  audience: RecoveryAudience;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 rounded-lg bg-m-surface-alt p-1">
      {(['user', 'company'] as const).map((item) => (
        <Link
          key={item}
          href={recoveryHref(mode, item)}
          className={`flex h-9 items-center justify-center rounded-md text-[13px] font-semibold transition-colors ${
            audience === item
              ? 'bg-m-surface text-m-text shadow-sm'
              : 'text-m-muted hover:bg-m-surface hover:text-m-text'
          }`}
        >
          {item === 'user' ? '개인회원' : '기업회원'}
        </Link>
      ))}
    </div>
  );
}

function recoveryHref(mode: RecoveryMode, audience: RecoveryAudience): string {
  const basePath = mode === 'find-email' ? '/find-account' : '/reset-password';
  return audience === 'company' ? `${basePath}?audience=company` : basePath;
}

function RecoveryModeTabs({
  mode,
  audience,
}: {
  mode: RecoveryMode;
  audience: RecoveryAudience;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Button asChild type="button" variant={mode === 'find-email' ? 'default' : 'outline'} size="sm">
        <Link href={recoveryHref('find-email', audience)}>
          <Icon name="mail" size={15} />
          아이디 찾기
        </Link>
      </Button>
      <Button asChild type="button" variant={mode === 'reset-password' ? 'default' : 'outline'} size="sm">
        <Link href={recoveryHref('reset-password', audience)}>
          <Icon name="lock" size={15} />
          비밀번호 찾기
        </Link>
      </Button>
    </div>
  );
}

function FindAccountForm({
  audience,
  values,
  onFieldChange,
}: {
  audience: RecoveryAudience;
  values: RecoveryValues;
  onFieldChange: (field: keyof RecoveryValues, value: string) => void;
}) {
  return (
    <>
      <FieldWithIcon
        id="recovery-name"
        label={audience === 'company' ? '담당자명' : '이름'}
        icon="user"
        value={values.name}
        onChange={(value) => onFieldChange('name', value)}
        placeholder={audience === 'company' ? '담당자 또는 대표자명' : '가입한 이름'}
        autoComplete="name"
      />
      {audience === 'user' ? (
        <FieldWithIcon
          id="recovery-phone"
          label="휴대폰 번호"
          icon="phone"
          value={values.phone}
          onChange={(value) => onFieldChange('phone', formatPhoneNumber(value))}
          placeholder="010-1234-5678"
          autoComplete="tel"
        />
      ) : (
        <FieldWithIcon
          id="recovery-business-number"
          label="사업자등록번호"
          icon="building"
          value={values.businessNumber}
          onChange={(value) => onFieldChange('businessNumber', value)}
          placeholder="123-45-67890"
          autoComplete="off"
        />
      )}
    </>
  );
}

function ResetPasswordForm({
  audience,
  resetStep,
  values,
  onFieldChange,
}: {
  audience: RecoveryAudience;
  resetStep: ResetStep;
  values: RecoveryValues;
  onFieldChange: (field: keyof RecoveryValues, value: string) => void;
}) {
  const showIdentityFields = audience === 'company' && resetStep === 'request';
  return (
    <>
      {showIdentityFields && (
        <>
          <FieldWithIcon
            id="reset-name"
            label="담당자명"
            icon="user"
            value={values.name}
            onChange={(value) => onFieldChange('name', value)}
            placeholder="담당자 또는 대표자명"
            autoComplete="name"
          />
          <FieldWithIcon
            id="reset-business-number"
            label="사업자등록번호"
            icon="building"
            value={values.businessNumber}
            onChange={(value) => onFieldChange('businessNumber', value)}
            placeholder="123-45-67890"
            autoComplete="off"
          />
        </>
      )}
      <FieldWithIcon
        id="reset-email"
        label="이메일"
        icon="mail"
        value={values.email}
        onChange={(value) => onFieldChange('email', value)}
        placeholder="you@example.com"
        autoComplete="email"
        disabled={resetStep !== 'request'}
      />
      {resetStep !== 'request' && (
        <FieldWithIcon
          id="reset-code"
          label="인증 코드"
          icon="lock"
          value={values.code}
          onChange={(value) => onFieldChange('code', value)}
          placeholder="6자리 숫자"
          autoComplete="one-time-code"
        />
      )}
    </>
  );
}

function ResultPanel({
  message,
  maskedEmail,
}: {
  message: string | null;
  maskedEmail: string | null;
}) {
  if (maskedEmail) {
    return (
      <div className="rounded-lg border border-m-primary/20 bg-m-primary-soft px-4 py-3">
        <p className="text-[12px] font-medium text-m-muted">가입된 아이디</p>
        <p className="mt-1 font-mono text-[18px] font-bold text-m-text">{maskedEmail}</p>
        {message && <p className="mt-2 text-[13px] leading-relaxed text-m-muted">{message}</p>}
      </div>
    );
  }

  return <Alert variant="success">{message}</Alert>;
}

function FieldWithIcon({
  id,
  label,
  icon,
  value,
  onChange,
  placeholder,
  autoComplete,
  disabled = false,
}: {
  id: string;
  label: string;
  icon: 'user' | 'phone' | 'building' | 'mail' | 'lock';
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  autoComplete: string;
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="absolute -top-2 left-3 z-10 bg-m-surface px-1.5 text-[11px] font-medium text-m-muted"
      >
        {label}
      </label>
      <Input
        id={id}
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        disabled={disabled}
        className="pl-10"
      />
      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
        <Icon name={icon} size={16} />
      </div>
    </div>
  );
}

function getRecoveryErrorMessage(err: unknown): string {
  if (
    typeof err === 'object' &&
    err !== null &&
    'message' in err &&
    typeof (err as { message?: unknown }).message === 'string'
  ) {
    return (err as { message: string }).message;
  }
  return '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.';
}
