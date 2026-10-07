"use client";

import { useState } from "react";

interface Tab {
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: number;
}

export default function Tabs({
  tabs,
  defaultTab = 0,
}: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return (
    <div className="w-full">
      <div className="flex gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1 dark:bg-slate-800">
        {tabs.map((tab, index) => (
          <button
            key={tab.label}
            type="button"
            onClick={() => setActiveTab(index)}
            className={`shrink-0 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all ${
              activeTab === index
                ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tabs[activeTab]?.content}
      </div>
    </div>
  );
}