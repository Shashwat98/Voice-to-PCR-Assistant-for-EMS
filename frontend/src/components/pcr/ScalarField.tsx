import { useRef, useEffect } from 'react';

interface ScalarFieldProps {
  value: string | number | undefined;
  isEditing: boolean;
  valueType: 'str' | 'int' | 'float';
  unit?: string;
  onStartEdit: () => void;
  onChange: (v: string | number) => void;
  onCommit: () => void;
  onDiscard: () => void;
}

export function ScalarField({
  value,
  isEditing,
  valueType,
  unit,
  onStartEdit,
  onChange,
  onCommit,
  onDiscard,
}: ScalarFieldProps) {
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing) inputRef.current?.focus();
  }, [isEditing]);

  if (isEditing) {
    const isMultiline = valueType === 'str' && String(value ?? '').length > 60;

    if (isMultiline) {
      return (
        <textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          defaultValue={String(value ?? '')}
          className="w-full rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-100 ring-1 ring-blue-500 outline-none resize-none min-h-[80px]"
          onChange={(e) => onChange(e.target.value)}
          onBlur={onCommit}
          onKeyDown={(e) => {
            if (e.key === 'Escape') onDiscard();
          }}
        />
      );
    }

    return (
      <input
        ref={inputRef as React.RefObject<HTMLInputElement>}
        type={valueType === 'str' ? 'text' : 'number'}
        inputMode={valueType !== 'str' ? 'numeric' : undefined}
        defaultValue={value !== undefined ? String(value) : ''}
        className="w-full rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-100 ring-1 ring-blue-500 outline-none min-h-[44px]"
        onChange={(e) => {
          const raw = e.target.value;
          onChange(valueType === 'str' ? raw : (valueType === 'float' ? parseFloat(raw) : parseInt(raw, 10)));
        }}
        onBlur={onCommit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') { e.preventDefault(); onCommit(); }
          if (e.key === 'Escape') onDiscard();
        }}
      />
    );
  }

  return (
    <button
      onClick={onStartEdit}
      className="min-h-[44px] w-full rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-gray-800/60"
    >
      {value !== undefined && value !== null && value !== '' ? (
        <span className="font-medium text-gray-100">
          {String(value)}{unit ? <span className="ml-1 text-gray-500 text-xs font-normal">{unit}</span> : null}
        </span>
      ) : (
        <span className="text-gray-600 italic">— tap to add</span>
      )}
    </button>
  );
}
