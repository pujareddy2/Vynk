import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="min-h-[calc(100vh-73px)] bg-slate-50">
      <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl lg:grid-cols-2">
        <section className="hidden flex-col justify-center px-8 py-12 lg:flex lg:px-16">
          <div className="max-w-xl">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 text-2xl font-bold text-white shadow-md">
              V
            </div>

            <p className="mt-8 text-sm font-semibold uppercase tracking-wider text-purple-600">
              Welcome back
            </p>

            <h1 className="mt-3 text-5xl font-bold leading-tight text-slate-900">
              Your people,
              <br />
              your moments,
              <br />
              your Vynk.
            </h1>

            <p className="mt-6 max-w-lg text-base leading-7 text-slate-500">
              Pick up where you left off and discover activities, communities,
              events, and people that match your vibe.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-full bg-purple-50 px-4 py-2 text-sm font-medium text-purple-600">
                Discover
              </span>

              <span className="rounded-full bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-600">
                Connect
              </span>

              <span className="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">
                Belong
              </span>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-6 py-10 sm:px-8">
          <div className="w-full max-w-md rounded-3xl bg-white p-7 shadow-sm ring-1 ring-slate-200 sm:p-9">
            <div className="lg:hidden">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 text-xl font-bold text-white">
                V
              </div>
            </div>

            <div className="mt-7">
              <p className="text-sm font-medium text-purple-600">
                Welcome back
              </p>

              <h2 className="mt-2 text-3xl font-bold text-slate-900">
                Sign in to Vynk
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Continue discovering people and experiences that feel right
                for you.
              </p>
            </div>

            <form className="mt-8 space-y-5">
              <div>
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-slate-700"
                >
                  Email address
                </label>

                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-400 focus:ring-4 focus:ring-purple-50"
                />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="text-sm font-medium text-slate-700"
                  >
                    Password
                  </label>

                  <button
                    type="button"
                    className="text-xs font-semibold text-purple-600 hover:text-indigo-600"
                  >
                    Forgot password?
                  </button>
                </div>

                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-400 focus:ring-4 focus:ring-purple-50"
                />
              </div>

              <button
                type="submit"
                className="w-full rounded-xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-purple-600"
              >
                Sign in
              </button>
            </form>

            <div className="my-7 flex items-center gap-4">
              <div className="h-px flex-1 bg-slate-200" />

              <span className="text-xs text-slate-400">
                or
              </span>

              <div className="h-px flex-1 bg-slate-200" />
            </div>

            <button
              type="button"
              className="w-full rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-purple-200 hover:bg-purple-50"
            >
              Continue with Google
            </button>

            <p className="mt-7 text-center text-sm text-slate-500">
              Don't have an account?{" "}
              <Link
                href="/signup"
                className="font-semibold text-purple-600 hover:text-indigo-600"
              >
                Create one
              </Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}