'use client';

import { useState } from 'react';
import Icon from '../../components/ui/Icon';
import { useAuth } from '../../stores/authContext';

type PlanKey = 'free' | 'pro' | 'enterprise';
type BillingCycle = 'monthly' | 'yearly';

interface Plan {
  key: PlanKey;
  name: string;
  monthlyPrice: number;
  yearlyPrice: number;
  description: string;
  features: string[];
  cta: string;
  highlighted: boolean;
}

const plans: Plan[] = [
  {
    key: 'free',
    name: 'Free',
    monthlyPrice: 0,
    yearlyPrice: 0,
    description: '취업 준비를 시작하는 분께',
    features: [
      '이력서 업로드 1개',
      '채용공고 조회 (공공기관)',
      '기본 이력서 파싱',
      'Q&A 게시판 열람',
    ],
    cta: '현재 플랜',
    highlighted: false,
  },
  {
    key: 'pro',
    name: 'Pro',
    monthlyPrice: 9900,
    yearlyPrice: 7900,
    description: '적극적으로 취업 활동 중인 분께',
    features: [
      '이력서 업로드 무제한',
      'AI 매칭 분석 무제한',
      '강점·약점 상세 리포트',
      '채용공고 알림 (매일)',
      '우선 매칭 순위 부여',
      '지원 현황 관리',
    ],
    cta: '14일 무료 체험',
    highlighted: true,
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    monthlyPrice: 0,
    yearlyPrice: 0,
    description: '기업·채용 담당자·팀 단위',
    features: [
      'Pro 기능 전체 포함',
      '팀원 계정 관리',
      '후보자 풀 관리',
      '대량 이력서 분석',
      '전담 고객 지원',
      '커스텀 API 연동',
    ],
    cta: '문의하기',
    highlighted: false,
  },
];

interface CardForm {
  number: string;
  expiry: string;
  cvc: string;
  name: string;
}

export default function PaymentPage() {
  const { user } = useAuth();
  const [cycle, setCycle] = useState<BillingCycle>('monthly');
  const [selectedPlan, setSelectedPlan] = useState<PlanKey | null>(null);
  const [showPayForm, setShowPayForm] = useState(false);
  const [card, setCard] = useState<CardForm>({ number: '', expiry: '', cvc: '', name: '' });
  const [payError, setPayError] = useState('');
  const [paySuccess, setPaySuccess] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const currentPlan = plans.find((p) => p.key === 'free')!;

  function formatCardNumber(v: string) {
    const digits = v.replace(/\D/g, '').slice(0, 16);
    return digits.replace(/(.{4})/g, '$1 ').trim();
  }

  function formatExpiry(v: string) {
    const digits = v.replace(/\D/g, '').slice(0, 4);
    if (digits.length >= 3) return `${digits.slice(0, 2)} / ${digits.slice(2)}`;
    return digits;
  }

  function handleCardChange(field: keyof CardForm, raw: string) {
    let val = raw;
    if (field === 'number') val = formatCardNumber(raw);
    if (field === 'expiry') val = formatExpiry(raw);
    if (field === 'cvc') val = raw.replace(/\D/g, '').slice(0, 3);
    setCard((prev) => ({ ...prev, [field]: val }));
    setPayError('');
  }

  function handlePaySubmit(e: React.FormEvent) {
    e.preventDefault();
    setPayError('');
    const digits = card.number.replace(/\s/g, '');
    if (digits.length < 16) { setPayError('카드 번호를 올바르게 입력하세요.'); return; }
    if (card.expiry.replace(/\s\/\s/, '').length < 4) { setPayError('유효기간을 입력하세요.'); return; }
    if (card.cvc.length < 3) { setPayError('CVC를 입력하세요.'); return; }
    if (!card.name.trim()) { setPayError('카드 소유자 이름을 입력하세요.'); return; }

    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setPaySuccess(true);
    }, 1500);
  }

  const price = (plan: Plan) =>
    cycle === 'monthly' ? plan.monthlyPrice : plan.yearlyPrice;

  return (
    <div className="p-6 max-w-[1000px] mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[22px] font-bold text-m-text tracking-tight">요금제 & 결제</h1>
        <p className="text-[14px] text-m-muted mt-1">
          현재 플랜:{' '}
          <span className="font-semibold text-m-text">{currentPlan.name}</span>
          {' '}·{' '}
          <span className="text-m-success font-medium">무료</span>
        </p>
      </div>

      {/* Billing cycle toggle */}
      <div className="flex justify-center mb-7">
        <div className="inline-flex items-center gap-1 bg-m-surface-alt rounded-xl p-1">
          <button
            onClick={() => setCycle('monthly')}
            className={`h-9 px-4 rounded-lg text-[13px] font-medium transition-colors ${
              cycle === 'monthly' ? 'bg-m-surface text-m-text shadow-sm' : 'text-m-muted hover:text-m-text'
            }`}
          >
            월간
          </button>
          <button
            onClick={() => setCycle('yearly')}
            className={`h-9 px-4 rounded-lg text-[13px] font-medium transition-colors flex items-center gap-1.5 ${
              cycle === 'yearly' ? 'bg-m-surface text-m-text shadow-sm' : 'text-m-muted hover:text-m-text'
            }`}
          >
            연간
            <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded-full bg-m-success-soft text-m-success">
              20% 할인
            </span>
          </button>
        </div>
      </div>

      {/* Plan cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {plans.map((plan) => {
          const planPrice = price(plan);
          const isHighlighted = plan.highlighted;
          const isEnterprise = plan.key === 'enterprise';

          return (
            <div
              key={plan.key}
              className={`relative rounded-xl border p-5 flex flex-col transition-all ${
                isHighlighted
                  ? 'border-m-primary bg-m-primary-soft ring-2 ring-m-primary ring-offset-2'
                  : 'border-m-border bg-m-surface hover:border-m-primary/40'
              }`}
            >
              {isHighlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-m-primary text-white text-[11px] font-bold">
                  가장 인기
                </span>
              )}

              <div className="mb-3">
                <p className="text-[14px] font-bold text-m-text">{plan.name}</p>
                <p className="text-[12px] text-m-muted mt-0.5">{plan.description}</p>
              </div>

              <div className="mb-4">
                {isEnterprise ? (
                  <p className="text-[22px] font-bold text-m-text">문의</p>
                ) : planPrice === 0 ? (
                  <p className="text-[22px] font-bold text-m-text">무료</p>
                ) : (
                  <div className="flex items-baseline gap-1">
                    <span className="text-[22px] font-bold text-m-text">
                      {planPrice.toLocaleString()}원
                    </span>
                    <span className="text-[12px] text-m-muted">/ 월</span>
                  </div>
                )}
                {cycle === 'yearly' && !isEnterprise && planPrice > 0 && (
                  <p className="text-[11px] text-m-success mt-0.5">연간 결제 시 월 {planPrice.toLocaleString()}원</p>
                )}
              </div>

              <ul className="flex flex-col gap-2 mb-5 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-[12px] text-m-muted">
                    <Icon name="check" size={13} color="#22c55e" strokeWidth={2.5} className="mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => {
                  if (plan.key === 'free') return;
                  if (isEnterprise) return;
                  setSelectedPlan(plan.key);
                  setShowPayForm(true);
                  setPaySuccess(false);
                  setCard({ number: '', expiry: '', cvc: '', name: '' });
                }}
                disabled={plan.key === 'free'}
                className={`h-9 rounded-lg text-[13px] font-semibold transition-colors ${
                  plan.key === 'free'
                    ? 'bg-m-surface-alt text-m-subtle cursor-default'
                    : isHighlighted
                    ? 'bg-m-primary text-white hover:bg-m-primary-hover'
                    : isEnterprise
                    ? 'bg-m-surface border border-m-border text-m-muted hover:bg-m-surface-alt'
                    : 'bg-m-text text-white hover:opacity-80'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          );
        })}
      </div>

      {/* Payment form */}
      {showPayForm && selectedPlan && !paySuccess && (
        <div className="bg-m-surface border border-m-border rounded-xl p-6 max-w-lg">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Icon name="credit-card" size={18} color="#2563eb" />
              <h2 className="text-[15px] font-semibold text-m-text">결제 정보 입력</h2>
            </div>
            <button
              onClick={() => setShowPayForm(false)}
              className="text-m-subtle hover:text-m-muted transition-colors"
            >
              <Icon name="x" size={16} />
            </button>
          </div>

          <div className="mb-4 p-3 rounded-lg bg-m-surface-alt flex items-center justify-between">
            <div>
              <p className="text-[12px] text-m-muted">선택한 플랜</p>
              <p className="text-[14px] font-bold text-m-text">
                {plans.find((p) => p.key === selectedPlan)?.name} ·{' '}
                {cycle === 'yearly' ? '연간' : '월간'}
              </p>
            </div>
            <p className="text-[16px] font-bold text-m-primary">
              {(price(plans.find((p) => p.key === selectedPlan)!)).toLocaleString()}원/월
            </p>
          </div>

          <form onSubmit={handlePaySubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">카드 번호</label>
              <input
                value={card.number}
                onChange={(e) => handleCardChange('number', e.target.value)}
                placeholder="0000 0000 0000 0000"
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[12px] font-medium text-m-muted block mb-1.5">유효기간</label>
                <input
                  value={card.expiry}
                  onChange={(e) => handleCardChange('expiry', e.target.value)}
                  placeholder="MM / YY"
                  className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                />
              </div>
              <div>
                <label className="text-[12px] font-medium text-m-muted block mb-1.5">CVC</label>
                <input
                  value={card.cvc}
                  onChange={(e) => handleCardChange('cvc', e.target.value)}
                  placeholder="000"
                  className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
                />
              </div>
            </div>
            <div>
              <label className="text-[12px] font-medium text-m-muted block mb-1.5">카드 소유자 이름</label>
              <input
                value={card.name}
                onChange={(e) => handleCardChange('name', e.target.value)}
                placeholder={user?.name ?? '홍길동'}
                className="w-full h-10 px-3 rounded-lg border border-m-border text-[13px] text-m-text focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
              />
            </div>

            {payError && (
              <p className="text-[12px] text-red-600 bg-red-50 px-3 py-2 rounded-lg">{payError}</p>
            )}

            <p className="text-[11px] text-m-subtle">
              실제 결제가 발생하지 않는 데모입니다. 카드 정보는 서버에 전송되지 않습니다.
            </p>

            <button
              type="submit"
              disabled={isProcessing}
              className="h-10 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  결제 처리 중...
                </>
              ) : (
                <>
                  <Icon name="credit-card" size={14} />
                  결제하기
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Success */}
      {paySuccess && (
        <div className="bg-m-surface border border-green-200 rounded-xl p-6 max-w-lg flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-3">
            <Icon name="check" size={22} color="#16a34a" strokeWidth={2.5} />
          </div>
          <h3 className="text-[16px] font-bold text-m-text mb-1">결제 완료!</h3>
          <p className="text-[13px] text-m-muted mb-4">
            {plans.find((p) => p.key === selectedPlan)?.name} 플랜이 활성화되었습니다.
          </p>
          <button
            onClick={() => { setShowPayForm(false); setPaySuccess(false); setSelectedPlan(null); }}
            className="h-9 px-5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors"
          >
            확인
          </button>
        </div>
      )}
    </div>
  );
}
