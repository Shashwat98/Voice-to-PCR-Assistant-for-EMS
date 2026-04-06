import type { GapDetectionResult } from '../types/session';

export const mockGaps: GapDetectionResult = {
  missing_mandatory: [],
  missing_required: [
    {
      field_name: 'narrative_text',
      usage: 'required',
      section: 'eNarrative',
      description: 'Free-text clinical narrative',
      prompt: 'Can you provide a brief narrative of the encounter?',
      priority: 24,
    },
  ],
  missing_recommended: [
    {
      field_name: 'secondary_impression',
      usage: 'recommended',
      section: 'eSituation',
      description: "Provider's secondary clinical impression",
      prompt: 'Is there a secondary impression?',
      priority: 34,
    },
    {
      field_name: 'temperature',
      usage: 'recommended',
      section: 'eVitals',
      description: 'Body temperature in °F',
      prompt: "What is the patient's temperature?",
      priority: 35,
    },
    {
      field_name: 'blood_glucose',
      usage: 'recommended',
      section: 'eVitals',
      description: 'Blood glucose level in mg/dL',
      prompt: 'What is the blood glucose level?',
      priority: 36,
    },
    {
      field_name: 'etco2',
      usage: 'recommended',
      section: 'eVitals',
      description: 'End-tidal CO2 in mmHg',
      prompt: 'What is the EtCO2?',
      priority: 37,
    },
    {
      field_name: 'cardiac_rhythm',
      usage: 'recommended',
      section: 'eVitals',
      description: 'Cardiac rhythm interpretation',
      prompt: 'What is the cardiac rhythm?',
      priority: 38,
    },
  ],
  suggested_prompts: ['Can you provide a brief narrative of the encounter?'],
  total_gaps: 6,
};
