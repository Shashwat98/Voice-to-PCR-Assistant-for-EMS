import type { PCRStateEnvelope } from './pcr';

export interface TranscriptSegment {
  text: string;
  start_time: number;
  end_time: number;
  timestamp: string;
}

export interface CorrectionEvent {
  field_name: string;
  old_value: unknown;
  new_value: unknown;
  timestamp: string;
}

export interface GapItem {
  field_name: string;
  usage: 'mandatory' | 'required' | 'recommended';
  section: string;
  description: string;
  prompt: string;
  priority: number;
}

export interface GapDetectionResult {
  missing_mandatory: GapItem[];
  missing_required: GapItem[];
  missing_recommended: GapItem[];
  suggested_prompts: string[];
  total_gaps: number;
}

export interface SessionResponse {
  session_id: string;
  incident_id: string | null;
  created_at: string;
  status: 'active' | 'finalized' | 'archived';
  pcr_state: PCRStateEnvelope;
}
