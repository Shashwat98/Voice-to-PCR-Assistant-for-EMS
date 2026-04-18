import { useState } from 'react';
import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { NEMSISSection } from '@shared/types/nemsis';
import { getFieldsForSection, getSectionLabel, isEmpty } from '@shared/utils/fieldHelpers';
import { usePCRStore } from '@shared/store/pcrStore';
import { PCRField } from './PCRField';

interface Props {
  section: NEMSISSection;
}

const SECTION_ACCENT: Record<NEMSISSection, string> = {
  ePatient:     'bg-blue-500',
  eSituation:   'bg-violet-500',
  eVitals:      'bg-teal-500',
  eHistory:     'bg-indigo-500',
  eMedications: 'bg-pink-500',
  eProcedures:  'bg-orange-500',
  eNarrative:   'bg-cyan-500',
};

export function SectionGroup({ section }: Props) {
  const [expanded, setExpanded] = useState(true);
  const { getEffectiveValue } = usePCRStore();
  const fields = getFieldsForSection(section);
  const filledCount = fields.filter((f) => !isEmpty(getEffectiveValue(f))).length;
  const accent = SECTION_ACCENT[section];

  return (
    <View className="mt-2 mx-3 rounded-xl overflow-hidden border border-gray-800">
      {/* Colored top accent bar */}
      <View className={`h-1 ${accent}`} />

      {/* Section header */}
      <Pressable
        onPress={() => setExpanded((v) => !v)}
        className="flex-row items-center justify-between px-4 py-3 bg-gray-900"
      >
        <Text className="text-gray-100 font-bold text-base">{getSectionLabel(section)}</Text>
        <View className="flex-row items-center gap-2">
          <Text className="text-gray-400 text-sm">{filledCount}/{fields.length}</Text>
          <Ionicons
            name={expanded ? 'chevron-down' : 'chevron-forward'}
            size={16}
            color="#9ca3af"
          />
        </View>
      </Pressable>

      {/* Fields */}
      {expanded && (
        <View className="px-4 pb-4 pt-1 bg-gray-950 gap-1">
          {fields.map((fieldKey) => (
            <PCRField key={fieldKey} fieldKey={fieldKey} />
          ))}
        </View>
      )}
    </View>
  );
}
