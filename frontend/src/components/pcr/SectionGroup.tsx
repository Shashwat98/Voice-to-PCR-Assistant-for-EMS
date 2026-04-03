import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { NEMSISSection } from '../../types/nemsis';
import { SECTION_LABELS } from '../../constants/fieldRegistry';
import { getFieldsForSection, isEmpty } from '../../utils/fieldHelpers';
import { usePCRStore } from '../../store/pcrStore';
import { PCRField } from './PCRField';

interface SectionGroupProps {
  section: NEMSISSection;
  fieldRefs: React.MutableRefObject<Record<string, HTMLDivElement | null>>;
}

export function SectionGroup({ section, fieldRefs }: SectionGroupProps) {
  const [open, setOpen] = useState(true);
  const fields = getFieldsForSection(section);
  const envelope = usePCRStore((s) => s.envelope);

  const filledCount = fields.filter((key) => {
    const val = (envelope?.pcr as unknown as Record<string, unknown>)?.[key];
    return !isEmpty(val);
  }).length;

  return (
    <div className="border-b border-gray-800/60">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronRight size={14} className="text-gray-500" />}
          <span className="text-sm font-semibold text-gray-200">{SECTION_LABELS[section]}</span>
        </div>
        <span className="text-xs text-gray-500">
          {filledCount}/{fields.length}
        </span>
      </button>

      {open && (
        <div className="grid grid-cols-1 gap-2 px-4 pb-3 sm:grid-cols-2">
          {fields.map((key) => (
            <PCRField
              key={key}
              fieldKey={key}
              fieldRef={(el) => { fieldRefs.current[key] = el; }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
