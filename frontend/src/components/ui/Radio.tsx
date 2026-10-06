import { InputHTMLAttributes } from "react";

export default function Radio({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="radio"
      className={`h-4 w-4 accent-white ${className}`}
      {...props}
    />
  );
}