'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import Icon from '../ui/Icon';
import { useAuth } from '../../stores/authContext';

const adminNav = [
  { to: '/admin/dashboard', label: '대시보드', icon: 'home' as const },
  { to: '/admin/categories', label: '카테고리', icon: 'layers' as const },
  { to: '/admin/posts', label: 'Q&A 게시글', icon: 'file' as const },
  { to: '/admin/jobs', label: '채용공고', icon: 'briefcase' as const },
  { to: '/admin/mock-jobs', label: 'Mock 공고', icon: 'grid' as const },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#f1f5f9', fontFamily: 'Pretendard, -apple-system, sans-serif' }}>
      {/* Admin Sidebar — 진한 네이비 배경으로 사용자 영역과 명확히 구분 */}
      <aside className="w-56 flex flex-col shrink-0 border-r" style={{ background: '#0f172a', borderColor: '#1e293b' }}>
        {/* Logo + Admin badge */}
        <div className="h-14 flex items-center gap-2.5 px-4 border-b" style={{ borderColor: '#1e293b' }}>
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: '#2563eb' }}>
            <Icon name="target" size={15} color="#fff" />
          </div>
          <div>
            <span className="font-bold text-[14px] text-white">JobFit</span>
            <span className="ml-1 text-[11px] font-bold px-1.5 py-0.5 rounded" style={{ background: '#dc2626', color: '#fff' }}>
              ADMIN
            </span>
          </div>
        </div>

        {/* Admin identity */}
        <div className="px-4 py-3 border-b" style={{ borderColor: '#1e293b' }}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold shrink-0" style={{ background: '#1e40af', color: '#bfdbfe' }}>
              {user?.name?.slice(0, 2) ?? 'AD'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-semibold truncate text-white">{user?.name ?? '관리자'}</p>
              <p className="text-[10px] font-medium" style={{ color: '#64748b' }}>{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 flex flex-col gap-0.5">
          <p className="text-[10px] font-semibold px-2 mb-1.5 tracking-widest" style={{ color: '#475569' }}>
            관리 메뉴
          </p>
          {adminNav.map((item) => {
            const isActive = pathname === item.to;
            return (
              <Link
                key={item.to}
                href={item.to}
                className="flex items-center h-9 px-3 rounded-lg text-[13px] gap-2.5 transition-colors font-medium"
                style={{
                  background: isActive ? '#1e3a8a' : 'transparent',
                  color: isActive ? '#93c5fd' : '#94a3b8',
                }}
                onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = '#1e293b'; }}
                onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
              >
                <Icon name={item.icon} size={16} color={isActive ? '#93c5fd' : '#64748b'} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User switch + logout */}
        <div className="p-3 border-t flex flex-col gap-1" style={{ borderColor: '#1e293b' }}>
          <Link
            href="/user/dashboard"
            className="flex items-center gap-2 h-8 px-3 rounded-lg text-[12px] font-medium transition-colors"
            style={{ color: '#64748b' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#1e293b'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
          >
            <Icon name="user" size={13} color="#64748b" />
            사용자 화면으로
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 h-8 px-3 rounded-lg text-[12px] font-medium transition-colors text-left w-full"
            style={{ color: '#64748b' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#1e293b'; (e.currentTarget as HTMLElement).style.color = '#f87171'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = '#64748b'; }}
          >
            <Icon name="logout" size={13} color="currentColor" />
            로그아웃
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar — 빨간 좌측 보더로 관리자 모드 표시 */}
        <header
          className="h-14 flex items-center gap-4 px-6 bg-white shrink-0"
          style={{ borderBottom: '1px solid #e2e8f0', borderLeft: '3px solid #dc2626' }}
        >
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
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-[12px] font-bold tracking-wide" style={{ color: '#dc2626' }}>
              ADMIN MODE
            </span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
}
