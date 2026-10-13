"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import authService from "../../services/auth.service";
import userService from "../../services/user.service";
import { detectLiveLocation } from "../../services/location.service";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pre-warm live location detection in background on page mount
  useState(() => {
    detectLiveLocation().catch(() => {});
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!agreeTerms) {
      setError("Please agree to the Vynk terms of service to create your account.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify both password fields.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Seamlessly detect live location in background (no button needed)
      let liveLocality = "";
      try {
        const detected = await detectLiveLocation();
        if (detected?.locality) {
          liveLocality = detected.locality;
        }
      } catch {}

      // 2. Call Backend API POST /auth/register with live location
      const user = await authService.register(
        email.trim().toLowerCase(),
        password,
        confirmPassword,
        liveLocality || undefined
      );

      // 3. Automatically log in to get access token via POST /auth/login
      const loginRes = await authService.login(email.trim().toLowerCase(), password);

      // 4. Ensure backend profile display_name and live location are synced
      try {
        await userService.updateProfile({
          display_name: name.trim() || email.split("@")[0],
          approx_locality: liveLocality || undefined,
        });
      } catch {}

      // 5. Save to localStorage with real live location
      localStorage.setItem(
        "vynk_user",
        JSON.stringify({
          user_id: user.user_id || loginRes.user_id,
          name: name.trim() || email.split("@")[0],
          email: email.trim().toLowerCase(),
          location: liveLocality || "",
        })
      );

      // 6. Seamlessly guide user to Profile Customization
      router.push("/profile?onboarding=true");
    } catch (err: any) {
      setError(err?.message || "Registration failed. This email may already be registered.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[calc(100vh-65px)] bg-slate-50 dark:bg-slate-950 flex items-center justify-center py-10 px-4 transition-colors duration-300">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 rounded-3xl bg-white shadow-xl ring-1 ring-slate-200 overflow-hidden dark:bg-slate-900 dark:ring-slate-800">
        {/* Form Section */}
        <section className="flex flex-col justify-center p-8 sm:p-12 order-2 lg:order-1">
          <div className="w-full max-w-md mx-auto">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                Join the Community · Step 1 of 2
              </p>
              <h1 className="mt-1 text-3xl font-extrabold text-slate-900 dark:text-white">
                Create your account
              </h1>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Start discovering people, activities, and local experiences near you.
              </p>
            </div>

            {error && (
              <div className="mt-5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 p-4 text-sm font-semibold text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 flex items-start gap-2.5">
                <span className="text-base">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {/* Name Field */}
              <div>
                <label
                  htmlFor="name"
                  className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block"
                >
                  Your Name
                </label>
                <input
                  id="name"
                  required
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Vikram Reddy"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* Email Field */}
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
                  placeholder="you@example.com"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              {/* Password Field */}
              <div>
                <label
                  htmlFor="password"
                  className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block"
                >
                  Password (min 6 characters)
                </label>
                <div className="relative mt-1.5">
                  <input
                    id="password"
                    required
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Choose a secure password"
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

              {/* Confirm Password Field */}
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block"
                >
                  Confirm Password
                </label>
                <div className="relative mt-1.5">
                  <input
                    id="confirmPassword"
                    required
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter your password"
                    className={`w-full rounded-xl border bg-white px-4 py-3 text-sm text-slate-900 outline-none transition pr-11 dark:bg-slate-800 dark:text-white ${
                      confirmPassword && confirmPassword !== password
                        ? "border-rose-300 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 dark:border-rose-800"
                        : "border-slate-200 focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 dark:border-slate-700"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm cursor-pointer"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  >
                    {showConfirmPassword ? "🙈" : "👁️"}
                  </button>
                </div>
                {confirmPassword && confirmPassword !== password && (
                  <p className="mt-1 text-xs text-rose-500 font-medium">
                    ✕ Passwords do not match yet
                  </p>
                )}
                {confirmPassword && confirmPassword === password && (
                  <p className="mt-1 text-xs text-teal-600 dark:text-teal-400 font-medium">
                    ✓ Passwords match
                  </p>
                )}
              </div>

              {/* Terms Agreement */}
              <label className="flex items-start gap-3 pt-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-400 dark:border-slate-700 dark:bg-slate-800"
                />
                <span className="text-xs leading-5 text-slate-600 dark:text-slate-400">
                  I agree to the Vynk terms of service, offline community safety guidelines, and code of conduct.
                </span>
              </label>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-teal-400 py-3.5 text-sm font-bold text-slate-950 shadow-md shadow-teal-500/20 transition hover:bg-teal-300 active:scale-[0.99] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                    <span>Creating your account...</span>
                  </>
                ) : (
                  <span>Continue to Profile Setup →</span>
                )}
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400"
              >
                Sign in
              </Link>
            </p>
          </div>
        </section>

        {/* Branding Hero Section */}
        <section className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-teal-950 p-12 text-white order-1 lg:order-2 border-l border-slate-800">
          <div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-400 text-2xl font-black text-slate-950 shadow-lg shadow-teal-500/20">
              V
            </div>

            <p className="mt-10 text-xs font-bold uppercase tracking-[0.25em] text-teal-400">
              Join Local Communities
            </p>

            <h2 className="mt-3 text-4xl font-extrabold leading-tight">
              Turn shared interests
              <br />
              into real-world
              <br />
              <span className="text-teal-400">adventures.</span>
            </h2>

            <p className="mt-6 text-sm leading-relaxed text-slate-300 max-w-md">
              Create your profile to match with nearby badminton players, cycling enthusiasts, photography lovers, and local creators.
            </p>
          </div>

          <div className="space-y-4 pt-8 border-t border-slate-800/80">
            <div className="flex items-center gap-3 text-xs text-slate-300">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/20 text-teal-300 font-bold">1</span>
              <span>Create account with email &amp; password</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-300">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/20 text-teal-300 font-bold">2</span>
              <span>Pick activities &amp; weekly free time in Profile</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-300">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/20 text-teal-300 font-bold">3</span>
              <span>Swipe, connect, and split venue costs automatically</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}