import { FIELD_REGISTRY, SECTION_LABELS } from '../constants/fieldRegistry';
import type { NEMSISSection } from '../types/nemsis';

export function getLabel(fieldKey: string): string {
  return FIELD_REGISTRY[fieldKey]?.clinical_label ?? fieldKey;
}

export function getSection(fieldKey: string): NEMSISSection | null {
  return FIELD_REGISTRY[fieldKey]?.section ?? null;
}

export function getSectionLabel(section: NEMSISSection): string {
  return SECTION_LABELS[section] ?? section;
}

export function isListType(fieldKey: string): boolean {
  const vt = FIELD_REGISTRY[fieldKey]?.value_type ?? '';
  return vt.startsWith('list');
}

export function isMedicationList(fieldKey: string): boolean {
  return FIELD_REGISTRY[fieldKey]?.value_type === 'list[MedicationGiven]';
}

export function getFieldsForSection(section: NEMSISSection): string[] {
  return Object.entries(FIELD_REGISTRY)
    .filter(([, meta]) => meta.section === section)
    .map(([key]) => key);
}

export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
}
