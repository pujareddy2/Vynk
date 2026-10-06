"use client";

import { ReactNode } from "react";

type ToastProps = {
  message: ReactNode;
  type?: "success" | "error" | "info";
};

export default function Toast({
  message,
  type = "info",
}: ToastProps) {
  const styles = {
    success: "border-green-500/20 text-green-300",
    error: "border-red-500/20 text-red-300",
    info: "border-white/10 text-gray-300",
  };

  return (
    <div
      role="status"
      className={`fixed bottom-6 right-6 z-50 rounded-xl border bg-[#11161d] px-5 py-3 text-sm shadow-xl ${styles[type]}`}
    >
      {message}
    </div>
  );
}