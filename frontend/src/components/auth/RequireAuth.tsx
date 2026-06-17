'use client';

import { useRouter } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';
import { useAuth } from '../../stores/authContext';

type KnownRole = 'USER' | 'COMPANY' | 'ADMIN';

function FullPageSpinner() {
  return (
    <div className="flex h-screen items-center justify-center bg-m-bg">
      <div className="w-8 h-8 rounded-full border-2 border-m-primary border-t-transparent animate-spin" />
    </div>
  );
}

function normalizedRole(role: string | undefined): KnownRole | null {
  const value = role?.trim().toUpperCase();
  return value === 'USER' || value === 'COMPANY' || value === 'ADMIN' ? value : null;
}

export function RequireAuth({
  children,
  adminOnly = false,
  allowedRoles,
}: {
  children: ReactNode;
  adminOnly?: boolean;
  allowedRoles?: KnownRole[];
}) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const role = normalizedRole(user?.role);
  const isRoleBlocked =
    !!user &&
    ((adminOnly && role !== 'ADMIN') ||
      (allowedRoles !== undefined && (role === null || !allowedRoles.includes(role))));
  const redirectTo = !user ? '/login' : isRoleBlocked ? '/user/dashboard' : null;

  useEffect(() => {
    if (!loading && redirectTo) router.replace(redirectTo);
  }, [loading, redirectTo, router]);

  if (loading || redirectTo) return <FullPageSpinner />;

  return <>{children}</>;
}

export function RootRedirect() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    const role = normalizedRole(user?.role);
    router.replace(
      !user
        ? '/login'
        : role === 'ADMIN'
          ? '/admin/dashboard'
          : role === 'COMPANY'
            ? '/company/dashboard'
            : '/user/dashboard',
    );
  }, [loading, router, user]);

  return <FullPageSpinner />;
}
