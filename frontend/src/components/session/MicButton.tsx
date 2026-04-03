import { Mic, MicOff, Loader2 } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

interface MicButtonProps {
  onToggle?: () => void;
}

export function MicButton({ onToggle }: MicButtonProps) {
  const micStatus = useUIStore((s) => s.micStatus);

  const isActive = micStatus === 'active';
  const isProcessing = micStatus === 'processing';

  return (
    <button
      onClick={onToggle}
      className={`relative flex h-12 w-12 items-center justify-center rounded-full transition-all
        ${isActive ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'}
        ${isProcessing ? 'cursor-wait opacity-75' : 'cursor-pointer'}
      `}
      title={isActive ? 'Stop recording' : isProcessing ? 'Processing...' : 'Start recording'}
    >
      {isActive && (
        <span className="absolute inset-0 animate-ping rounded-full bg-red-600 opacity-40" />
      )}
      {isProcessing ? (
        <Loader2 size={20} className="animate-spin text-white" />
      ) : isActive ? (
        <Mic size={20} className="text-white" />
      ) : (
        <MicOff size={20} className="text-gray-300" />
      )}
    </button>
  );
}
