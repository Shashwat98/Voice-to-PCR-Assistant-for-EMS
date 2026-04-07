/**
 * useAudioCapture — connects the mic button to real audio recording.
 *
 * Flow:
 *   1. User presses mic → micStatus becomes 'active' → start MediaRecorder
 *   2. User presses mic again → micStatus becomes 'processing'
 *      → stop MediaRecorder, collect full audio buffer
 *      → POST /sessions/{id}/transcribe → update transcript store
 *      → POST /sessions/{id}/extract   → update PCR store
 *      → GET  /sessions/{id}/gaps      → update gap store
 *      → micStatus back to 'idle'
 */

import { useEffect, useRef } from 'react';
import type { RefObject } from 'react';
import { usePCRStore } from '../store/pcrStore';
import { useTranscriptStore } from '../store/transcriptStore';
import { useUIStore } from '../store/uiStore';
import type { PCRStateEnvelope } from '../types/pcr';
import type { GapDetectionResult, TranscriptSegment } from '../types/session';

export function useAudioCapture(sessionIdRef: RefObject<string | null>) {
  const { micStatus, setMicStatus, setGaps, setGapPanelOpen } = useUIStore();
  const { addSegment, setPartial } = useTranscriptStore();
  const { applyServerState } = usePCRStore();

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Start recording when mic becomes active
  useEffect(() => {
    if (micStatus === 'active') {
      startRecording();
    } else if (micStatus === 'processing') {
      stopAndProcess();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [micStatus]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';
      const recorder = new MediaRecorder(stream, { mimeType });
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.start();
    } catch (err) {
      console.error('[useAudioCapture] mic access denied', err);
      setMicStatus('idle');
    }
  };

  const stopAndProcess = async () => {
    const recorder = recorderRef.current;
    if (!recorder) {
      setMicStatus('idle');
      return;
    }

    // Stop recorder and wait for final data
    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve();
      recorder.stop();
      recorder.stream.getTracks().forEach((t) => t.stop());
    });

    const sid = sessionIdRef.current;
    if (!sid || chunksRef.current.length === 0) {
      setMicStatus('idle');
      return;
    }

    const mimeType = chunksRef.current[0]?.type || 'audio/webm';
    const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
    const audioBlob = new Blob(chunksRef.current, { type: mimeType });
    chunksRef.current = [];

    try {
      // Show partial text while processing
      setPartial('Transcribing...');

      // 1. Transcribe
      const formData = new FormData();
      formData.append('file', audioBlob, `audio.${ext}`);

      const transcribeRes = await fetch(`/api/v1/sessions/${sid}/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!transcribeRes.ok) throw new Error(`Transcribe failed: ${transcribeRes.status}`);
      const transcribeData = await transcribeRes.json();
      const transcript: string = transcribeData.transcript_text ?? '';

      // Update transcript store
      setPartial(null);
      const seg: TranscriptSegment = {
        text: transcript,
        start_time: 0,
        end_time: transcribeData.duration_sec ?? 0,
        timestamp: new Date().toISOString(),
      };
      addSegment(seg);

      // 2. Extract PCR fields
      setPartial('Extracting PCR fields...');
      const extractRes = await fetch(`/api/v1/sessions/${sid}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript, model: 'llm_baseline' }),
      });

      if (extractRes.ok) {
        const extractData = await extractRes.json();
        if (extractData.pcr_state) {
          applyServerState(extractData.pcr_state as PCRStateEnvelope);
        }
      }

      // 3. Fetch gaps
      const gapRes = await fetch(`/api/v1/sessions/${sid}/gaps`);
      if (gapRes.ok) {
        const gaps: GapDetectionResult = await gapRes.json();
        setGaps(gaps);
        if (gaps.missing_mandatory.length > 0 || gaps.missing_required.length > 0) {
          setGapPanelOpen(true);
        }
      }
    } catch (err) {
      console.error('[useAudioCapture] processing error', err);
    } finally {
      setPartial(null);
      setMicStatus('idle');
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      recorderRef.current?.stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);
}
