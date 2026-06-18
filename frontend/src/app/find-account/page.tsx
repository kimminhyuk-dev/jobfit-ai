import AccountRecoveryPage from '../../screens/AccountRecoveryPage';
import type { RecoveryAudience } from '../../components/auth/AccountRecoveryForm';

interface FindAccountProps {
  searchParams?: Promise<{
    audience?: string | string[];
  }>;
}

function getInitialAudience(value: string | string[] | undefined): RecoveryAudience {
  return value === 'company' ? 'company' : 'user';
}

export default async function FindAccount({ searchParams }: FindAccountProps) {
  const params = await searchParams;
  return (
    <AccountRecoveryPage
      mode="find-email"
      initialAudience={getInitialAudience(params?.audience)}
    />
  );
}
