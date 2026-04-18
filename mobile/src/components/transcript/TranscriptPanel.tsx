import { useState } from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranscriptStore } from '@shared/store/transcriptStore';
import { formatTime } from '@shared/utils/formatters';

export function TranscriptPanel() {
  const { segments, partialText } = useTranscriptStore();
  const [collapsed, setCollapsed] = useState(false);

  if (segments.length === 0 && !partialText) return null;

  return (
    <View className="border-t border-gray-800 bg-gray-900">
      <Pressable
        onPress={() => setCollapsed((v) => !v)}
        className="flex-row items-center justify-between px-4 pt-2 pb-1"
      >
        <Text className="text-sm text-gray-400 font-semibold">Transcript</Text>
        <Ionicons
          name={collapsed ? 'chevron-up' : 'chevron-down'}
          size={14}
          color="#6b7280"
        />
      </Pressable>
      {!collapsed && (
        <ScrollView className="px-4 pb-2 max-h-44">
          {segments.map((seg, i) => (
            <View key={i} className="flex-row gap-2 py-0.5">
              <Text className="text-gray-500 text-xs w-16">{formatTime(seg.timestamp)}</Text>
              <Text className="text-gray-300 text-xs flex-1">{seg.text}</Text>
            </View>
          ))}
          {partialText && (
            <Text className="text-gray-500 text-xs italic py-0.5">{partialText}</Text>
          )}
        </ScrollView>
      )}
    </View>
  );
}
