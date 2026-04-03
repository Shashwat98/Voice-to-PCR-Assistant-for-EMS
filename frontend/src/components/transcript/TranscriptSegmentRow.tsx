import type { TranscriptSegment } from '../../types/session';
import { formatTime } from '../../utils/formatters';

interface TranscriptSegmentRowProps {
  segment: TranscriptSegment;
}

export function TranscriptSegmentRow({ segment }: TranscriptSegmentRowProps) {
  return (
    <div className="group flex gap-3 px-4 py-2.5 hover:bg-gray-800/30 transition-colors">
      <span className="mt-0.5 shrink-0 text-xs text-gray-600">{formatTime(segment.timestamp)}</span>
      <p className="text-sm leading-relaxed text-gray-200">{segment.text}</p>
    </div>
  );
}
