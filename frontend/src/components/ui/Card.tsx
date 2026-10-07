import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export default function Card({
  hover = true,
  className = "",
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900 ${
        hover
          ? "transition-all duration-300 hover:-translate-y-1 hover:border-teal-200 hover:shadow-lg dark:hover:border-teal-800"
          : ""
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}