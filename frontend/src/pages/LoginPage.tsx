import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Icon from '../components/ui/Icon';
import Gauge from '../components/ui/Gauge';
import { authApi } from '../api/auth';
import { useAuth } from '../stores/authStore';
import type { ApiError } from '../api/client';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login({ email, password });
      login(res.access_token, res.user);
      navigate(res.user.role === 'ADMIN' ? '/admin/dashboard' : '/user/dashboard');
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const inputBase =
    'w-full h-11 rounded-lg border border-m-border bg-m-surface text-[14px] text-m-text placeholder:text-m-subtle focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary transition-colors';

  return (
    <div className="flex h-screen bg-m-bg font-sans">
      {/* Left — form panel */}
      <div className="flex-[0_0_50%] flex flex-col bg-m-surface px-16 py-12 justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-m-primary flex items-center justify-center text-white">
            <Icon name="target" size={17} />
          </div>
          <span className="font-bold text-[16px] text-m-text tracking-tight">JobFit AI</span>
        </div>

        {/* Form */}
        <div className="max-w-[380px] w-full mx-auto">
          <h1 className="text-[28px] font-bold text-m-text tracking-tight leading-tight">다시 만나서 반가워요</h1>
          <p className="text-[14px] text-m-muted mt-2 mb-8 leading-relaxed">
            이력서를 분석하고 맞춤 채용공고를 추천해 드릴게요.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Email */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">이메일</label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className={`${inputBase} pl-10`}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="mail" size={16} />
                </div>
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-[12px] font-medium text-m-muted">비밀번호</label>
                <button type="button" className="text-[12px] text-m-primary hover:underline">
                  잊으셨나요?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호 입력"
                  required
                  className={`${inputBase} pl-10 pr-10`}
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
            </div>

            {/* Error */}
            {error && (
              <p className="text-[13px] text-m-danger bg-m-danger-soft px-3 py-2 rounded-lg">{error}</p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="h-11 mt-1 rounded-lg bg-m-primary text-white text-[14px] font-semibold hover:bg-m-primary-hover transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? '로그인 중...' : '로그인'}
              {!loading && <Icon name="arrow" size={16} />}
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 text-m-subtle text-[12px]">
              <div className="flex-1 h-px bg-m-border" />
              또는
              <div className="flex-1 h-px bg-m-border" />
            </div>

            {/* Google */}
            <button
              type="button"
              className="h-11 rounded-lg border border-m-border bg-m-surface text-[14px] font-medium text-m-text hover:bg-m-surface-alt transition-colors flex items-center justify-center gap-2.5"
            >
              <Icon name="google" size={16} strokeWidth={0} />
              Google로 계속하기
            </button>
          </form>

          <p className="text-[13px] text-m-muted text-center mt-7">
            계정이 없으신가요?{' '}
            <Link to="/signup" className="text-m-primary font-medium hover:underline">
              회원가입
            </Link>
          </p>
        </div>

        <p className="text-[11px] text-m-subtle">© 2026 JobFit AI · 개인정보 보호</p>
      </div>

      {/* Right — marketing panel */}
      <div
        className="flex-1 flex flex-col justify-center p-12 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #1e1b4b 100%)' }}
      >
        {/* Grid bg */}
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
            이력서를 올리면<br />어울리는 회사가 보여요.
          </h2>
          <p className="text-[15px] text-white/80 mt-4 mb-8 leading-relaxed">
            매일 1만 건의 채용공고와 비교 분석합니다. 내 이력의 강점과 보완할 점을 LLM이 짚어드릴게요.
          </p>

          {/* Preview card */}
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
              <p className="text-[15px] font-semibold text-white mt-1">네오랩스 · 프론트엔드 엔지니어</p>
              <div className="flex gap-1.5 mt-2 flex-wrap">
                {['React', 'TypeScript', 'Next.js'].map((s) => (
                  <span key={s} className="text-[11px] px-2 py-0.5 bg-white/15 rounded text-white font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Stats */}
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
