import { usePCRStore } from '../../store/pcrStore';

export function CompletenessBar() {
  const score = usePCRStore((s) => s.envelope?.completeness_score ?? 0);
  const pct = Math.round(score * 100);

  const barColor =
    pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-500';

  return (
    <div className="flex flex-1 items-center gap-3 px-4">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-sm font-medium text-gray-400">{pct}%</span>
    </div>
  );
}
