'use client';

import { RequireAuth } from '../../components/auth/RequireAuth';
import UserLayout from '../../components/layout/UserLayout';

export default function UserRouteLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <UserLayout>{children}</UserLayout>
    </RequireAuth>
  );
}
