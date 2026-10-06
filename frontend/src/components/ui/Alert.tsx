import { HTMLAttributes } from "react";

export default function Alert({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="alert"
      className={`rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-300 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}