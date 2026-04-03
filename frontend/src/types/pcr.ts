export interface MedicationGiven {
  drug: string;
  dose?: number;
  unit?: string;
  route?: string;
  time?: string;
}

export interface PCRDocument {
  age?: number;
  sex?: string;
  chief_complaint?: string;
  primary_impression?: string;
  secondary_impression?: string;
  signs_symptoms: string[];
  events_leading?: string;
  allergies: string[];
  medications_current: string[];
  past_medical_history: string[];
  bp_systolic?: number;
  bp_diastolic?: number;
  heart_rate?: number;
  respiratory_rate?: number;
  spo2?: number;
  gcs_total?: number;
  avpu?: string;
  pain_scale?: number;
  temperature?: number;
  blood_glucose?: number;
  etco2?: number;
  cardiac_rhythm?: string;
  medications_given: MedicationGiven[];
  procedures: string[];
  narrative_text?: string;
}

export interface FieldConfidence {
  value: unknown;
  confidence: number;
  source: 'asr_extraction' | 'user_correction' | 'gap_fill';
  timestamp: string;
  extraction_model: string;
}

export interface PCRStateEnvelope {
  session_id: string;
  pcr: PCRDocument;
  field_confidence: Record<string, FieldConfidence>;
  missing_mandatory: string[];
  missing_required: string[];
  completeness_score: number;
  last_updated: string;
  version: number;
}
