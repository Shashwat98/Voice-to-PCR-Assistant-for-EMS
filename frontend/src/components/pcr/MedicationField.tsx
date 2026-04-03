import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import type { MedicationGiven } from '../../types/pcr';

interface MedicationFieldProps {
  values: MedicationGiven[];
  isEditing: boolean;
  onStartEdit: () => void;
  onChange: (v: MedicationGiven[]) => void;
  onCommit: () => void;
  onDiscard: () => void;
}

const EMPTY_MED: MedicationGiven = { drug: '', dose: undefined, unit: 'mg', route: '' };

export function MedicationField({ values, isEditing, onStartEdit, onChange, onCommit, onDiscard }: MedicationFieldProps) {
  const [newMed, setNewMed] = useState<MedicationGiven>(EMPTY_MED);

  const updateMed = (idx: number, patch: Partial<MedicationGiven>) => {
    const updated = values.map((m, i) => (i === idx ? { ...m, ...patch } : m));
    onChange(updated);
  };

  const removeMed = (idx: number) => onChange(values.filter((_, i) => i !== idx));

  const addMed = () => {
    if (!newMed.drug.trim()) return;
    onChange([...values, newMed]);
    setNewMed(EMPTY_MED);
  };

  if (isEditing) {
    return (
      <div className="space-y-3 py-1">
        {values.map((med, i) => (
          <div key={i} className="flex flex-wrap items-center gap-2 rounded-lg bg-gray-800 p-2">
            <input
              value={med.drug}
              onChange={(e) => updateMed(i, { drug: e.target.value })}
              placeholder="Drug"
              className="min-h-[36px] w-32 rounded bg-gray-700 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              value={med.dose ?? ''}
              onChange={(e) => updateMed(i, { dose: parseFloat(e.target.value) })}
              placeholder="Dose"
              className="min-h-[36px] w-20 rounded bg-gray-700 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
            />
            <input
              value={med.unit ?? ''}
              onChange={(e) => updateMed(i, { unit: e.target.value })}
              placeholder="Unit"
              className="min-h-[36px] w-16 rounded bg-gray-700 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
            />
            <input
              value={med.route ?? ''}
              onChange={(e) => updateMed(i, { route: e.target.value })}
              placeholder="Route"
              className="min-h-[36px] w-20 rounded bg-gray-700 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
            />
            <button onClick={() => removeMed(i)} className="text-gray-500 hover:text-red-400">
              <X size={14} />
            </button>
          </div>
        ))}

        {/* New medication row */}
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-gray-700 p-2">
          <input
            value={newMed.drug}
            onChange={(e) => setNewMed((m) => ({ ...m, drug: e.target.value }))}
            placeholder="Drug"
            className="min-h-[36px] w-32 rounded bg-gray-800 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
          />
          <input
            type="number"
            value={newMed.dose ?? ''}
            onChange={(e) => setNewMed((m) => ({ ...m, dose: parseFloat(e.target.value) }))}
            placeholder="Dose"
            className="min-h-[36px] w-20 rounded bg-gray-800 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
          />
          <input
            value={newMed.unit ?? ''}
            onChange={(e) => setNewMed((m) => ({ ...m, unit: e.target.value }))}
            placeholder="Unit"
            className="min-h-[36px] w-16 rounded bg-gray-800 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
          />
          <input
            value={newMed.route ?? ''}
            onChange={(e) => setNewMed((m) => ({ ...m, route: e.target.value }))}
            placeholder="Route"
            className="min-h-[36px] w-20 rounded bg-gray-800 px-2 text-sm text-gray-100 outline-none ring-inset focus:ring-1 focus:ring-blue-500"
          />
          <button onClick={addMed} className="flex items-center gap-1 rounded bg-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-600">
            <Plus size={12} /> Add
          </button>
        </div>

        <div className="flex gap-2">
          <button onClick={onCommit} className="rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">Done</button>
          <button onClick={onDiscard} className="rounded-lg bg-gray-700 px-3 py-2 text-sm text-gray-300 hover:bg-gray-600">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={onStartEdit}
      className="min-h-[44px] w-full rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-800/60"
    >
      {values.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {values.map((med, i) => (
            <span key={i} className="rounded-full bg-gray-800 px-2.5 py-1 text-sm text-gray-200">
              {med.drug}{med.dose != null ? ` ${med.dose}${med.unit ?? ''}` : ''}{med.route ? ` ${med.route}` : ''}
            </span>
          ))}
        </div>
      ) : (
        <span className="text-sm text-gray-600 italic">— tap to add</span>
      )}
    </button>
  );
}
