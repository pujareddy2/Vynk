import { HTMLAttributes } from "react";

export default function Avatar({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-white/10 text-sm font-semibold text-white ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}