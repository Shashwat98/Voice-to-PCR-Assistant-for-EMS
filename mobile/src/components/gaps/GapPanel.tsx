import { View, Text, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useUIStore } from '@shared/store/uiStore';

export function GapPanel() {
  const { gaps, setGapPanelOpen, setEditingField } = useUIStore();

  if (!gaps) return null;

  const { missing_mandatory, missing_required, missing_recommended } = gaps;

  return (
    <View className="bg-gray-900 border-b border-gray-800 max-h-52">
      <View className="flex-row items-center justify-between px-4 py-2">
        <Text className="text-gray-200 text-sm font-semibold">Missing Fields</Text>
        <Pressable onPress={() => setGapPanelOpen(false)}>
          <Ionicons name="close" size={16} color="#6b7280" />
        </Pressable>
      </View>
      <ScrollView className="px-4 pb-3">
        {missing_mandatory.map((gap, i) => (
          <View key={i} className="flex-row items-start justify-between py-1.5 border-b border-gray-800">
            <View className="flex-1">
              <Text className="text-red-400 text-xs font-semibold">{gap.field_name}</Text>
              <Text className="text-gray-500 text-xs italic">{gap.prompt}</Text>
            </View>
            <Pressable onPress={() => setEditingField(gap.field_name)} className="ml-3">
              <Text className="text-blue-400 text-xs font-semibold">Go</Text>
            </Pressable>
          </View>
        ))}
        {missing_required.map((gap, i) => (
          <View key={i} className="flex-row items-start justify-between py-1.5 border-b border-gray-800">
            <View className="flex-1">
              <Text className="text-amber-400 text-xs font-semibold">{gap.field_name}</Text>
              <Text className="text-gray-500 text-xs italic">{gap.prompt}</Text>
            </View>
            <Pressable onPress={() => setEditingField(gap.field_name)} className="ml-3">
              <Text className="text-blue-400 text-xs font-semibold">Go</Text>
            </Pressable>
          </View>
        ))}
        {missing_recommended.map((gap, i) => (
          <View key={i} className="flex-row items-start justify-between py-1.5">
            <View className="flex-1">
              <Text className="text-gray-400 text-xs font-semibold">{gap.field_name}</Text>
              <Text className="text-gray-500 text-xs italic">{gap.prompt}</Text>
            </View>
            <Pressable onPress={() => setEditingField(gap.field_name)} className="ml-3">
              <Text className="text-blue-400 text-xs font-semibold">Go</Text>
            </Pressable>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}
