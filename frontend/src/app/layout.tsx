import type { Metadata } from 'next';
import ThemeRegistry from '@/theme/ThemeRegistry';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'SumireBot Dashboard',
  description: 'Manage your Discord server with SumireBot',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <ThemeRegistry>
          <Providers>{children}</Providers>
        </ThemeRegistry>
      </body>
    </html>
  );
}
