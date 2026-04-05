import { ScrollView } from 'react-native';
import { SECTION_ORDER } from '@shared/constants/fieldRegistry';
import { useUIStore } from '@shared/store/uiStore';
import { GapPanel } from '../gaps/GapPanel';
import { SectionGroup } from './SectionGroup';

export function PCRForm() {
  const { gapPanelOpen } = useUIStore();

  return (
    <ScrollView className="flex-1 bg-gray-950" contentContainerStyle={{ paddingBottom: 32 }}>
      {gapPanelOpen && <GapPanel />}
      {SECTION_ORDER.map((section) => (
        <SectionGroup key={section} section={section} />
      ))}
    </ScrollView>
  );
}
