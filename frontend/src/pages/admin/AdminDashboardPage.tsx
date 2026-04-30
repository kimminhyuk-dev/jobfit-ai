import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import Icon from '../../components/ui/Icon';

interface StatCard {
  label: string;
  value: number | string;
  icon: 'user' | 'layers' | 'file' | 'sparkle' | 'briefcase';
  iconColor: string;
  iconBg: string;
}

function buildStats(data: {
  total_users: number;
  active_categories: number;
  total_posts: number;
  today_signups: number;
  total_jobs: number;
}): StatCard[] {
  return [
    { label: '전체 사용자', value: data.total_users.toLocaleString(), icon: 'user', iconColor: '#6366f1', iconBg: '#eef2ff' },
    { label: '활성 카테고리', value: data.active_categories.toLocaleString(), icon: 'layers', iconColor: '#f59e0b', iconBg: '#fffbeb' },
    { label: '총 게시글', value: data.total_posts.toLocaleString(), icon: 'file', iconColor: '#64748b', iconBg: '#f1f5f9' },
    { label: '오늘 가입', value: data.today_signups.toLocaleString(), icon: 'sparkle', iconColor: '#f59e0b', iconBg: '#fffbeb' },
    { label: '채용공고', value: data.total_jobs.toLocaleString(), icon: 'briefcase', iconColor: '#10b981', iconBg: '#f0fdf4' },
  ];
}

export default function AdminDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
  });

  const stats: StatCard[] = data ? buildStats(data) : [];

  return (
    <div className="p-6">
      <h1 className="text-[20px] font-bold mb-1" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>대시보드</h1>
      <p className="text-[13px] mb-6" style={{ color: '#475569' }}>JobFit AI 서비스 현황을 한눈에 확인하세요.</p>

      {isError && (
        <div className="mb-4 rounded-xl p-3 border text-[13px]" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' }}>
          통계 데이터를 불러오지 못했습니다.
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border animate-pulse" style={{ borderColor: '#e2e8f0' }}>
                <div className="h-3 w-20 rounded mb-3" style={{ background: '#e2e8f0' }} />
                <div className="h-7 w-14 rounded" style={{ background: '#e2e8f0' }} />
              </div>
            ))
          : stats.map((s) => (
              <div key={s.label} className="bg-white rounded-xl p-4 border" style={{ borderColor: '#e2e8f0' }}>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-[12px] font-medium" style={{ color: '#475569' }}>{s.label}</p>
                  <span
                    className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: s.iconBg }}
                  >
                    <Icon name={s.icon} size={14} color={s.iconColor} strokeWidth={2} />
                  </span>
                </div>
                <span className="text-[24px] font-bold font-mono" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>
                  {s.value}
                </span>
              </div>
            ))}
      </div>

      {/* Notice */}
      <div className="rounded-xl p-4 border" style={{ background: '#eff6ff', borderColor: '#bfdbfe' }}>
        <p className="text-[13px] font-semibold mb-1" style={{ color: '#1e40af' }}>관리자 안내</p>
        <p className="text-[13px]" style={{ color: '#3b82f6' }}>
          카테고리, Q&A 게시글, 채용공고 관리는 왼쪽 메뉴에서 접근하세요.
        </p>
      </div>
    </div>
  );
}
