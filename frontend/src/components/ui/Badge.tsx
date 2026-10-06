import { HTMLAttributes } from "react";

export default function Badge({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={`inline-flex items-center rounded-full bg-white/10 px-3 py-1.5 text-xs font-medium text-gray-300 ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}