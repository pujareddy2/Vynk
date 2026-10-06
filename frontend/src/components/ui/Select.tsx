import { SelectHTMLAttributes } from "react";

export default function Select({
  className = "",
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`w-full rounded-xl border border-white/10 bg-[#11161d] px-4 py-3 text-white outline-none transition focus:border-white/30 ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}