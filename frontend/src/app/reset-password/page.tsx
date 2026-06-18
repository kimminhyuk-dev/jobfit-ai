import AccountRecoveryPage from '../../screens/AccountRecoveryPage';
import type { RecoveryAudience } from '../../components/auth/AccountRecoveryForm';

interface ResetPasswordProps {
  searchParams?: Promise<{
    audience?: string | string[];
  }>;
}

function getInitialAudience(value: string | string[] | undefined): RecoveryAudience {
  return value === 'company' ? 'company' : 'user';
}

export default async function ResetPassword({ searchParams }: ResetPasswordProps) {
  const params = await searchParams;
  return (
    <AccountRecoveryPage
      mode="reset-password"
      initialAudience={getInitialAudience(params?.audience)}
    />
  );
}
