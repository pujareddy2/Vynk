"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import authService from "../../services/auth.service";
import userService from "../../services/user.service";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Blank initial state for new and returning users
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Call Backend API POST /auth/login
      const res = await authService.login(email.trim(), password);

      if (rememberMe) {
        localStorage.setItem("vynk_remember_email", email.trim());
      } else {
        localStorage.removeItem("vynk_remember_email");
      }

      // 2. Fetch live profile from GET /profile/me to seed local user data
      try {
        const profile = await userService.getProfileMe();
        if (profile) {
          localStorage.setItem(
            "vynk_user",
            JSON.stringify({
              user_id: profile.user_id,
              email: profile.email,
              name: profile.display_name || email.split("@")[0],
              location: profile.approx_locality || "Hyderabad",
              avatar: profile.avatar_url || null,
              bio: profile.bio || "",
            })
          );

          // Smart check: If user hasn't completed their profile interests yet, guide to onboarding!
          if (!profile.interests || profile.interests.length === 0) {
            router.push("/profile?onboarding=true");
            return;
          }
        }
      } catch {
        // Fallback user object if profile fetch fails
        localStorage.setItem(
          "vynk_user",
          JSON.stringify({
            user_id: res.user_id,
            email: res.email,
            name: email.split("@")[0].charAt(0).toUpperCase() + email.split("@")[0].slice(1),
            location: "Hyderabad",
          })
        );
      }

      // 3. Smooth transition to Dashboard
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Invalid email or password. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[calc(100vh-65px)] bg-slate-50 dark:bg-slate-950 flex items-center justify-center py-10 px-4 transition-colors duration-300">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 rounded-3xl bg-white shadow-xl ring-1 ring-slate-200 overflow-hidden dark:bg-slate-900 dark:ring-slate-800">
        {/* Left Branding Hero Section */}
        <section className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-teal-950 p-12 text-white border-r border-slate-800">
          <div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-400 text-2xl font-black text-slate-950 shadow-lg shadow-teal-500/20">
              V
            </div>

            <p className="mt-10 text-xs font-bold uppercase tracking-[0.25em] text-teal-400">
              Welcome Back to Vynk
            </p>

            <h1 className="mt-3 text-4xl font-extrabold leading-tight">
              Real plans.
              <br />
              Verified people.
              <br />
              <span className="text-teal-400">Zero friction.</span>
            </h1>

            <p className="mt-6 text-sm leading-relaxed text-slate-300 max-w-md">
              Sign in to pick up right where you left off — check your badminton sparring groups, community notifications, and split-cost plans.
            </p>
          </div>

          <div className="pt-8 border-t border-slate-800/80">
            <div className="flex items-center gap-3">
              <span className="flex h-2.5 w-2.5 rounded-full bg-teal-400 animate-pulse" />
              <p className="text-xs font-semibold text-slate-400">
                Connected to Localy Engine · FastAPI + PostgreSQL Active
              </p>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300 backdrop-blur">
                🎴 Swipe Deck
              </span>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300 backdrop-blur">
                ⚡ Instant Matches
              </span>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300 backdrop-blur">
                💰 Auto Split-Cost
              </span>
            </div>
          </div>
        </section>

        {/* Right Form Section */}
        <section className="flex flex-col justify-center p-8 sm:p-12">
          <div className="w-full max-w-md mx-auto">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                Account Access
              </p>
              <h2 className="mt-1 text-3xl font-extrabold text-slate-900 dark:text-white">
                Sign in to your account
              </h2>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Enter your registered credentials to access your dashboard.
              </p>
            </div>

            {error && (
              <div className="mt-5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 p-4 text-sm font-semibold text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 flex items-start gap-2.5">
                <span className="text-base">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {/* Email Address Field */}
              <div>
                <label
                  htmlFor="email"
                  className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block"
                >
                  Email Address
                </label>
                <input
                  id="email"
                  required
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@example.com"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* Password Field */}
              <div>
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider"
                  >
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => alert("To reset your password, contact admin or register a new verified account.")}
                    className="text-xs font-semibold text-teal-600 hover:text-teal-700 dark:text-teal-400 cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative mt-1.5">
                  <input
                    id="password"
                    required
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm cursor-pointer"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "🙈" : "👁️"}
                  </button>
                </div>
              </div>

              {/* Remember Me Toggle */}
              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-400 dark:border-slate-700 dark:bg-slate-800"
                  />
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    Remember my email
                  </span>
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-teal-400 py-3.5 text-sm font-bold text-slate-950 shadow-md shadow-teal-500/20 transition hover:bg-teal-300 active:scale-[0.99] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                    <span>Signing in to Vynk...</span>
                  </>
                ) : (
                  <span>Sign in to Dashboard →</span>
                )}
              </button>
            </form>



            <p className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
              New to Vynk?{" "}
              <Link
                href="/signup"
                className="font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400"
              >
                Create an account
              </Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}