import { useEffect } from 'react';
import { mockPCRState, MOCK_SESSION_ID } from '@shared/mock/mockPCRState';
import { mockTranscriptSegments } from '@shared/mock/mockTranscript';
import { mockGaps } from '@shared/mock/mockGaps';
import { usePCRStore } from '@shared/store/pcrStore';
import { useSessionStore } from '@shared/store/sessionStore';
import { useTranscriptStore } from '@shared/store/transcriptStore';
import { useUIStore } from '@shared/store/uiStore';

export function useMockSession() {
  const { applyServerState } = usePCRStore();
  const { setSession, setConnectionState } = useSessionStore();
  const { addSegment, setPartial } = useTranscriptStore();
  const { setGaps, setGapPanelOpen } = useUIStore();

  useEffect(() => {
    setSession(MOCK_SESSION_ID, 'INC-2026-0042');
    setConnectionState('connected');

    const timers: ReturnType<typeof setTimeout>[] = [];

    mockTranscriptSegments.forEach((seg, i) => {
      timers.push(
        setTimeout(() => {
          setPartial(seg.text.slice(0, Math.ceil(seg.text.length * 0.6)) + '...');
        }, i * 1800)
      );
      timers.push(
        setTimeout(() => {
          setPartial(null);
          addSegment(seg);
        }, i * 1800 + 900)
      );
    });

    const pcrDelay = mockTranscriptSegments.length * 1800 + 500;
    timers.push(
      setTimeout(() => {
        applyServerState(mockPCRState);
        setGaps(mockGaps);
        if (mockGaps.missing_mandatory.length > 0 || mockGaps.missing_required.length > 0) {
          setGapPanelOpen(true);
        }
      }, pcrDelay)
    );

    return () => timers.forEach(clearTimeout);
  }, []);
}
