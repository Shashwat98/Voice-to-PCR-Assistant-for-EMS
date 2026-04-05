export type WSClientMessageType = 'audio_chunk' | 'correction' | 'request_gaps' | 'finalize';

export interface WSClientMessage {
  type: WSClientMessageType;
  payload: Record<string, unknown>;
}

export type WSServerMessageType =
  | 'transcript_partial'
  | 'transcript_final'
  | 'extraction_update'
  | 'pcr_state'
  | 'gap_alert'
  | 'correction_applied'
  | 'error';

export interface WSServerMessage {
  type: WSServerMessageType;
  payload: Record<string, unknown>;
  timestamp: string;
  version: number;
}
