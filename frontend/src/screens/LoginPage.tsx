'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import Icon from '../components/ui/Icon';
import Gauge from '../components/ui/Gauge';
import { Alert } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { authApi } from '../api/auth';
import { useAuth } from '../stores/authContext';
import { writeAutoLogin, writeSavedId } from '../lib/loginPrefs';
import type { User } from '../api/types';

const loginSchema = z.object({
  email: z.string().trim().min(1, '이메일 또는 사업자번호를 입력하세요.'),
  password: z.string().min(1, '비밀번호를 입력하세요.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;
type LoginPortal = 'user' | 'company';

interface LoginPageProps {
  portal?: LoginPortal;
}

function normalizedRole(user: User): string {
  return user.role.trim().toUpperCase();
}

function routeForUser(user: User): string {
  const role = normalizedRole(user);
  if (role === 'ADMIN') return '/admin/dashboard';
  if (role === 'COMPANY') return '/company/dashboard';
  return '/user/dashboard';
}

function loginFailureMessage(portal: LoginPortal): string {
  return portal === 'company'
    ? '사업자등록번호 또는 이메일을 확인해 주세요.'
    : '아이디 또는 비밀번호를 확인해 주세요.';
}

function isAllowedForPortal(user: User, portal: LoginPortal): boolean {
  const role = normalizedRole(user);
  if (portal === 'company') return role === 'COMPANY' || role === 'ADMIN';
  return role === 'USER';
}

export default function LoginPage({ portal = 'user' }: LoginPageProps) {
  const router = useRouter();
  const { login } = useAuth();
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveId, setSaveId] = useState(false);
  const [autoLogin, setAutoLogin] = useState(false);
  const isCompanyPortal = portal === 'company';
  const recoveryAudienceQuery = isCompanyPortal ? '?audience=company' : '';

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setError(null);
    try {
      const res = await authApi.login({ ...values, portal });
      if (!isAllowedForPortal(res.user, portal)) {
        await authApi.logout().catch(() => undefined);
        setError(loginFailureMessage(portal));
        return;
      }
      writeSavedId(portal, saveId ? values.email : null);
      writeAutoLogin(autoLogin);
      login(res.user);
      router.push(routeForUser(res.user));
    } catch {
      setError(loginFailureMessage(portal));
    }
  };

  return (
    <div className="flex min-h-screen bg-m-bg font-sans">
      <div className="flex flex-[0_0_50%] flex-col justify-between bg-m-surface px-16 py-12">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-m-primary text-white">
            <Icon name="target" size={17} />
          </div>
          <span className="text-[16px] font-bold tracking-tight text-m-text">JobFit AI</span>
        </div>

        <div className="mx-auto w-full max-w-[400px]">
          <h1 className="text-[28px] font-bold leading-tight tracking-tight text-m-text">
            {isCompanyPortal ? '기업회원 · 관리자 로그인' : '일반회원 로그인'}
          </h1>
          <p className="mb-8 mt-2 text-[14px] leading-relaxed text-m-muted">
            {isCompanyPortal
              ? '사업자번호 또는 관리자 이메일로 접속하세요.'
              : '이메일로 로그인하고 맞춤 채용공고를 확인하세요.'}
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <div>
                <div className="relative">
                  <label
                    htmlFor="login-id"
                    className="absolute -top-2 left-3 z-10 bg-m-surface px-1.5 text-[11px] font-medium text-m-muted"
                  >
                    아이디
                  </label>
                  <Input
                    id="login-id"
                    type="text"
                    placeholder={isCompanyPortal ? 'you@example.com 또는 123-45-67890' : 'you@example.com'}
                    autoComplete="username"
                    className="pl-10"
                    {...register('email')}
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                    <Icon name="user" size={16} />
                  </div>
                </div>
                {errors.email && <p className="mt-1 text-[12px] text-m-danger">{errors.email.message}</p>}
              </div>

              <div>
                <div className="relative">
                  <label
                    htmlFor="login-pw"
                    className="absolute -top-2 left-3 z-10 bg-m-surface px-1.5 text-[11px] font-medium text-m-muted"
                  >
                    비밀번호
                  </label>
                  <Input
                    id="login-pw"
                    type={showPw ? 'text' : 'password'}
                    placeholder="비밀번호 입력"
                    autoComplete="current-password"
                    className="pl-10 pr-10"
                    {...register('password')}
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
                <div className="mt-1.5 flex items-center justify-between">
                  {errors.password ? (
                    <p className="text-[12px] text-m-danger">{errors.password.message}</p>
                  ) : (
                    <span />
                  )}
                  <div className="flex items-center gap-2 text-[12px]">
                    <Link
                      href={`/find-account${recoveryAudienceQuery}`}
                      className="text-m-primary hover:underline"
                    >
                      아이디 찾기
                    </Link>
                    <span className="text-m-subtle">/</span>
                    <Link
                      href={`/reset-password${recoveryAudienceQuery}`}
                      className="text-m-primary hover:underline"
                    >
                      비밀번호 찾기
                    </Link>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-5">
                <label className="flex cursor-pointer select-none items-center gap-2 text-[13px] text-m-muted">
                  <input
                    type="checkbox"
                    checked={saveId}
                    onChange={(e) => setSaveId(e.target.checked)}
                    className="h-4 w-4 rounded border-m-border accent-m-primary"
                  />
                  아이디 저장
                </label>
                <label className="flex cursor-pointer select-none items-center gap-2 text-[13px] text-m-muted">
                  <input
                    type="checkbox"
                    checked={autoLogin}
                    onChange={(e) => setAutoLogin(e.target.checked)}
                    className="h-4 w-4 rounded border-m-border accent-m-primary"
                  />
                  자동 로그인
                </label>
              </div>

              {error && <Alert variant="danger">{error}</Alert>}

              <Button type="submit" disabled={isSubmitting} className="mt-1">
                {isSubmitting ? '로그인 중...' : '로그인'}
                {!isSubmitting && <Icon name="arrow" size={16} />}
              </Button>

              {!isCompanyPortal && (
                <>
                  <div className="flex items-center gap-3 text-[12px] text-m-subtle">
                    <div className="h-px flex-1 bg-m-border" />
                    또는
                    <div className="h-px flex-1 bg-m-border" />
                  </div>

                  <Button type="button" variant="outline" className="font-medium">
                    <Icon name="google" size={16} strokeWidth={0} />
                    Google로 계속하기
                  </Button>
                </>
              )}
          </form>

          <p className="mt-7 text-center text-[13px] text-m-muted">
              {isCompanyPortal ? (
                <>
                  일반회원이신가요?{' '}
                  <Link href="/login" className="font-medium text-m-primary hover:underline">
                    일반회원 로그인
                  </Link>
                </>
              ) : (
                <>
                  기업회원 또는 관리자이신가요?{' '}
                  <Link href="/company/login" className="font-medium text-m-primary hover:underline">
                    기업회원 로그인
                  </Link>
                  <br />
                  계정이 없으신가요?{' '}
                  <Link href="/signup" className="font-medium text-m-primary hover:underline">
                    회원가입
                  </Link>
                </>
              )}
          </p>
        </div>

        <p className="text-[11px] text-m-subtle">© 2026 JobFit AI · 개인정보 보호</p>
      </div>

      <div
        className="relative flex flex-1 flex-col justify-center overflow-hidden p-12"
        style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #1e1b4b 100%)' }}
      >
        <svg className="absolute inset-0 opacity-[0.07]" width="100%" height="100%">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#fff" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        <div className="relative max-w-[420px]">
          <div className="mb-5 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-[12px] font-medium text-white backdrop-blur-sm">
            <Icon name="sparkle" size={12} />
            AI 분석 v3.2
          </div>
          <h2 className="text-[32px] font-bold leading-tight tracking-tight text-white">
            이력서를 올리면
            <br />
            어울리는 회사가 보여요
          </h2>
          <p className="mb-8 mt-4 text-[15px] leading-relaxed text-white/80">
            매일 수집되는 채용공고와 비교해 강점과 보완점을 알려드립니다.
          </p>

          <div className="flex items-center gap-4 rounded-2xl border border-white/20 bg-white/10 p-5 backdrop-blur-md">
            <Gauge
              score={94}
              size={72}
              stroke={7}
              label=""
              primaryColor="#60a5fa"
              successColor="#34d399"
              warnColor="#fbbf24"
              borderColor="rgba(255,255,255,0.2)"
              textColor="#fff"
              subtleColor="rgba(255,255,255,0.6)"
            />
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-medium uppercase tracking-widest text-white/60">최고 매칭</p>
              <p className="mt-1 text-[15px] font-semibold text-white">프론트엔드 엔지니어</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {['React', 'TypeScript', 'Next.js'].map((skill) => (
                  <span key={skill} className="rounded bg-white/15 px-2 py-0.5 text-[11px] font-medium text-white">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-8 flex gap-8">
            {[
              { v: '12,400+', l: '활성 채용공고' },
              { v: '94%', l: '매칭 정확도' },
              { v: '23초', l: '평균 분석 시간' },
            ].map((stat) => (
              <div key={stat.l}>
                <p className="font-mono text-[22px] font-bold tracking-tight text-white">{stat.v}</p>
                <p className="mt-0.5 text-[11px] text-white/60">{stat.l}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
