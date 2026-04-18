import { useState, useRef } from 'react';
import { X, Plus } from 'lucide-react';

interface ListFieldProps {
  values: string[];
  isEditing: boolean;
  onStartEdit: () => void;
  onChange: (v: string[]) => void;
  onCommit: () => void;
  onDiscard: () => void;
}

export function ListField({ values, isEditing, onStartEdit, onChange, onCommit, onDiscard }: ListFieldProps) {
  const [inputText, setInputText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const addItem = () => {
    const trimmed = inputText.trim();
    if (!trimmed) return;
    const updated = [...values, trimmed];
    onChange(updated);
    setInputText('');
    inputRef.current?.focus();
  };

  const removeItem = (idx: number) => {
    onChange(values.filter((_, i) => i !== idx));
  };

  if (isEditing) {
    return (
      <div className="space-y-2 py-1">
        <div className="flex flex-wrap gap-1.5">
          {values.map((v, i) => (
            <span
              key={i}
              className="flex items-center gap-1 rounded-full bg-gray-700 px-2.5 py-1 text-sm text-gray-200"
            >
              {v}
              <button
                onClick={() => removeItem(i)}
                className="ml-0.5 rounded-full text-gray-400 hover:text-red-400"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') { e.preventDefault(); addItem(); }
              if (e.key === 'Escape') onDiscard();
            }}
            placeholder="Add item..."
            className="min-h-[44px] flex-1 rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-100 ring-1 ring-blue-500 outline-none"
            autoFocus
          />
          <button onClick={addItem} className="rounded-lg bg-gray-700 px-3 py-2 hover:bg-gray-600">
            <Plus size={16} className="text-gray-300" />
          </button>
          <button onClick={onCommit} className="rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
            Done
          </button>
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
          {values.map((v, i) => (
            <span key={i} className="rounded-full bg-gray-800 px-2.5 py-1 text-sm text-gray-200">
              {v}
            </span>
          ))}
        </div>
      ) : (
        <span className="text-sm text-gray-600 italic">— tap to add</span>
      )}
    </button>
  );
}
