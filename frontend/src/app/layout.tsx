import type { Metadata } from 'next';
import Providers from './providers';
import '../styles/global.css';

export const metadata: Metadata = {
  title: 'JobFit AI',
  description: 'AI 기반 이력서-채용공고 매칭 플랫폼',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
