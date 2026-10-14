"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import notificationService from "../services/notification.service";

const navigationItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Activities", href: "/activities" },
  { label: "Events", href: "/events" },
  { label: "Connections", href: "/connections" },
  { label: "Recommendations", href: "/recommendations" },
  { label: "Communities", href: "/communities" },
  { label: "Creators", href: "/creators" },
];

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Check dark mode preference
    const savedTheme = typeof window !== "undefined" ? localStorage.getItem("vynk-theme") : null;
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    }

    // Check auth status
    const token = typeof window !== "undefined" ? localStorage.getItem("vynk_token") : null;
    const authed = !!token;

    // Subscribe to live unread count updates
    let unsubscribe = () => {};
    if (authed) {
      unsubscribe = notificationService.subscribeUnreadCount((count) => {
        setUnreadCount(count);
      });
      notificationService.refreshUnreadCount().catch(() => {});
    }

    queueMicrotask(() => {
      setIsAuthenticated(authed);
      if (savedTheme === "dark") {
        setIsDark(true);
      }
      if (!authed) {
        setUnreadCount(0);
        notificationService.setUnreadCount(0);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [pathname]);

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

  const handleLogout = () => {
    notificationService.setUnreadCount(0);
    setUnreadCount(0);
    localStorage.removeItem("vynk_token");
    localStorage.removeItem("vynk_user");
    setIsAuthenticated(false);
    router.push("/login");
  };

  const isAuthPage = pathname === "/login" || pathname === "/signup";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          href="/"
          className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white"
        >
          Vynk<span className="text-teal-500">.</span>
        </Link>

        {/* Minimal header on login/signup */}
        {isAuthPage ? (
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-sm font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
            >
              ← Back to Home
            </Link>
          </div>
        ) : (
          <>
            {/* Desktop Navigation */}
            <nav className="hidden lg:block">
              <ul className="flex items-center gap-1">
                {navigationItems.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href === "/connections" && pathname === "/matches");

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
                className="relative rounded-xl px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
              >
                Notifications
                {isAuthenticated && unreadCount > 0 && (
                  <span
                    data-testid="notification-badge"
                    className="ml-1.5 inline-flex items-center justify-center rounded-full bg-teal-500 px-1.5 py-0.5 text-xs font-bold leading-none text-white dark:bg-teal-400 dark:text-slate-950"
                  >
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </span>
                )}
              </Link>

              <button
                type="button"
                onClick={toggleTheme}
                aria-label="Toggle light and dark mode"
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-teal-300 hover:text-teal-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-teal-500 dark:hover:text-teal-300 cursor-pointer"
              >
                {isDark ? "☀️ Light" : "🌙 Dark"}
              </button>

              {isAuthenticated ? (
                <div className="flex items-center gap-2">
                  <Link
                    href="/profile"
                    className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
                  >
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-400 text-xs font-bold text-slate-900">
                      V
                    </span>
                    Profile
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:border-slate-700 dark:hover:bg-slate-800 cursor-pointer"
                  >
                    Log Out
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950"
                  >
                    Get Started
                  </Link>
                </div>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              type="button"
              aria-label="Toggle navigation menu"
              aria-expanded={isMenuOpen}
              onClick={() => setIsMenuOpen((current) => !current)}
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-teal-300 hover:text-teal-600 dark:border-slate-700 dark:text-slate-200 lg:hidden cursor-pointer"
            >
              {isMenuOpen ? "Close" : "Menu"}
            </button>
          </>
        )}
      </div>

      {/* Mobile Drawer Menu */}
      {isMenuOpen && !isAuthPage && (
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
                  className="flex items-center justify-between rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  <span>Notifications</span>
                  {isAuthenticated && unreadCount > 0 && (
                    <span
                      data-testid="mobile-notification-badge"
                      className="inline-flex items-center justify-center rounded-full bg-teal-500 px-2 py-0.5 text-xs font-bold leading-none text-white dark:bg-teal-400 dark:text-slate-950"
                    >
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </Link>
              </li>

              {isAuthenticated ? (
                <>
                  <li>
                    <Link
                      href="/profile"
                      onClick={() => setIsMenuOpen(false)}
                      className="block rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
                    >
                      Profile
                    </Link>
                  </li>
                  <li>
                    <button
                      type="button"
                      onClick={() => {
                        setIsMenuOpen(false);
                        handleLogout();
                      }}
                      className="block w-full rounded-xl border border-rose-200 px-4 py-3 text-left text-sm font-semibold text-rose-600"
                    >
                      Log Out
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <Link
                      href="/login"
                      onClick={() => setIsMenuOpen(false)}
                      className="block rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-200"
                    >
                      Sign In
                    </Link>
                  </li>
                  <li>
                    <Link
                      href="/signup"
                      onClick={() => setIsMenuOpen(false)}
                      className="block rounded-xl bg-teal-500 px-4 py-3 text-sm font-semibold text-slate-950"
                    >
                      Create Account
                    </Link>
                  </li>
                </>
              )}
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
}