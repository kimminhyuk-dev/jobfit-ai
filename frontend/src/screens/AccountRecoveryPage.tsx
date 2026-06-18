'use client';

import Link from 'next/link';
import AccountRecoveryForm, {
  type RecoveryAudience,
  type RecoveryMode,
} from '../components/auth/AccountRecoveryForm';
import Gauge from '../components/ui/Gauge';
import Icon from '../components/ui/Icon';

interface AccountRecoveryPageProps {
  mode: RecoveryMode;
  initialAudience?: RecoveryAudience;
}

export default function AccountRecoveryPage({
  mode,
  initialAudience = 'user',
}: AccountRecoveryPageProps) {
  const isFindEmail = mode === 'find-email';

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
          <Link
            href={initialAudience === 'company' ? '/company/login' : '/login'}
            className="mb-5 flex items-center gap-1 text-[13px] font-medium text-m-muted transition-colors hover:text-m-text"
          >
            <Icon name="arrow-left" size={15} />
            로그인으로 돌아가기
          </Link>

          <h1 className="text-[28px] font-bold leading-tight tracking-tight text-m-text">
            {isFindEmail ? '아이디 찾기' : '비밀번호 찾기'}
          </h1>
          <p className="mb-8 mt-2 text-[14px] leading-relaxed text-m-muted">
            회원 유형을 선택하고 가입 정보를 입력하세요.
          </p>

          <AccountRecoveryForm mode={mode} initialAudience={initialAudience} />
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
            안전한 계정 복구
          </div>
          <h2 className="text-[32px] font-bold leading-tight tracking-tight text-white">
            필요한 정보만 확인하고
            <br />
            이메일로 안내해요
          </h2>
          <p className="mb-8 mt-4 text-[15px] leading-relaxed text-white/80">
            비밀번호 재설정은 5분 동안 유효한 인증 코드로 보호됩니다.
          </p>

          <div className="flex items-center gap-4 rounded-2xl border border-white/20 bg-white/10 p-5 backdrop-blur-md">
            <Gauge
              score={98}
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
              <p className="text-[11px] font-medium uppercase tracking-widest text-white/60">
                Account Recovery
              </p>
              <p className="mt-1 text-[15px] font-semibold text-white">
                {isFindEmail ? '아이디 안내 메일 발송' : '인증 코드 확인 후 임시 비밀번호 발급'}
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {['이메일 안내', '코드 5분 유효', '보안 로그'].map((item) => (
                  <span key={item} className="rounded bg-white/15 px-2 py-0.5 text-[11px] font-medium text-white">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
