import type { ReactNode } from "react";

interface ChipProps {
  children: ReactNode;
  selected?: boolean;
  onClick?: () => void;
}

export default function Chip({
  children,
  selected = false,
  onClick,
}: ChipProps) {
  const className = `inline-flex items-center rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
    selected
      ? "border-teal-500 bg-teal-500 text-white"
      : "border-slate-200 bg-white text-slate-600 hover:border-teal-300 hover:text-teal-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-teal-500 dark:hover:text-teal-300"
  }`;

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={className}
      >
        {children}
      </button>
    );
  }

  return <span className={className}>{children}</span>;
}