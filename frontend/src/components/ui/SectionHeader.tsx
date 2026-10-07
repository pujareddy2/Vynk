import type { ReactNode } from "react";

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function SectionHeader({
  eyebrow,
  title,
  description,
  action,
}: SectionHeaderProps) {
  return (
    <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-2xl">
        {eyebrow && (
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal-600 dark:text-teal-400">
            {eyebrow}
          </p>
        )}

        <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {title}
        </h2>

        {description && (
          <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {description}
          </p>
        )}
      </div>

      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}