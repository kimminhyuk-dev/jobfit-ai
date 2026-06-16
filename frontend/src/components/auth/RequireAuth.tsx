'use client';

import { useRouter } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';
import { useAuth } from '../../stores/authContext';

function FullPageSpinner() {
  return (
    <div className="flex h-screen items-center justify-center bg-m-bg">
      <div className="w-8 h-8 rounded-full border-2 border-m-primary border-t-transparent animate-spin" />
    </div>
  );
}

export function RequireAuth({
  children,
  adminOnly = false,
  allowedRoles,
}: {
  children: ReactNode;
  adminOnly?: boolean;
  allowedRoles?: Array<'USER' | 'COMPANY' | 'ADMIN'>;
}) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const isRoleBlocked =
    !!user &&
    ((adminOnly && user.role !== 'ADMIN') ||
      (allowedRoles !== undefined && !allowedRoles.includes(user.role)));
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
    router.replace(
      !user
        ? '/login'
        : user.role === 'ADMIN'
          ? '/admin/dashboard'
          : user.role === 'COMPANY'
            ? '/company/dashboard'
            : '/user/dashboard',
    );
  }, [loading, router, user]);

  return <FullPageSpinner />;
}
