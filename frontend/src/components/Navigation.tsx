"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navigationItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Activities", href: "/activities" },
  { label: "Events", href: "/events" },
  { label: "Matches", href: "/matches" },
  { label: "Recommendations", href: "/recommendations" },
  { label: "Communities", href: "/communities" },
  { label: "Creators", href: "/creators" },
  { label: "Notifications", href: "/notifications" },
  { label: "Profile", href: "/profile" },
];

export default function Navigation() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link
          href="/"
          className="bg-gradient-to-r from-teal-500 to-cyan-500 bg-clip-text text-xl font-bold text-transparent"
        >
          Vynk
        </Link>

        <div className="hidden md:flex">
          <ul className="flex items-center gap-6">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`text-sm font-medium transition ${
                      isActive
                        ? "text-teal-600"
                        : "text-slate-600 hover:text-teal-600"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        <button
          type="button"
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:border-teal-400 hover:text-teal-600 md:hidden"
        >
          Menu
        </button>
      </div>

      {isMenuOpen && (
        <div className="border-t border-slate-200 bg-white px-6 py-4 md:hidden">
          <ul className="flex flex-col gap-4">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsMenuOpen(false)}
                    className={`block text-sm font-medium ${
                      isActive
                        ? "text-teal-600"
                        : "text-slate-600 hover:text-teal-600"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </nav>
  );
}