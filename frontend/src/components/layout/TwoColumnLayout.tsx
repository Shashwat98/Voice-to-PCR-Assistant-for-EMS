import type { ReactNode } from 'react';

interface TwoColumnLayoutProps {
  left: ReactNode;
  right: ReactNode;
}

export function TwoColumnLayout({ left, right }: TwoColumnLayoutProps) {
  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Left: transcript */}
      <div className="hidden w-[400px] shrink-0 flex-col border-r border-gray-800 lg:flex">
        {left}
      </div>
      {/* Right: PCR form */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {right}
      </div>
    </div>
  );
}
