import type { FieldConfidence } from '../types/pcr';

export function confidenceDotColor(conf: FieldConfidence | null): string {
  if (!conf) return 'bg-gray-600';
  if (conf.source === 'user_correction') return 'bg-blue-400';
  if (conf.confidence > 0.8) return 'bg-green-500';
  if (conf.confidence >= 0.5) return 'bg-amber-400';
  return 'bg-red-500';
}

export function confidenceBorderColor(conf: FieldConfidence | null): string {
  if (!conf) return 'border-gray-700';
  if (conf.source === 'user_correction') return 'border-blue-400/50';
  if (conf.confidence > 0.8) return 'border-transparent';
  if (conf.confidence >= 0.5) return 'border-amber-400/50';
  return 'border-red-500/60';
}

export function confidenceLabel(conf: FieldConfidence | null): string {
  if (!conf) return 'Not extracted';
  if (conf.source === 'user_correction') return 'Manually verified';
  const pct = Math.round(conf.confidence * 100);
  return `${pct}% confidence (${conf.extraction_model})`;
}
