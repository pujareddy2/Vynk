"use client";

import type { ReactNode } from "react";
import { useState } from "react";

interface TooltipProps {
  content: string;
  children: ReactNode;
}

export default function Tooltip({
  content,
  children,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}

      {isVisible && (
        <span
          role="tooltip"
          className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white shadow-lg dark:bg-white dark:text-slate-900"
        >
          {content}
        </span>
      )}
    </span>
  );
}