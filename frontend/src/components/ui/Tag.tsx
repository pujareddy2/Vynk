import type { HTMLAttributes } from "react";

interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
}

export default function Tag({
  children,
  className = "",
  ...props
}: TagProps) {
  return (
    <span
      {...props}
      className={`inline-flex items-center rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 ${className}`}
    >
      {children}
    </span>
  );
}