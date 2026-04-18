import { useEffect, useRef } from 'react';
import { FileText } from 'lucide-react';
import { useTranscriptStore } from '../../store/transcriptStore';
import { TranscriptSegmentRow } from './TranscriptSegmentRow';
import { PartialText } from './PartialText';

export function TranscriptPanel() {
  const segments = useTranscriptStore((s) => s.segments);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [segments]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-gray-800 px-4 py-3">
        <FileText size={14} className="text-gray-500" />
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Live Transcript</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {segments.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-600 italic">Transcript will appear here as you speak</p>
          </div>
        ) : (
          <>
            {segments.map((seg, i) => (
              <TranscriptSegmentRow key={i} segment={seg} />
            ))}
            <PartialText />
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  );
}
