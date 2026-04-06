import { View, Text, Pressable, TextInput } from 'react-native';
import { usePCRStore } from '@shared/store/pcrStore';
import { useUIStore } from '@shared/store/uiStore';
import { getLabel, isEmpty, isListType, isMedicationList } from '@shared/utils/fieldHelpers';
import { FIELD_REGISTRY } from '@shared/constants/fieldRegistry';
import type { MedicationGiven } from '@shared/types/pcr';

interface Props {
  fieldKey: string;
}

export function PCRField({ fieldKey }: Props) {
  const { getEffectiveValue, getConfidence, setFieldEdit, commitFieldEdit, discardFieldEdit } = usePCRStore();
  const { editingField, setEditingField } = useUIStore();

  const value = getEffectiveValue(fieldKey);
  const conf = getConfidence(fieldKey);
  const meta = FIELD_REGISTRY[fieldKey];
  const isEditing = editingField === fieldKey;
  const label = getLabel(fieldKey);
  const usageBadge = meta?.usage === 'mandatory' ? 'M' : meta?.usage === 'required' ? 'R' : null;

  const dotColor =
    !conf ? '#4b5563'
    : conf.source === 'user_correction' ? '#60a5fa'
    : conf.confidence > 0.8 ? '#22c55e'
    : conf.confidence >= 0.5 ? '#fbbf24'
    : '#ef4444';

  function renderDisplayValue() {
    if (isEmpty(value)) {
      return <Text className="text-gray-600 text-base mt-0.5">— tap to add</Text>;
    }
    if (isMedicationList(fieldKey)) {
      const meds = value as MedicationGiven[];
      return (
        <View className="flex-row flex-wrap gap-1.5 mt-1">
          {meds.map((m, i) => (
            <View key={i} className="bg-gray-800 px-3 py-1 rounded-full">
              <Text className="text-gray-300 text-sm">{m.drug} {m.dose}{m.unit} {m.route}</Text>
            </View>
          ))}
        </View>
      );
    }
    if (isListType(fieldKey)) {
      const items = value as string[];
      return (
        <View className="flex-row flex-wrap gap-1.5 mt-1">
          {items.map((item, i) => (
            <View key={i} className="bg-gray-800 px-3 py-1 rounded-full">
              <Text className="text-gray-300 text-sm">{item}</Text>
            </View>
          ))}
        </View>
      );
    }
    return <Text className="text-gray-100 text-base mt-0.5">{String(value)}</Text>;
  }

  function renderEditor() {
    const currentVal = String(getEffectiveValue(fieldKey) ?? '');

    if (meta?.allowed_values) {
      return (
        <View className="flex-row flex-wrap gap-2 mt-2">
          {meta.allowed_values.map((opt) => (
            <Pressable
              key={opt}
              onPress={() => {
                setFieldEdit(fieldKey, opt);
                commitFieldEdit(fieldKey);
                setEditingField(null);
              }}
              className={`px-4 py-2 rounded-full border ${
                currentVal === opt
                  ? 'bg-blue-600 border-blue-600'
                  : 'bg-gray-800 border-gray-700'
              }`}
            >
              <Text className="text-gray-200 text-sm">{opt}</Text>
            </Pressable>
          ))}
          <Pressable
            onPress={() => { discardFieldEdit(fieldKey); setEditingField(null); }}
            className="px-4 py-2"
          >
            <Text className="text-gray-500 text-sm">Cancel</Text>
          </Pressable>
        </View>
      );
    }

    return (
      <View className="mt-2">
        <TextInput
          autoFocus
          className="bg-gray-800 text-gray-100 text-base rounded-xl px-4 py-3 border border-gray-600"
          defaultValue={currentVal}
          keyboardType={meta?.value_type === 'int' || meta?.value_type === 'float' ? 'numeric' : 'default'}
          onChangeText={(text) => setFieldEdit(fieldKey, text)}
          onSubmitEditing={() => { commitFieldEdit(fieldKey); setEditingField(null); }}
          returnKeyType="done"
          placeholderTextColor="#6b7280"
        />
        <View className="flex-row gap-4 mt-2">
          <Pressable
            onPress={() => { commitFieldEdit(fieldKey); setEditingField(null); }}
            className="bg-blue-600 px-4 py-2 rounded-lg"
          >
            <Text className="text-white text-sm font-semibold">Done</Text>
          </Pressable>
          <Pressable
            onPress={() => { discardFieldEdit(fieldKey); setEditingField(null); }}
            className="px-4 py-2"
          >
            <Text className="text-gray-500 text-sm">Cancel</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <Pressable
      onPress={() => !isEditing && setEditingField(fieldKey)}
      className="py-3 border-b border-gray-800/50"
    >
      <View className="flex-row items-center gap-2">
        <View className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: dotColor }} />
        <Text className="text-gray-400 text-xs uppercase tracking-widest font-medium">{label}</Text>
        {usageBadge && (
          <View className={`px-1.5 py-0.5 rounded ${usageBadge === 'M' ? 'bg-red-900/50' : 'bg-gray-800'}`}>
            <Text className={`text-xs font-bold ${usageBadge === 'M' ? 'text-red-400' : 'text-gray-500'}`}>
              {usageBadge}
            </Text>
          </View>
        )}
      </View>
      {isEditing ? renderEditor() : renderDisplayValue()}
    </Pressable>
  );
}
