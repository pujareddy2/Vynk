"use client";

import { ReactNode, useState } from "react";

type DropdownProps = {
  label: string;
  children: ReactNode;
};

export default function Dropdown({
  label,
  children,
}: DropdownProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
      >
        {label}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 min-w-40 rounded-xl border border-white/10 bg-[#11161d] p-2 shadow-xl">
          {children}
        </div>
      )}
    </div>
  );
}