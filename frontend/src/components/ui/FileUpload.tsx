import type { ChangeEvent, InputHTMLAttributes } from "react";

interface FileUploadProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  helperText?: string;
  onFileChange?: (file: File | null) => void;
}

export default function FileUpload({
  label,
  helperText,
  onFileChange,
  id,
  ...props
}: FileUploadProps) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFileChange?.(event.target.files?.[0] ?? null);
  };

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={id}
          className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200"
        >
          {label}
        </label>
      )}

      <label
        htmlFor={id}
        className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center transition hover:border-teal-400 hover:bg-teal-50/40 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-teal-500 dark:hover:bg-teal-950/30"
      >
        <span className="text-3xl">📎</span>

        <span className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
          Choose a file
        </span>

        <span className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Click to browse from your device
        </span>

        <input
          {...props}
          id={id}
          type="file"
          onChange={handleChange}
          className="sr-only"
        />
      </label>

      {helperText && (
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          {helperText}
        </p>
      )}
    </div>
  );
}