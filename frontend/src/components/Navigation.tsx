"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

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
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem("vynk-theme");

    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
      setIsDark(true);
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = !isDark;

    setIsDark(nextTheme);

    if (nextTheme) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("vynk-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("vynk-theme", "light");
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur dark:border-slate-700/80 dark:bg-slate-950/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          href="/"
          className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white"
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
                        ? "bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
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
            className="rounded-xl px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            Notifications
          </Link>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle light and dark mode"
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-teal-300 hover:text-teal-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-teal-500 dark:hover:text-teal-300"
          >
            {isDark ? "☀️ Light" : "🌙 Dark"}
          </button>

          <Link
            href="/profile"
            className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
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
          className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-teal-300 hover:text-teal-600 dark:border-slate-700 dark:text-slate-200 lg:hidden"
        >
          {isMenuOpen ? "Close" : "Menu"}
        </button>
      </div>

      {isMenuOpen && (
        <div className="border-t border-slate-200 bg-white px-6 py-4 dark:border-slate-700 dark:bg-slate-950 lg:hidden">
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
                          ? "bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
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
                  className="block rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  Notifications
                </Link>
              </li>

              <li>
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="block w-full rounded-xl border border-slate-200 px-4 py-3 text-left text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200"
                >
                  {isDark ? "☀️ Switch to Light Mode" : "🌙 Switch to Dark Mode"}
                </button>
              </li>

              <li>
                <Link
                  href="/profile"
                  onClick={() => setIsMenuOpen(false)}
                  className="block rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
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