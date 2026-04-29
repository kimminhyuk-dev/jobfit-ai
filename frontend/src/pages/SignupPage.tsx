import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Icon from '../components/ui/Icon';
import { authApi } from '../api/auth';
import { useAuth } from '../stores/authStore';
import type { ApiError } from '../api/client';

export default function SignupPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setLoading(true);
    try {
      const res = await authApi.signup({ name, email, password });
      login(res.access_token, res.user);
      navigate('/user/resumes');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.details) {
        const map: Record<string, string> = {};
        apiErr.details.forEach((d) => { map[d.field] = d.message; });
        setFieldErrors(map);
      } else {
        setError(apiErr.message ?? '회원가입에 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  const inputBase =
    'w-full h-11 rounded-lg border bg-m-surface text-[14px] text-m-text placeholder:text-m-subtle focus:outline-none focus:ring-1 transition-colors';

  const inputClass = (field: string) =>
    `${inputBase} pl-10 ${
      fieldErrors[field]
        ? 'border-m-danger focus:border-m-danger focus:ring-m-danger'
        : 'border-m-border focus:border-m-primary focus:ring-m-primary'
    }`;

  return (
    <div className="min-h-screen bg-m-bg flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-[440px]">
        {/* Logo */}
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-8 h-8 rounded-lg bg-m-primary flex items-center justify-center text-white">
            <Icon name="target" size={17} />
          </div>
          <span className="font-bold text-[16px] text-m-text tracking-tight">JobFit AI</span>
        </div>

        <div className="bg-m-surface border border-m-border rounded-2xl p-8 shadow-sm">
          <h1 className="text-[22px] font-bold text-m-text tracking-tight">계정 만들기</h1>
          <p className="text-[13px] text-m-muted mt-1.5 mb-6">
            시작하는 데 1분도 걸리지 않아요.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Name */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">이름</label>
              <div className="relative">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="홍길동"
                  required
                  className={inputClass('name')}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="user" size={16} />
                </div>
              </div>
              {fieldErrors.name && <p className="mt-1 text-[12px] text-m-danger">{fieldErrors.name}</p>}
            </div>

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
                  className={inputClass('email')}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="mail" size={16} />
                </div>
              </div>
              {fieldErrors.email && <p className="mt-1 text-[12px] text-m-danger">{fieldErrors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">비밀번호</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="8자 이상"
                  required
                  minLength={8}
                  className={`${inputClass('password')} pr-10`}
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
              {fieldErrors.password && <p className="mt-1 text-[12px] text-m-danger">{fieldErrors.password}</p>}
            </div>

            {/* Global error */}
            {error && (
              <p className="text-[13px] text-m-danger bg-m-danger-soft px-3 py-2 rounded-lg">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="h-11 mt-1 rounded-lg bg-m-primary text-white text-[14px] font-semibold hover:bg-m-primary-hover transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? '가입 중...' : '시작하기'}
              {!loading && <Icon name="arrow" size={16} />}
            </button>
          </form>

          <p className="text-[13px] text-m-muted text-center mt-6">
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="text-m-primary font-medium hover:underline">
              로그인
            </Link>
          </p>
        </div>

        <p className="text-[11px] text-m-subtle text-center mt-4">© 2026 JobFit AI · 개인정보 보호</p>
      </div>
    </div>
  );
}
