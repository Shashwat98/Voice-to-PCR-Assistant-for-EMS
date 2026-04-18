import { useState } from 'react';
import type { FieldConfidence } from '../../types/pcr';
import { confidenceDotColor, confidenceLabel } from '../../utils/confidenceColor';

interface ConfidenceDotProps {
  confidence: FieldConfidence | null;
}

export function ConfidenceDot({ confidence }: ConfidenceDotProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const color = confidenceDotColor(confidence);
  const label = confidenceLabel(confidence);

  return (
    <div
      className="relative flex items-center"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {showTooltip && (
        <div className="absolute right-4 top-1/2 z-10 -translate-y-1/2 whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs text-gray-200 shadow-lg ring-1 ring-gray-700">
          {label}
        </div>
      )}
    </div>
  );
}
