import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import Icon from '../components/ui/Icon';
import { Alert } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { authApi } from '../api/auth';
import { useAuth } from '../stores/authContext';
import type { ApiError } from '../api/client';

const signupSchema = z.object({
  name: z.string().min(1, '이름을 입력하세요.').max(50, '이름은 50자 이하로 입력하세요.'),
  email: z.string().email('올바른 이메일을 입력하세요.'),
  password: z.string().min(8, '비밀번호는 8자 이상이어야 합니다.').max(128, '비밀번호는 128자 이하로 입력하세요.'),
});

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverFieldErrors, setServerFieldErrors] = useState<Record<string, string>>({});
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: SignupFormValues) => {
    setError(null);
    setServerFieldErrors({});
    try {
      const res = await authApi.signup(values);
      login(res.access_token, res.user);
      navigate('/user/resumes');
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
      } else {
        setError(apiErr.message ?? '회원가입에 실패했습니다.');
      }
    }
  };

  const inputClass = (field: string) =>
    `pl-10 ${
      errors[field as keyof SignupFormValues] || serverFieldErrors[field]
        ? 'border-m-danger focus:border-m-danger focus:ring-m-danger'
        : ''
    }`;

  const fieldError = (field: keyof SignupFormValues) =>
    errors[field]?.message || serverFieldErrors[field];

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

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            {/* Name */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">이름</label>
              <div className="relative">
                <Input
                  placeholder="홍길동"
                  autoComplete="name"
                  className={inputClass('name')}
                  {...register('name')}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="user" size={16} />
                </div>
              </div>
              {fieldError('name') && <p className="mt-1 text-[12px] text-m-danger">{fieldError('name')}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">이메일</label>
              <div className="relative">
                <Input
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  className={inputClass('email')}
                  {...register('email')}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
                  <Icon name="mail" size={16} />
                </div>
              </div>
              {fieldError('email') && <p className="mt-1 text-[12px] text-m-danger">{fieldError('email')}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-[12px] font-medium text-m-muted mb-1.5">비밀번호</label>
              <div className="relative">
                <Input
                  type={showPw ? 'text' : 'password'}
                  placeholder="8자 이상"
                  autoComplete="new-password"
                  className={`${inputClass('password')} pr-10`}
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
              {fieldError('password') && <p className="mt-1 text-[12px] text-m-danger">{fieldError('password')}</p>}
            </div>

            {/* Global error */}
            {error && <Alert variant="danger">{error}</Alert>}

            <Button
              type="submit"
              disabled={isSubmitting}
              className="mt-1"
            >
              {isSubmitting ? '가입 중...' : '시작하기'}
              {!isSubmitting && <Icon name="arrow" size={16} />}
            </Button>
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
