import { useSessionStore } from '../store/sessionStore';
import { useUIStore } from '../store/uiStore';
import { useMockSession } from '../hooks/useMockSession';
import { AppShell } from '../components/layout/AppShell';
import { TwoColumnLayout } from '../components/layout/TwoColumnLayout';
import { SessionHeader } from '../components/session/SessionHeader';
import { TranscriptPanel } from '../components/transcript/TranscriptPanel';
import { PCRForm } from '../components/pcr/PCRForm';

export function SessionPage() {
  useMockSession();

  const finalizeSession = useSessionStore((s) => s.finalizeSession);
  const { micStatus, setMicStatus } = useUIStore();

  const handleMicToggle = () => {
    if (micStatus === 'idle') setMicStatus('active');
    else if (micStatus === 'active') setMicStatus('processing');
    else setMicStatus('idle');
  };

  return (
    <AppShell>
      <SessionHeader onMicToggle={handleMicToggle} onFinalize={finalizeSession} />
      <TwoColumnLayout
        left={<TranscriptPanel />}
        right={<PCRForm />}
      />
    </AppShell>
  );
}
