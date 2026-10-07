import type { ReactNode } from "react";

type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
}

const variantClasses: Record<
  AlertVariant,
  {
    container: string;
    icon: string;
  }
> = {
  info: {
    container:
      "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200",
    icon: "ℹ️",
  },
  success: {
    container:
      "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200",
    icon: "✓",
  },
  warning: {
    container:
      "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200",
    icon: "⚠️",
  },
  error: {
    container:
      "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200",
    icon: "!",
  },
};

export default function Alert({
  variant = "info",
  title,
  children,
}: AlertProps) {
  const styles = variantClasses[variant];

  return (
    <div
      role="alert"
      className={`flex gap-3 rounded-2xl border px-4 py-4 text-sm ${styles.container}`}
    >
      <span
        aria-hidden="true"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/70 text-xs font-bold dark:bg-slate-900/50"
      >
        {styles.icon}
      </span>

      <div className="min-w-0">
        {title && (
          <p className="font-semibold">
            {title}
          </p>
        )}

        <div className={title ? "mt-1" : ""}>
          {children}
        </div>
      </div>
    </div>
  );
}