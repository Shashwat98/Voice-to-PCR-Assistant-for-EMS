import { create } from 'zustand';
import type { NEMSISSection } from '../types/nemsis';
import type { GapDetectionResult } from '../types/session';

export type MicStatus = 'idle' | 'active' | 'processing';

interface UIState {
  micStatus: MicStatus;
  activeSection: NEMSISSection | null;
  editingField: string | null;
  gapPanelOpen: boolean;
  gaps: GapDetectionResult | null;

  setMicStatus: (s: MicStatus) => void;
  setActiveSection: (s: NEMSISSection | null) => void;
  setEditingField: (key: string | null) => void;
  toggleGapPanel: () => void;
  setGapPanelOpen: (open: boolean) => void;
  setGaps: (gaps: GapDetectionResult) => void;
}

export const useUIStore = create<UIState>((set) => ({
  micStatus: 'idle',
  activeSection: null,
  editingField: null,
  gapPanelOpen: false,
  gaps: null,

  setMicStatus: (micStatus) => set({ micStatus }),
  setActiveSection: (activeSection) => set({ activeSection }),
  setEditingField: (editingField) => set({ editingField }),
  toggleGapPanel: () => set((s) => ({ gapPanelOpen: !s.gapPanelOpen })),
  setGapPanelOpen: (gapPanelOpen) => set({ gapPanelOpen }),
  setGaps: (gaps) => set({ gaps }),
}));
