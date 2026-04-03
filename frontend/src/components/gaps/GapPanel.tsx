import { X } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { GapItem } from './GapItem';

interface GapPanelProps {
  onJumpToField: (fieldKey: string) => void;
}

export function GapPanel({ onJumpToField }: GapPanelProps) {
  const { gapPanelOpen, setGapPanelOpen, gaps } = useUIStore();

  if (!gapPanelOpen || !gaps) return null;

  const hasMandatory = gaps.missing_mandatory.length > 0;
  const hasRequired = gaps.missing_required.length > 0;
  const hasRecommended = gaps.missing_recommended.length > 0;

  if (!hasMandatory && !hasRequired && !hasRecommended) return null;

  return (
    <div className="border-b border-gray-800 bg-gray-900">
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Missing Fields</span>
        <button onClick={() => setGapPanelOpen(false)} className="text-gray-500 hover:text-gray-300">
          <X size={14} />
        </button>
      </div>

      <div className="max-h-52 overflow-y-auto px-4 pb-3">
        {hasMandatory && (
          <div className="mb-3">
            <p className="mb-1 text-xs font-bold uppercase tracking-wider text-red-400">Mandatory</p>
            <div className="divide-y divide-gray-800/60">
              {gaps.missing_mandatory.map((gap) => (
                <GapItem key={gap.field_name} gap={gap} onJump={onJumpToField} />
              ))}
            </div>
          </div>
        )}

        {hasRequired && (
          <div className="mb-3">
            <p className="mb-1 text-xs font-bold uppercase tracking-wider text-amber-400">Required</p>
            <div className="divide-y divide-gray-800/60">
              {gaps.missing_required.map((gap) => (
                <GapItem key={gap.field_name} gap={gap} onJump={onJumpToField} />
              ))}
            </div>
          </div>
        )}

        {hasRecommended && (
          <div>
            <p className="mb-1 text-xs font-bold uppercase tracking-wider text-gray-500">Recommended</p>
            <div className="divide-y divide-gray-800/60">
              {gaps.missing_recommended.map((gap) => (
                <GapItem key={gap.field_name} gap={gap} onJump={onJumpToField} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
