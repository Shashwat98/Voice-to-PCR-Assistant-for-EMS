import { useRef } from 'react';
import { SECTION_ORDER } from '../../constants/fieldRegistry';
import { GapPanel } from '../gaps/GapPanel';
import { SectionGroup } from './SectionGroup';

export function PCRForm() {
  const fieldRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const scrollToField = (fieldKey: string) => {
    const el = fieldRefs.current[fieldKey];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <GapPanel onJumpToField={scrollToField} />
      <div className="flex-1 overflow-y-auto">
        {SECTION_ORDER.map((section) => (
          <SectionGroup key={section} section={section} fieldRefs={fieldRefs} />
        ))}
      </div>
    </div>
  );
}
