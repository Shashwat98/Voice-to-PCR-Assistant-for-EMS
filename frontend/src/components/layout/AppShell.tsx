import type { ReactNode } from 'react';
import { OfflineBanner } from './OfflineBanner';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <OfflineBanner />
      {children}
    </div>
  );
}
