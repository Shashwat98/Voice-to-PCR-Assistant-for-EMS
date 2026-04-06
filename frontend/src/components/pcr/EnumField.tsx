interface EnumFieldProps {
  value: string | undefined;
  allowedValues: string[];
  isEditing: boolean;
  onStartEdit: () => void;
  onSelect: (v: string) => void;
  onDiscard: () => void;
}

export function EnumField({ value, allowedValues, isEditing, onStartEdit, onSelect, onDiscard }: EnumFieldProps) {
  if (isEditing) {
    return (
      <div className="flex flex-wrap gap-2 py-1">
        {allowedValues.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`min-h-[44px] rounded-lg px-4 py-2 text-sm font-medium transition-colors
              ${opt === value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
          >
            {opt}
          </button>
        ))}
        <button
          onClick={onDiscard}
          className="min-h-[44px] rounded-lg px-3 py-2 text-sm text-gray-500 hover:text-gray-300"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={onStartEdit}
      className="min-h-[44px] w-full rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-gray-800/60"
    >
      {value ? (
        <span className="inline-flex items-center rounded-full bg-gray-800 px-3 py-1 text-sm font-medium text-gray-100">
          {value}
        </span>
      ) : (
        <span className="text-gray-600 italic">— tap to select</span>
      )}
    </button>
  );
}
