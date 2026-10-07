import type { InputHTMLAttributes } from "react";

interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
}

export default function Checkbox({
  label,
  id,
  className = "",
  ...props
}: CheckboxProps) {
  return (
    <label
      htmlFor={id}
      className="flex cursor-pointer items-center gap-3 text-sm text-slate-700 dark:text-slate-300"
    >
      <input
        id={id}
        type="checkbox"
        className={`h-4 w-4 rounded border-slate-300 text-teal-500 accent-teal-500 focus:ring-2 focus:ring-teal-500/20 dark:border-slate-600 ${className}`}
        {...props}
      />

      <span>{label}</span>
    </label>
  );
}