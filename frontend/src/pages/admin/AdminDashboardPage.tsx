export default function AdminDashboardPage() {
  const stats = [
    { label: '전체 사용자', value: '1,284', delta: '+12', icon: '👤' },
    { label: '활성 카테고리', value: '8', delta: '+1', icon: '📁' },
    { label: '총 게시글', value: '142', delta: '+5', icon: '📄' },
    { label: '오늘 가입', value: '24', delta: '+8', icon: '✨' },
  ];

  return (
    <div className="p-6">
      <h1 className="text-[20px] font-bold mb-1" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>대시보드</h1>
      <p className="text-[13px] mb-6" style={{ color: '#475569' }}>JobFit AI 서비스 현황을 한눈에 확인하세요.</p>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-xl p-4 border" style={{ borderColor: '#e2e8f0' }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-[12px] font-medium" style={{ color: '#475569' }}>{s.label}</p>
              <span className="text-[18px]">{s.icon}</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[24px] font-bold font-mono" style={{ color: '#0f172a', letterSpacing: '-.02em' }}>{s.value}</span>
              <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded" style={{ background: '#f0fdf4', color: '#16a34a' }}>{s.delta}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Notice */}
      <div className="rounded-xl p-4 border" style={{ background: '#eff6ff', borderColor: '#bfdbfe' }}>
        <p className="text-[13px] font-semibold mb-1" style={{ color: '#1e40af' }}>관리자 안내</p>
        <p className="text-[13px]" style={{ color: '#3b82f6' }}>
          카테고리와 Q&A 게시글 관리는 왼쪽 메뉴에서 접근하세요. CRUD 상세 기능은 백엔드 API 연결 후 순차적으로 활성화됩니다.
        </p>
      </div>
    </div>
  );
}
