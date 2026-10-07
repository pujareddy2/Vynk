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
];

export default function Navigation() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          href="/"
          className="text-2xl font-bold tracking-tight text-slate-900"
        >
          Vynk<span className="text-teal-500">.</span>
        </Link>

        <nav className="hidden lg:block">
          <ul className="flex items-center gap-1">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
                      isActive
                        ? "bg-teal-50 text-teal-700"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            href="/notifications"
            className="rounded-xl px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
          >
            Notifications
          </Link>

          <Link
            href="/profile"
            className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-400 text-xs font-bold text-slate-900">
              A
            </span>
            Profile
          </Link>
        </div>

        <button
          type="button"
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
          onClick={() => setIsMenuOpen((current) => !current)}
          className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-teal-300 hover:text-teal-600 lg:hidden"
        >
          {isMenuOpen ? "Close" : "Menu"}
        </button>
      </div>

      {isMenuOpen && (
        <div className="border-t border-slate-200 bg-white px-6 py-4 lg:hidden">
          <nav>
            <ul className="grid gap-2 sm:grid-cols-2">
              {navigationItems.map((item) => {
                const isActive = pathname === item.href;

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setIsMenuOpen(false)}
                      className={`block rounded-xl px-4 py-3 text-sm font-medium transition ${
                        isActive
                          ? "bg-teal-50 text-teal-700"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}

              <li>
                <Link
                  href="/notifications"
                  onClick={() => setIsMenuOpen(false)}
                  className="block rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Notifications
                </Link>
              </li>

              <li>
                <Link
                  href="/profile"
                  onClick={() => setIsMenuOpen(false)}
                  className="block rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
                >
                  Profile
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
}