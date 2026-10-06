import { HTMLAttributes } from "react";

export default function EmptyState({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-sm text-gray-400 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}