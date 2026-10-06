"use client";

import { ReactNode } from "react";

type DrawerProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

export default function Drawer({
  open,
  onClose,
  children,
}: DrawerProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="absolute bottom-0 left-0 w-full rounded-t-3xl border-t border-white/10 bg-[#11161d] p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}