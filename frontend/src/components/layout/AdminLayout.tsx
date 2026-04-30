import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import Icon from '../ui/Icon';
import { useAuth } from '../../stores/authContext';

const adminNav = [
  { to: '/admin/dashboard', label: '대시보드', icon: 'home' as const },
  { to: '/admin/categories', label: '카테고리', icon: 'layers' as const },
  { to: '/admin/posts', label: 'Q&A 게시글', icon: 'file' as const },
  { to: '/admin/jobs', label: '채용공고', icon: 'briefcase' as const },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#f6f8fb', fontFamily: 'Pretendard, -apple-system, sans-serif' }}>
      {/* Classic SaaS Sidebar */}
      <aside className="w-56 flex flex-col shrink-0 bg-white border-r" style={{ borderColor: '#e2e8f0' }}>
        {/* Logo */}
        <div className="h-14 flex items-center gap-2 px-4 border-b" style={{ borderColor: '#e2e8f0' }}>
          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white" style={{ background: '#2563eb' }}>
            <Icon name="target" size={15} />
          </div>
          <span className="font-bold text-[15px]" style={{ color: '#0f172a' }}>JobFit Admin</span>
        </div>

        {/* Role badge */}
        <div className="px-4 py-2 border-b" style={{ borderColor: '#e2e8f0' }}>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: '#eff6ff', color: '#2563eb' }}>
            관리자
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 flex flex-col gap-0.5">
          {adminNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center h-9 px-3 rounded-lg text-[13px] gap-2.5 transition-colors ${
                  isActive
                    ? 'font-semibold'
                    : 'font-medium hover:bg-slate-50'
                }`
              }
              style={({ isActive }) => ({
                background: isActive ? '#eff6ff' : undefined,
                color: isActive ? '#2563eb' : '#475569',
              })}
            >
              {({ isActive }) => (
                <>
                  <Icon name={item.icon} size={16} color={isActive ? '#2563eb' : '#94a3b8'} />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-3 border-t flex items-center gap-2.5" style={{ borderColor: '#e2e8f0' }}>
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-800 text-[12px] font-bold shrink-0">
            {user?.name?.slice(0, 2) ?? 'AD'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold truncate" style={{ color: '#0f172a' }}>{user?.name ?? '관리자'}</p>
            <p className="text-[11px]" style={{ color: '#94a3b8' }}>ADMIN</p>
          </div>
          <button onClick={handleLogout} title="로그아웃" className="text-slate-400 hover:text-slate-600 p-1">
            <Icon name="logout" size={14} />
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 flex items-center gap-4 px-6 bg-white border-b shrink-0" style={{ borderColor: '#e2e8f0' }}>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#94a3b8' }}>
              <Icon name="search" size={14} />
            </div>
            <input
              placeholder="검색"
              className="h-9 pl-9 pr-3 rounded-lg text-[13px] focus:outline-none"
              style={{ width: 240, border: '1px solid #e2e8f0', background: '#f1f5f9', color: '#0f172a' }}
            />
          </div>
          <div className="flex-1" />
          <span className="text-[12px] font-medium px-3 py-1 rounded-full" style={{ background: '#fef9c3', color: '#92400e' }}>
            관리자 모드
          </span>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto scrollbar-thin">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
