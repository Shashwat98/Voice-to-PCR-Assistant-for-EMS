import { create } from 'zustand';
import type { PCRStateEnvelope, FieldConfidence } from '../types/pcr';

interface PCRState {
  envelope: PCRStateEnvelope | null;
  pendingEdits: Record<string, unknown>;

  applyServerState: (envelope: PCRStateEnvelope) => void;
  setFieldEdit: (fieldKey: string, value: unknown) => void;
  commitFieldEdit: (fieldKey: string) => void;
  discardFieldEdit: (fieldKey: string) => void;
  getEffectiveValue: (fieldKey: string) => unknown;
  getConfidence: (fieldKey: string) => FieldConfidence | null;
  reset: () => void;
}

export const usePCRStore = create<PCRState>((set, get) => ({
  envelope: null,
  pendingEdits: {},

  applyServerState: (incoming) => {
    const current = get().envelope;
    if (current && incoming.version < current.version) return;
    set({ envelope: incoming });
  },

  setFieldEdit: (fieldKey, value) =>
    set((s) => ({ pendingEdits: { ...s.pendingEdits, [fieldKey]: value } })),

  commitFieldEdit: (fieldKey) => {
    const { pendingEdits, envelope } = get();
    if (!envelope || !(fieldKey in pendingEdits)) return;
    const newValue = pendingEdits[fieldKey];
    const now = new Date().toISOString();
    const updatedPcr = { ...envelope.pcr, [fieldKey]: newValue };
    const updatedConfidence: FieldConfidence = {
      value: newValue,
      confidence: 1.0,
      source: 'user_correction',
      timestamp: now,
      extraction_model: 'manual',
    };
    set((s) => {
      const { [fieldKey]: _, ...rest } = s.pendingEdits;
      return {
        pendingEdits: rest,
        envelope: {
          ...envelope,
          pcr: updatedPcr,
          field_confidence: { ...envelope.field_confidence, [fieldKey]: updatedConfidence },
          version: envelope.version + 1,
          last_updated: now,
        },
      };
    });
  },

  discardFieldEdit: (fieldKey) =>
    set((s) => {
      const { [fieldKey]: _, ...rest } = s.pendingEdits;
      return { pendingEdits: rest };
    }),

  getEffectiveValue: (fieldKey) => {
    const { pendingEdits, envelope } = get();
    if (fieldKey in pendingEdits) return pendingEdits[fieldKey];
    if (!envelope) return undefined;
    return (envelope.pcr as unknown as Record<string, unknown>)[fieldKey];
  },

  getConfidence: (fieldKey) => {
    const { envelope } = get();
    return envelope?.field_confidence[fieldKey] ?? null;
  },

  reset: () => set({ envelope: null, pendingEdits: {} }),
}));
