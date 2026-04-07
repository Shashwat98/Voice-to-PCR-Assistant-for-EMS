import { useEffect } from 'react';
import { useUIStore } from '../store/uiStore';
import { usePCRStore } from '../store/pcrStore';
import { useSession } from '../hooks/useSession';
import { useAudioCapture } from '../hooks/useAudioCapture';
import { AppShell } from '../components/layout/AppShell';
import { TwoColumnLayout } from '../components/layout/TwoColumnLayout';
import { SessionHeader } from '../components/session/SessionHeader';
import { TranscriptPanel } from '../components/transcript/TranscriptPanel';
import { PCRForm } from '../components/pcr/PCRForm';

export function SessionPage() {
  const { sendCorrection, handleFinalize, sessionIdRef } = useSession();
  useAudioCapture(sessionIdRef);

  const { micStatus, setMicStatus } = useUIStore();
  const { setOnCommit } = usePCRStore();

  // Wire field corrections to the backend
  useEffect(() => {
    setOnCommit((fieldKey, value) => {
      sendCorrection(fieldKey, value);
    });
    return () => setOnCommit(null);
  }, [sendCorrection, setOnCommit]);

  const handleMicToggle = () => {
    if (micStatus === 'idle') setMicStatus('active');
    else if (micStatus === 'active') setMicStatus('processing');
    // 'processing' resets to 'idle' automatically once audio is processed
  };

  return (
    <AppShell>
      <SessionHeader onMicToggle={handleMicToggle} onFinalize={handleFinalize} />
      <TwoColumnLayout
        left={<TranscriptPanel />}
        right={<PCRForm />}
      />
    </AppShell>
  );
}
