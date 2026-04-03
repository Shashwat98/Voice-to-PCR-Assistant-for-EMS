import { useTranscriptStore } from '../../store/transcriptStore';

export function PartialText() {
  const partialText = useTranscriptStore((s) => s.partialText);
  if (!partialText) return null;

  return (
    <div className="px-4 py-2">
      <p className="text-sm italic text-gray-500">
        {partialText}
        <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-gray-500 align-middle" />
      </p>
    </div>
  );
}
