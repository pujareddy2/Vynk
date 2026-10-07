import type { InputHTMLAttributes } from "react";

interface SearchInputProps
  extends InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export default function SearchInput({
  value,
  onClear,
  className = "",
  ...props
}: SearchInputProps) {
  const hasValue =
    typeof value === "string" && value.length > 0;

  return (
    <div className="relative w-full">
      <span
        className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-lg text-slate-400"
        aria-hidden="true"
      >
        🔍
      </span>

      <input
        {...props}
        value={value}
        className={`w-full rounded-xl border border-slate-200 bg-white py-3 pl-11 pr-11 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:placeholder:text-slate-500 ${className}`}
      />

      {hasValue && onClear && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear search"
          className="absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          ×
        </button>
      )}
    </div>
  );
}