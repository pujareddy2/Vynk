import { HTMLAttributes } from "react";

export default function Card({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-3xl border border-white/10 bg-white/[0.03] p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}