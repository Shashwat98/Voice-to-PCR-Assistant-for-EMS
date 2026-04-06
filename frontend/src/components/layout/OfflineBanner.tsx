import { WifiOff } from 'lucide-react';
import { useSessionStore } from '../../store/sessionStore';

export function OfflineBanner() {
  const isOffline = useSessionStore((s) => s.isOffline);
  if (!isOffline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 bg-red-600 py-2 text-sm font-medium text-white">
      <WifiOff size={14} />
      Connection lost — attempting to reconnect
    </div>
  );
}
