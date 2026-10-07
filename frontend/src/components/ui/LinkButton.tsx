import Link from "next/link";
import type { ComponentProps } from "react";

interface LinkButtonProps extends ComponentProps<typeof Link> {
  variant?: "primary" | "secondary" | "outline";
}

const variantClasses = {
  primary:
    "bg-teal-500 text-white hover:bg-teal-600",
  secondary:
    "bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200",
  outline:
    "border border-slate-200 bg-white text-slate-700 hover:border-teal-400 hover:text-teal-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-teal-500 dark:hover:text-teal-300",
};

export default function LinkButton({
  variant = "primary",
  className = "",
  children,
  ...props
}: LinkButtonProps) {
  return (
    <Link
      {...props}
      className={`inline-flex items-center justify-center rounded-xl px-5 py-3 text-sm font-semibold shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${variantClasses[variant]} ${className}`}
    >
      {children}
    </Link>
  );
}