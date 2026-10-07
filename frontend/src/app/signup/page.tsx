import Link from "next/link";

export default function SignupPage() {
  return (
    <main className="min-h-[calc(100vh-73px)] bg-slate-50">
      <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl lg:grid-cols-2">
        <section className="flex items-center justify-center px-6 py-10 sm:px-8 lg:order-2 lg:px-16">
          <div className="w-full max-w-md rounded-3xl bg-white p-7 shadow-sm ring-1 ring-slate-200 sm:p-9">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 text-xl font-bold text-white">
              V
            </div>

            <div className="mt-7">
              <p className="text-sm font-medium text-pink-600">
                Start your Vynk
              </p>

              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                Create your account
              </h1>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Tell us a little about yourself and start discovering people,
                activities, and experiences.
              </p>
            </div>

            <form className="mt-8 space-y-5">
              <div>
                <label
                  htmlFor="name"
                  className="text-sm font-medium text-slate-700"
                >
                  Your name
                </label>

                <input
                  id="name"
                  type="text"
                  placeholder="What should we call you?"
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-pink-400 focus:ring-4 focus:ring-pink-50"
                />
              </div>

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
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-pink-400 focus:ring-4 focus:ring-pink-50"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-slate-700"
                >
                  Create a password
                </label>

                <input
                  id="password"
                  type="password"
                  placeholder="Choose a secure password"
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-pink-400 focus:ring-4 focus:ring-pink-50"
                />
              </div>

              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-pink-500 focus:ring-pink-400"
                />

                <span className="text-xs leading-5 text-slate-500">
                  I agree to the Vynk terms and understand how my information
                  will be used.
                </span>
              </label>

              <button
                type="submit"
                className="w-full rounded-xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-pink-500"
              >
                Create account
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
              className="w-full rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-pink-200 hover:bg-pink-50"
            >
              Sign up with Google
            </button>

            <p className="mt-7 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-semibold text-pink-600 hover:text-purple-600"
              >
                Sign in
              </Link>
            </p>
          </div>
        </section>

        <section className="relative hidden overflow-hidden bg-gradient-to-br from-orange-400 via-pink-500 to-purple-600 p-12 text-white lg:order-1 lg:flex lg:flex-col lg:justify-center">
          <div className="relative z-10 max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-wider text-white/75">
              Welcome to Vynk
            </p>

            <h2 className="mt-4 text-5xl font-bold leading-tight">
              Meet people.
              <br />
              Find your thing.
              <br />
              Make it yours.
            </h2>

            <p className="mt-6 max-w-lg text-base leading-7 text-white/85">
              Vynk helps you discover activities, communities, events, and
              connections that fit who you are.
            </p>

            <div className="mt-8 grid max-w-md grid-cols-2 gap-3">
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-lg font-bold">Discover</p>
                <p className="mt-1 text-sm text-white/70">
                  Find experiences you enjoy.
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-lg font-bold">Connect</p>
                <p className="mt-1 text-sm text-white/70">
                  Meet people who get you.
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-lg font-bold">Explore</p>
                <p className="mt-1 text-sm text-white/70">
                  Try something new.
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
                <p className="text-lg font-bold">Belong</p>
                <p className="mt-1 text-sm text-white/70">
                  Find your people.
                </p>
              </div>
            </div>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/10" />
          <div className="absolute -bottom-24 -left-16 h-56 w-56 rounded-full bg-white/10" />
        </section>
      </div>
    </main>
  );
}