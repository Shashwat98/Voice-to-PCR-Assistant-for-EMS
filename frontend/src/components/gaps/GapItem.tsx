import { ArrowRight } from 'lucide-react';
import type { GapItem as GapItemType } from '../../types/session';
import { getLabel } from '../../utils/fieldHelpers';
import { useUIStore } from '../../store/uiStore';

interface GapItemProps {
  gap: GapItemType;
  onJump: (fieldKey: string) => void;
}

export function GapItem({ gap, onJump }: GapItemProps) {
  const setEditingField = useUIStore((s) => s.setEditingField);

  const handleJump = () => {
    setEditingField(gap.field_name);
    onJump(gap.field_name);
  };

  return (
    <div className="flex items-start justify-between gap-3 py-2">
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-200">{getLabel(gap.field_name)}</p>
        <p className="text-xs text-gray-500 italic">{gap.prompt}</p>
      </div>
      <button
        onClick={handleJump}
        className="flex shrink-0 items-center gap-1 rounded-lg bg-gray-800 px-2.5 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
      >
        Go <ArrowRight size={11} />
      </button>
    </div>
  );
}
