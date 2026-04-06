import { FIELD_REGISTRY } from '../../constants/fieldRegistry';
import { usePCRStore } from '../../store/pcrStore';
import { useUIStore } from '../../store/uiStore';
import type { MedicationGiven } from '../../types/pcr';
import { confidenceBorderColor } from '../../utils/confidenceColor';
import { ConfidenceDot } from './ConfidenceDot';
import { EnumField } from './EnumField';
import { FieldLabel } from './FieldLabel';
import { ListField } from './ListField';
import { MedicationField } from './MedicationField';
import { ScalarField } from './ScalarField';

interface PCRFieldProps {
  fieldKey: string;
  fieldRef?: (el: HTMLDivElement | null) => void;
}

export function PCRField({ fieldKey, fieldRef }: PCRFieldProps) {
  const meta = FIELD_REGISTRY[fieldKey];
  if (!meta) return null;

  const { getEffectiveValue, getConfidence, setFieldEdit, commitFieldEdit, discardFieldEdit } = usePCRStore();
  const { editingField, setEditingField } = useUIStore();

  const isEditing = editingField === fieldKey;
  const value = getEffectiveValue(fieldKey);
  const confidence = getConfidence(fieldKey);
  const borderClass = confidenceBorderColor(confidence);

  const startEdit = () => setEditingField(fieldKey);
  const commit = () => {
    commitFieldEdit(fieldKey);
    setEditingField(null);
  };
  const discard = () => {
    discardFieldEdit(fieldKey);
    setEditingField(null);
  };

  const renderEditor = () => {
    if (meta.value_type === 'list[MedicationGiven]') {
      return (
        <MedicationField
          values={(value as MedicationGiven[]) ?? []}
          isEditing={isEditing}
          onStartEdit={startEdit}
          onChange={(v) => setFieldEdit(fieldKey, v)}
          onCommit={commit}
          onDiscard={discard}
        />
      );
    }

    if (meta.value_type.startsWith('list[')) {
      return (
        <ListField
          values={(value as string[]) ?? []}
          isEditing={isEditing}
          onStartEdit={startEdit}
          onChange={(v) => setFieldEdit(fieldKey, v)}
          onCommit={commit}
          onDiscard={discard}
        />
      );
    }

    if (meta.allowed_values) {
      return (
        <EnumField
          value={value as string | undefined}
          allowedValues={meta.allowed_values}
          isEditing={isEditing}
          onStartEdit={startEdit}
          onSelect={(v) => {
            setFieldEdit(fieldKey, v);
            commitFieldEdit(fieldKey);
            setEditingField(null);
          }}
          onDiscard={discard}
        />
      );
    }

    return (
      <ScalarField
        value={value as string | number | undefined}
        isEditing={isEditing}
        valueType={meta.value_type as 'str' | 'int' | 'float'}
        onStartEdit={startEdit}
        onChange={(v) => setFieldEdit(fieldKey, v)}
        onCommit={commit}
        onDiscard={discard}
      />
    );
  };

  return (
    <div
      ref={fieldRef}
      className={`rounded-lg border p-3 transition-all ${
        isEditing ? 'border-blue-500/50 bg-gray-900' : `${borderClass} bg-gray-900/40 hover:bg-gray-900/70`
      }`}
    >
      <div className="mb-1 flex items-center justify-between">
        <FieldLabel label={meta.clinical_label} usage={meta.usage} />
        <ConfidenceDot confidence={confidence} />
      </div>
      {renderEditor()}
    </div>
  );
}
