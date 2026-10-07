import type { ReactNode } from "react";

interface PillProps {
  children: ReactNode;
  active?: boolean;
  onClick?: () => void;
}

export default function Pill({
  children,
  active = false,
  onClick,
}: PillProps) {
  const className = `inline-flex items-center rounded-full px-4 py-2 text-sm font-medium transition ${
    active
      ? "bg-teal-500 text-white shadow-sm"
      : "bg-slate-100 text-slate-600 hover:bg-teal-50 hover:text-teal-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-teal-950 dark:hover:text-teal-300"
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