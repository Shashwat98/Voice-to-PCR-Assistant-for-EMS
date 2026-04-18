import { AlertTriangle } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

export function GapBadge() {
  const { gaps, toggleGapPanel, gapPanelOpen } = useUIStore();

  const mandatoryCount = gaps?.missing_mandatory.length ?? 0;
  const requiredCount = gaps?.missing_required.length ?? 0;
  const total = mandatoryCount + requiredCount;

  if (total === 0) return null;

  return (
    <button
      onClick={toggleGapPanel}
      className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors
        ${gapPanelOpen
          ? 'bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/40'
          : mandatoryCount > 0
          ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30'
          : 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30'
        }`}
      title="Show missing fields"
    >
      <AlertTriangle size={14} />
      {total} gap{total !== 1 ? 's' : ''}
    </button>
  );
}
