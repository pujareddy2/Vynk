"use client";

import { ReactNode } from "react";

type DialogProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
};

export default function Dialog({
  open,
  onClose,
  title,
  children,
}: DialogProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-3xl border border-white/10 bg-[#11161d] p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        {title && <h2 className="mb-4 text-xl font-semibold">{title}</h2>}

        {children}
      </div>
    </div>
  );
}