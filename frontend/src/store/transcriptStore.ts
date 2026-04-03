import { create } from 'zustand';
import type { TranscriptSegment } from '../types/session';

interface TranscriptState {
  segments: TranscriptSegment[];
  partialText: string | null;
  addSegment: (seg: TranscriptSegment) => void;
  setPartial: (text: string | null) => void;
  clearAll: () => void;
}

export const useTranscriptStore = create<TranscriptState>((set) => ({
  segments: [],
  partialText: null,
  addSegment: (seg) => set((s) => ({ segments: [...s.segments, seg] })),
  setPartial: (partialText) => set({ partialText }),
  clearAll: () => set({ segments: [], partialText: null }),
}));
