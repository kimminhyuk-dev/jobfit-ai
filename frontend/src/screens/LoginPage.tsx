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
    ? '사업자등록번호 또는 이메일을 확인해주세요.'
    : '아이디 또는 비밀번호를 확인해주세요.';
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
      // 로그인 성공 시 환경설정 저장.
      writeSavedId(portal, saveId ? values.email : null);
      writeAutoLogin(autoLogin);
      login(res.user);
      router.push(routeForUser(res.user));
    } catch {
      setError(loginFailureMessage(portal));
    }
  };

  return (
    <div className="flex h-screen bg-m-bg font-sans">
      <div className="flex-[0_0_50%] flex flex-col bg-m-surface px-16 py-12 justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-m-primary flex items-center justify-center text-white">
            <Icon name="target" size={17} />
          </div>
          <span className="font-bold text-[16px] text-m-text tracking-tight">JobFit AI</span>
        </div>

        <div className="max-w-[380px] w-full mx-auto">
          <h1 className="text-[28px] font-bold text-m-text tracking-tight leading-tight">
            {isCompanyPortal ? '기업회원 · 관리자 로그인' : '일반회원 로그인'}
          </h1>
          <p className="text-[14px] text-m-muted mt-2 mb-8 leading-relaxed">
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
                <button type="button" className="text-[12px] text-m-primary hover:underline">
                  잊으셨나요?
                </button>
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

            <div className="flex items-center gap-3 text-m-subtle text-[12px]">
              <div className="flex-1 h-px bg-m-border" />
              또는
              <div className="flex-1 h-px bg-m-border" />
            </div>

            <Button type="button" variant="outline" className="font-medium">
              <Icon name="google" size={16} strokeWidth={0} />
              Google로 계속하기
            </Button>
          </form>

          <p className="text-[13px] text-m-muted text-center mt-7">
            {isCompanyPortal ? (
              <>
                일반회원이신가요?{' '}
                <Link href="/login" className="text-m-primary font-medium hover:underline">
                  일반회원 로그인
                </Link>
              </>
            ) : (
              <>
                기업회원 또는 관리자이신가요?{' '}
                <Link href="/company/login" className="text-m-primary font-medium hover:underline">
                  기업회원 로그인
                </Link>
                <br />
                계정이 없으신가요?{' '}
                <Link href="/signup" className="text-m-primary font-medium hover:underline">
                  회원가입
                </Link>
              </>
            )}
          </p>
        </div>

        <p className="text-[11px] text-m-subtle">© 2026 JobFit AI · 개인정보 보호</p>
      </div>

      <div
        className="flex-1 flex flex-col justify-center p-12 relative overflow-hidden"
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
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/15 backdrop-blur-sm rounded-full text-[12px] font-medium text-white mb-5">
            <Icon name="sparkle" size={12} />
            AI 분석 v3.2
          </div>
          <h2 className="text-[32px] font-bold text-white leading-tight tracking-tight">
            이력서를 올리면
            <br />
            어울리는 회사가 보여요
          </h2>
          <p className="text-[15px] text-white/80 mt-4 mb-8 leading-relaxed">
            매일 수집되는 채용공고와 비교해 강점과 보완점을 알려드립니다.
          </p>

          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5 flex items-center gap-4">
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
            <div className="flex-1 min-w-0">
              <p className="text-[11px] text-white/60 font-medium tracking-widest uppercase">최고 매칭</p>
              <p className="text-[15px] font-semibold text-white mt-1">프론트엔드 엔지니어</p>
              <div className="flex gap-1.5 mt-2 flex-wrap">
                {['React', 'TypeScript', 'Next.js'].map((s) => (
                  <span key={s} className="text-[11px] px-2 py-0.5 bg-white/15 rounded text-white font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-8 mt-8">
            {[
              { v: '12,400+', l: '활성 채용공고' },
              { v: '94%', l: '매칭 정확도' },
              { v: '23초', l: '평균 분석 시간' },
            ].map((s) => (
              <div key={s.l}>
                <p className="text-[22px] font-bold text-white font-mono tracking-tight">{s.v}</p>
                <p className="text-[11px] text-white/60 mt-0.5">{s.l}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
