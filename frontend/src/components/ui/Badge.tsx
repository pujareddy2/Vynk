import type { HTMLAttributes } from "react";

type BadgeVariant = "teal" | "purple" | "gold" | "pink" | "slate";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  teal:
    "bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300",
  purple:
    "bg-violet-50 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  gold:
    "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  pink:
    "bg-pink-50 text-pink-700 dark:bg-pink-950 dark:text-pink-300",
  slate:
    "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

export default function Badge({
  variant = "teal",
  className = "",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}