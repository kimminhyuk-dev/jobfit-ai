'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import Icon from '../ui/Icon';
import { useAuth } from '../../stores/authContext';

const navItems = [
  { to: '/user/dashboard', label: '홈', icon: 'home' as const },
  { to: '/user/jobs', label: '추천 공고', icon: 'briefcase' as const, badge: 28 },
  { to: '/user/mock-jobs', label: 'IT 채용 (Mock)', icon: 'layers' as const },
  { to: '/user/matches', label: 'AI 매칭', icon: 'sparkle' as const },
  { to: '/user/resumes', label: '내 이력서', icon: 'file' as const },
];

export default function UserLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const initials = user?.name?.slice(0, 2) ?? '??';

  return (
    <div className="flex h-screen bg-m-bg overflow-hidden">
      {/* Sidebar */}
      <aside
        className="flex flex-col flex-shrink-0 bg-m-surface border-r border-m-border transition-all duration-200"
        style={{ width: collapsed ? 64 : 220 }}
      >
        {/* Logo */}
        <div
          className="flex items-center h-14 border-b border-m-border flex-shrink-0 px-4 gap-2.5"
          style={{ justifyContent: collapsed ? 'center' : 'flex-start', padding: collapsed ? 0 : undefined }}
        >
          <div className="w-7 h-7 rounded-lg bg-m-primary flex items-center justify-center text-white flex-shrink-0">
            <Icon name="target" size={15} />
          </div>
          {!collapsed && (
            <span className="font-bold text-[15px] text-m-text tracking-tight">JobFit AI</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 flex flex-col gap-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.to;

            return (
            <Link
              key={item.to}
              href={item.to}
              title={item.label}
              className={`flex items-center h-9 rounded-lg text-[13px] font-medium transition-colors gap-2.5 ${
                  collapsed ? 'justify-center px-0' : 'px-3'
                } ${
                  isActive
                    ? 'bg-m-primary-soft text-m-primary font-semibold'
                    : 'text-m-muted hover:bg-m-surface-alt hover:text-m-text'
                }`}
            >
              <Icon name={item.icon} size={16} />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[11px] px-1.5 py-0.5 rounded-full font-semibold font-mono ${
                        isActive
                          ? 'bg-m-primary text-white'
                          : 'bg-m-surface-alt text-m-subtle'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
            );
          })}
        </nav>

        {/* Upgrade banner */}
        {!collapsed && (
          <div className="mx-3 mb-3 p-3.5 rounded-xl bg-m-primary-soft border border-m-primary/10">
            <p className="text-[12px] font-semibold text-m-primary">Pro로 업그레이드</p>
            <p className="text-[11px] text-m-muted mt-1 leading-snug">
              무제한 AI 분석과 우선 매칭을 받아보세요.
            </p>
            <button className="mt-2.5 h-7 w-full rounded-md bg-m-primary text-white text-[12px] font-semibold hover:bg-m-primary-hover transition-colors">
              14일 무료 체험
            </button>
          </div>
        )}

        {/* User + collapse */}
        <div
          className="p-3 border-t border-m-border flex items-center gap-2.5"
          style={{ justifyContent: collapsed ? 'center' : 'flex-start' }}
        >
          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-800 text-[12px] font-bold flex-shrink-0">
            {initials}
          </div>
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-semibold truncate text-m-text">{user?.name ?? '사용자'}</p>
                <p className="text-[11px] text-m-subtle">구직 활동 중</p>
              </div>
              <button
                onClick={handleLogout}
                title="로그아웃"
                className="text-m-subtle hover:text-m-muted transition-colors p-1"
              >
                <Icon name="logout" size={15} />
              </button>
            </>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed((v) => !v)}
          className="flex items-center justify-center h-9 border-t border-m-border text-m-subtle hover:text-m-muted hover:bg-m-surface-alt transition-colors text-[11px] gap-1"
        >
          <Icon name={collapsed ? 'chevron' : 'chevron-left'} size={14} />
          {!collapsed && <span>접기</span>}
        </button>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 flex items-center gap-3 px-6 border-b border-m-border bg-m-surface flex-shrink-0">
          <div className="relative flex-1 max-w-xs">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-m-subtle">
              <Icon name="search" size={14} />
            </div>
            <input
              placeholder="회사, 직무, 스킬 검색"
              className="w-full h-9 pl-9 pr-3 rounded-lg border border-m-border bg-m-surface-alt text-[13px] text-m-text placeholder:text-m-subtle focus:outline-none focus:border-m-primary focus:ring-1 focus:ring-m-primary"
            />
          </div>
          <div className="flex-1" />
          <button className="relative w-9 h-9 flex items-center justify-center rounded-lg border border-m-border bg-m-surface text-m-muted hover:bg-m-surface-alt transition-colors">
            <Icon name="bell" size={16} />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-m-danger rounded-full border border-m-surface" />
          </button>
          <Link
            href="/user/resumes"
            className="h-9 px-3.5 flex items-center gap-1.5 rounded-lg bg-m-primary text-white text-[13px] font-semibold hover:bg-m-primary-hover transition-colors"
          >
            <Icon name="upload" size={14} />
            새 이력서
          </Link>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
}
