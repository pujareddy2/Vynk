"use client";

import type { InputHTMLAttributes } from "react";

interface SwitchProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
}

export default function Switch({
  label,
  id,
  className = "",
  ...props
}: SwitchProps) {
  return (
    <label
      htmlFor={id}
      className="flex cursor-pointer items-center justify-between gap-4 text-sm text-slate-700 dark:text-slate-300"
    >
      <span>{label}</span>

      <span className="relative inline-flex shrink-0 items-center">
        <input
          id={id}
          type="checkbox"
          className={`peer sr-only ${className}`}
          {...props}
        />

        <span className="h-6 w-11 rounded-full bg-slate-300 transition-colors peer-checked:bg-teal-500 peer-focus-visible:ring-4 peer-focus-visible:ring-teal-500/20 dark:bg-slate-600" />

        <span className="pointer-events-none absolute left-1 h-4 w-4 rounded-full bg-white shadow-sm transition-transform peer-checked:translate-x-5" />
      </span>
    </label>
  );
}