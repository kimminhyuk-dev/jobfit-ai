'use client';

import { RequireAuth } from '../../components/auth/RequireAuth';
import AdminLayout from '../../components/layout/AdminLayout';

export default function AdminRouteLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth adminOnly>
      <AdminLayout>{children}</AdminLayout>
    </RequireAuth>
  );
}
