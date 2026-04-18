import './global.css';
import { cssInterop } from 'nativewind';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { SessionHeader } from './src/components/session/SessionHeader';
import { TranscriptPanel } from './src/components/transcript/TranscriptPanel';
import { PCRForm } from './src/components/pcr/PCRForm';
import { useMockSession } from './src/hooks/useMockSession';
import { View } from 'react-native';

cssInterop(SafeAreaView, { className: 'style' });

function SessionScreen() {
  useMockSession();
  return (
    <SafeAreaView className="flex-1 bg-gray-950">
      <SessionHeader />
      <View className="flex-1">
        <PCRForm />
      </View>
      <TranscriptPanel />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <SessionScreen />
    </SafeAreaProvider>
  );
}
