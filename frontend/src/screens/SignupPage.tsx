'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import type { FieldErrors } from 'react-hook-form';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import Icon from '../components/ui/Icon';
import { Alert } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { showToast } from '../components/ui/Toast';
import { authApi } from '../api/auth';
import type { SignupRequest } from '../api/auth';
import { useAuth } from '../stores/authContext';
import type { ApiError } from '../api/client';
import type { Gender } from '../api/types';
import AddressFields from '../components/profile/AddressFields';
import TechStackInput from '../components/profile/TechStackInput';

const signupSchema = z
  .object({
    name: z.string().trim().min(1, '이름을 입력하세요.').max(50, '이름은 50자 이하로 입력하세요.'),
    email: z
      .string()
      .trim()
      .min(1, '이메일을 입력하세요.')
      .email('올바른 이메일 형식으로 입력하세요.'),
    password: z
      .string()
      .min(8, '비밀번호는 8자 이상 입력하세요.')
      .max(128, '비밀번호는 128자 이하로 입력하세요.'),
    passwordConfirm: z.string().min(1, '비밀번호 확인을 입력하세요.'),
  })
  .superRefine(({ password, passwordConfirm }, ctx) => {
    if (passwordConfirm && password !== passwordConfirm) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['passwordConfirm'],
        message: '비밀번호가 일치하지 않습니다.',
      });
    }
  });

type SignupFormValues = z.infer<typeof signupSchema>;
type RequiredField = keyof SignupFormValues;

const FIELD_ORDER: RequiredField[] = ['name', 'email', 'password', 'passwordConfirm'];

function RequiredMark() {
  return (
    <span aria-hidden="true" className="ml-1 align-top text-[10px] font-bold text-m-danger">
      *
    </span>
  );
}

export default function SignupPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);
  const [activeField, setActiveField] = useState<RequiredField | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [serverFieldErrors, setServerFieldErrors] = useState<Record<string, string>>({});

  const [birthDate, setBirthDate] = useState('');
  const [phone, setPhone] = useState('');
  const [gender, setGender] = useState<'' | Gender>('');
  const [zipcode, setZipcode] = useState('');
  const [address1, setAddress1] = useState('');
  const [address2, setAddress2] = useState('');
  const [techStack, setTechStack] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    setFocus,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      passwordConfirm: '',
    },
    mode: 'onBlur',
    reValidateMode: 'onChange',
  });

  const passwordValue = useWatch({ control, name: 'password' }) ?? '';
  const passwordLengthOk = passwordValue.length >= 8;

  const clearServerFieldError = (field: string) => {
    if (!serverFieldErrors[field]) return;
    setServerFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const hasFieldError = (field: RequiredField) =>
    Boolean(errors[field]?.message || serverFieldErrors[field]);

  const inputClass = (field: RequiredField, extra = '') =>
    [
      'pl-10',
      activeField === field && !hasFieldError(field)
        ? 'border-m-primary ring-1 ring-m-primary'
        : '',
      hasFieldError(field)
        ? 'border-m-danger focus:border-m-danger focus:ring-m-danger'
        : '',
      extra,
    ]
      .filter(Boolean)
      .join(' ');

  const fieldError = (field: RequiredField) =>
    errors[field]?.message || serverFieldErrors[field];

  const focusField = (field: RequiredField) => {
    setActiveField(field);
    const target = document.querySelector<HTMLInputElement>(`[name="${field}"]`);
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    window.setTimeout(() => {
      setFocus(field);
    }, 0);
  };

  const onInvalid = (formErrors: FieldErrors<SignupFormValues>) => {
    const firstField = FIELD_ORDER.find((field) => formErrors[field]);
    if (!firstField) return;

    const message =
      formErrors[firstField]?.message?.toString() ?? '필수 입력 항목을 확인해주세요.';
    showToast(message, 'error');
    focusField(firstField);
  };

  const validateOptionalProfile = () => {
    const phoneDigits = phone.replace(/\D/g, '');
    if (phone.trim() && !/^01[016789]\d{7,8}$/.test(phoneDigits)) {
      return '휴대폰 번호 형식을 확인해주세요.';
    }
    return null;
  };

  const onSubmit = async (values: SignupFormValues) => {
    setError(null);
    setServerFieldErrors({});

    const profileError = validateOptionalProfile();
    if (profileError) {
      setError(profileError);
      showToast(profileError, 'error');
      document.getElementById('signup-phone')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    try {
      const body: SignupRequest = {
        name: values.name,
        email: values.email,
        password: values.password,
        birth_date: birthDate || null,
        phone: phone.trim() || null,
        gender: gender || null,
        zipcode: zipcode || null,
        address1: address1 || null,
        address2: address2.trim() || null,
        tech_stack: techStack.length ? techStack : null,
      };
      const res = await authApi.signup(body);
      login(res.user);
      router.push('/user/resumes');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.details) {
        const map: Record<string, string> = {};
        apiErr.details.forEach((d) => {
          const field = d.loc[d.loc.length - 1];
          if (typeof field === 'string') {
            map[field] = d.msg;
          }
        });
        setServerFieldErrors(map);

        const firstServerField = FIELD_ORDER.find((field) => map[field]);
        if (firstServerField) {
          showToast(map[firstServerField], 'error');
          focusField(firstServerField);
        }
      } else {
        const message = apiErr.message ?? '회원가입에 실패했습니다.';
        setError(message);
        showToast(message, 'error');
      }
    }
  };

  return (
    <div className="min-h-screen bg-m-bg flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-[480px]">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-8 h-8 rounded-lg bg-m-primary flex items-center justify-center text-white">
            <Icon name="target" size={17} />
          </div>
          <span className="font-bold text-[16px] text-m-text tracking-tight">JobFit AI</span>
        </div>

        <div className="bg-m-surface border border-m-border rounded-2xl p-7 sm:p-8 shadow-sm">
          <div className="mb-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-[22px] font-bold text-m-text tracking-tight">계정 만들기</h1>
                <p className="text-[13px] text-m-muted mt-1.5">
                  가입 후 바로 이력서를 등록하고 공고에 지원할 수 있습니다.
                </p>
              </div>
              <p className="shrink-0 pt-1 text-[11px] text-m-subtle">
                <RequiredMark /> 필수
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit, onInvalid)} className="flex flex-col gap-4" noValidate>
            <section className="space-y-4" aria-label="필수 계정 정보">
              <div>
                <label htmlFor="signup-name" className="block text-[12px] font-medium text-m-muted mb-1.5">
                  이름
                  <RequiredMark />
                </label>
                <div className="relative">
                  <Input
                    id="signup-name"
                    placeholder="홍길동"
                    autoComplete="name"
                    aria-invalid={hasFieldError('name')}
                    aria-describedby={fieldError('name') ? 'signup-name-error' : undefined}
                    className={inputClass('name')}
                    {...register('name', {
                      onChange: () => clearServerFieldError('name'),
                    })}
                    onFocus={() => setActiveField('name')}
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                    <Icon name="user" size={16} />
                  </div>
                </div>
                {fieldError('name') && (
                  <p id="signup-name-error" role="alert" className="mt-1.5 text-[12px] text-m-danger">
                    {fieldError('name')}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="signup-email" className="block text-[12px] font-medium text-m-muted mb-1.5">
                  이메일
                  <RequiredMark />
                </label>
                <div className="relative">
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    aria-invalid={hasFieldError('email')}
                    aria-describedby={fieldError('email') ? 'signup-email-error' : undefined}
                    className={inputClass('email')}
                    {...register('email', {
                      onChange: () => clearServerFieldError('email'),
                    })}
                    onFocus={() => setActiveField('email')}
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                    <Icon name="mail" size={16} />
                  </div>
                </div>
                {fieldError('email') && (
                  <p id="signup-email-error" role="alert" className="mt-1.5 text-[12px] text-m-danger">
                    {fieldError('email')}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="signup-password" className="block text-[12px] font-medium text-m-muted mb-1.5">
                  비밀번호
                  <RequiredMark />
                </label>
                <div className="relative">
                  <Input
                    id="signup-password"
                    type={showPw ? 'text' : 'password'}
                    placeholder="8자 이상"
                    autoComplete="new-password"
                    aria-invalid={hasFieldError('password')}
                    aria-describedby="signup-password-help signup-password-error"
                    className={inputClass('password', 'pr-10')}
                    {...register('password', {
                      onChange: () => clearServerFieldError('password'),
                    })}
                    onFocus={() => setActiveField('password')}
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                    <Icon name="lock" size={16} />
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-m-subtle hover:text-m-muted"
                    aria-label={showPw ? '비밀번호 숨기기' : '비밀번호 보기'}
                  >
                    <Icon name={showPw ? 'eye-off' : 'eye'} size={16} />
                  </button>
                </div>
                <div id="signup-password-help" className="mt-2 flex items-center gap-1.5 text-[12px]">
                  <Icon
                    name={passwordLengthOk ? 'check' : 'bell'}
                    size={13}
                    className={passwordLengthOk ? 'text-m-success' : 'text-m-subtle'}
                  />
                  <span className={passwordLengthOk ? 'text-m-success' : 'text-m-subtle'}>
                    8자 이상 입력
                  </span>
                  <span className="text-m-subtle">({Math.min(passwordValue.length, 8)}/8)</span>
                </div>
                {fieldError('password') && (
                  <div
                    id="signup-password-error"
                    role="alert"
                    className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-m-danger bg-m-danger-soft px-2.5 py-1.5 text-[12px] font-medium text-m-danger"
                  >
                    <Icon name="bell" size={13} />
                    {fieldError('password')}
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="signup-password-confirm" className="block text-[12px] font-medium text-m-muted mb-1.5">
                  비밀번호 확인
                  <RequiredMark />
                </label>
                <div className="relative">
                  <Input
                    id="signup-password-confirm"
                    type={showPwConfirm ? 'text' : 'password'}
                    placeholder="비밀번호 재입력"
                    autoComplete="new-password"
                    aria-invalid={hasFieldError('passwordConfirm')}
                    aria-describedby={fieldError('passwordConfirm') ? 'signup-password-confirm-error' : undefined}
                    className={inputClass('passwordConfirm', 'pr-10')}
                    {...register('passwordConfirm')}
                    onFocus={() => setActiveField('passwordConfirm')}
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                    <Icon name="lock" size={16} />
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowPwConfirm((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-m-subtle hover:text-m-muted"
                    aria-label={showPwConfirm ? '비밀번호 확인 숨기기' : '비밀번호 확인 보기'}
                  >
                    <Icon name={showPwConfirm ? 'eye-off' : 'eye'} size={16} />
                  </button>
                </div>
                {fieldError('passwordConfirm') && (
                  <p id="signup-password-confirm-error" role="alert" className="mt-1.5 text-[12px] text-m-danger">
                    {fieldError('passwordConfirm')}
                  </p>
                )}
              </div>
            </section>

            <section className="space-y-4 border-t border-m-border pt-4" aria-label="선택 프로필 정보">
              <div>
                <p className="text-[12px] font-semibold text-m-muted">
                  추가 정보 <span className="font-normal text-m-subtle">(선택)</span>
                </p>
                <p className="mt-1 text-[11px] text-m-subtle">
                  입력하면 추천 공고와 이력서 관리에 함께 활용됩니다.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="signup-birth-date" className="block text-[12px] font-medium text-m-muted mb-1.5">
                    생년월일
                  </label>
                  <Input
                    id="signup-birth-date"
                    type="date"
                    max={new Date().toISOString().slice(0, 10)}
                    value={birthDate}
                    onChange={(e) => {
                      setBirthDate(e.target.value);
                      clearServerFieldError('birth_date');
                    }}
                  />
                  {serverFieldErrors['birth_date'] && (
                    <p className="mt-1 text-[12px] text-m-danger">{serverFieldErrors['birth_date']}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="signup-gender" className="block text-[12px] font-medium text-m-muted mb-1.5">
                    성별
                  </label>
                  <select
                    id="signup-gender"
                    value={gender}
                    onChange={(e) => setGender(e.target.value as '' | Gender)}
                    className="w-full h-11 px-3 rounded-lg border border-m-border text-[14px] text-m-text bg-m-surface focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                  >
                    <option value="">선택 안 함</option>
                    <option value="MALE">남성</option>
                    <option value="FEMALE">여성</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="signup-phone" className="block text-[12px] font-medium text-m-muted mb-1.5">
                  휴대폰 번호
                </label>
                <Input
                  id="signup-phone"
                  inputMode="numeric"
                  placeholder="010-1234-5678"
                  value={phone}
                  onChange={(e) => {
                    setPhone(e.target.value);
                    clearServerFieldError('phone');
                  }}
                />
                {serverFieldErrors['phone'] && (
                  <p className="mt-1 text-[12px] text-m-danger">{serverFieldErrors['phone']}</p>
                )}
              </div>

              <AddressFields
                value={{ zipcode, address1, address2 }}
                onChange={(next) => {
                  if (next.zipcode !== undefined) {
                    setZipcode(next.zipcode);
                    clearServerFieldError('zipcode');
                  }
                  if (next.address1 !== undefined) {
                    setAddress1(next.address1);
                    clearServerFieldError('address1');
                  }
                  if (next.address2 !== undefined) {
                    setAddress2(next.address2);
                    clearServerFieldError('address2');
                  }
                }}
              />

              <TechStackInput value={techStack} onChange={setTechStack} />
            </section>

            {error && <Alert variant="danger">{error}</Alert>}

            <Button type="submit" disabled={isSubmitting} className="mt-1">
              {isSubmitting ? '가입 중...' : '시작하기'}
              {!isSubmitting && <Icon name="arrow" size={16} />}
            </Button>
          </form>

          <p className="text-[13px] text-m-muted text-center mt-6">
            이미 계정이 있으신가요?{' '}
            <Link href="/login" className="text-m-primary font-medium hover:underline">
              로그인
            </Link>
          </p>
        </div>

        <p className="text-[11px] text-m-subtle text-center mt-4">© 2026 JobFit AI · 개인정보 보호</p>
      </div>
    </div>
  );
}
