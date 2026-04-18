import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSessionStore } from '@shared/store/sessionStore';
import { usePCRStore } from '@shared/store/pcrStore';
import { useUIStore } from '@shared/store/uiStore';

export function SessionHeader() {
  const { sessionId, finalizeSession, status } = useSessionStore();
  const { envelope } = usePCRStore();
  const { micStatus, setMicStatus, gaps, toggleGapPanel } = useUIStore();

  const score = envelope?.completeness_score ?? 0;
  const pct = Math.round(score * 100);
  const barColor = pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-500';
  const totalGaps = (gaps?.missing_mandatory.length ?? 0) + (gaps?.missing_required.length ?? 0);
  const isFinalized = status === 'finalized';

  function handleMicPress() {
    setMicStatus(micStatus === 'idle' ? 'active' : 'idle');
  }

  return (
    <View className="px-4 py-4 border-b border-gray-700 bg-gray-900">
      {/* Top row */}
      <View className="flex-row items-center justify-between mb-3">
        <View>
          <Text className="text-white font-bold text-lg">Voice-to-PCR</Text>
          {sessionId && (
            <Text className="text-gray-500 text-sm">{sessionId.slice(0, 12)}</Text>
          )}
        </View>

        <View className="flex-row items-center gap-3">
          {/* Gap badge */}
          {totalGaps > 0 && (
            <Pressable onPress={toggleGapPanel} className="flex-row items-center gap-1 bg-amber-400/10 px-2 py-1 rounded-full">
              <Ionicons name="warning" size={14} color="#f59e0b" />
              <Text className="text-amber-400 text-sm font-semibold">{totalGaps}</Text>
            </Pressable>
          )}

          {/* Finalize button */}
          <Pressable
            onPress={finalizeSession}
            disabled={isFinalized}
            className={`px-3 py-2 rounded-lg ${isFinalized ? 'bg-green-800' : 'bg-green-600'}`}
          >
            <Text className="text-white text-sm font-semibold">
              {isFinalized ? 'Done' : 'Finalize'}
            </Text>
          </Pressable>

          {/* Mic button */}
          <Pressable
            onPress={handleMicPress}
            className={`w-12 h-12 rounded-full items-center justify-center ${
              micStatus === 'active' ? 'bg-red-600' : 'bg-gray-700'
            }`}
          >
            <Ionicons
              name={micStatus === 'active' ? 'mic-off' : 'mic'}
              size={22}
              color="white"
            />
          </Pressable>
        </View>
      </View>

      {/* Completeness bar */}
      <View className="flex-row items-center gap-2">
        <View className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
          <View className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
        </View>
        <Text className="text-gray-400 text-sm w-10 text-right">{pct}%</Text>
      </View>
    </View>
  );
}
