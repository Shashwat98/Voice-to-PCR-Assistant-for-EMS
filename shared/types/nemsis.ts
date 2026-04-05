export type NEMSISUsage = 'mandatory' | 'required' | 'recommended';

export type NEMSISSection =
  | 'ePatient'
  | 'eSituation'
  | 'eHistory'
  | 'eVitals'
  | 'eMedications'
  | 'eProcedures'
  | 'eNarrative';

export interface FieldMetadata {
  nemsis_element: string;
  usage: NEMSISUsage;
  section: NEMSISSection;
  description: string;
  value_type: string;
  allowed_values?: string[];
  prompt_template: string;
  clinical_label: string;
}
