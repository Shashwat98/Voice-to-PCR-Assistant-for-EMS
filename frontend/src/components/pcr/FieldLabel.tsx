import type { NEMSISUsage } from '../../types/nemsis';

interface FieldLabelProps {
  label: string;
  usage: NEMSISUsage;
}

const USAGE_BADGE: Record<NEMSISUsage, { text: string; className: string }> = {
  mandatory: { text: 'M', className: 'bg-red-500/20 text-red-400 ring-1 ring-red-500/30' },
  required: { text: 'R', className: 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30' },
  recommended: { text: '', className: '' },
};

export function FieldLabel({ label, usage }: FieldLabelProps) {
  const badge = USAGE_BADGE[usage];
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</span>
      {badge.text && (
        <span className={`rounded px-1 py-0.5 text-[10px] font-bold leading-none ${badge.className}`}>
          {badge.text}
        </span>
      )}
    </div>
  );
}
