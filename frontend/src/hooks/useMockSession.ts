import { useEffect } from 'react';
import { mockPCRState, MOCK_SESSION_ID } from '../mock/mockPCRState';
import { mockTranscriptSegments } from '../mock/mockTranscript';
import { mockGaps } from '../mock/mockGaps';
import { usePCRStore } from '../store/pcrStore';
import { useSessionStore } from '../store/sessionStore';
import { useTranscriptStore } from '../store/transcriptStore';
import { useUIStore } from '../store/uiStore';

export function useMockSession() {
  const { applyServerState } = usePCRStore();
  const { setSession, setConnectionState } = useSessionStore();
  const { addSegment, setPartial } = useTranscriptStore();
  const { setGaps, setGapPanelOpen } = useUIStore();

  useEffect(() => {
    setSession(MOCK_SESSION_ID, 'INC-2026-0042');
    setConnectionState('connected');

    // Replay transcript segments with delays
    const timers: ReturnType<typeof setTimeout>[] = [];

    mockTranscriptSegments.forEach((seg, i) => {
      // Show partial text just before the segment finalizes
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

    // Load PCR state after all segments
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
