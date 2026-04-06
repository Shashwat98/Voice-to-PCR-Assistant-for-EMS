import { create } from 'zustand';

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
export type SessionStatus = 'active' | 'finalized' | 'archived';

interface SessionState {
  sessionId: string | null;
  incidentId: string | null;
  status: SessionStatus;
  connectionState: ConnectionState;
  isOffline: boolean;
  setSession: (id: string, incidentId?: string) => void;
  setConnectionState: (s: ConnectionState) => void;
  setOffline: (v: boolean) => void;
  finalizeSession: () => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  incidentId: null,
  status: 'active',
  connectionState: 'disconnected',
  isOffline: false,

  setSession: (id, incidentId) => set({ sessionId: id, incidentId: incidentId ?? null }),
  setConnectionState: (connectionState) => set({ connectionState }),
  setOffline: (isOffline) => set({ isOffline }),
  finalizeSession: () => set({ status: 'finalized' }),
  reset: () => set({ sessionId: null, incidentId: null, status: 'active', connectionState: 'disconnected', isOffline: false }),
}));
