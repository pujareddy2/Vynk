import PageContainer from "../../components/PageContainer";

const quickActions = [
  {
    title: "Discover activities",
    description: "Find experiences that match your interests and mood.",
    icon: "✦",
  },
  {
    title: "Meet your people",
    description: "Connect with people who share your interests.",
    icon: "♡",
  },
  {
    title: "Explore events",
    description: "Discover elegant moments and memorable plans.",
    icon: "◈",
  },
];

const trending = [
  {
    title: "Photography Walk",
    category: "Creative",
    people: "10 people interested",
    icon: "📷",
  },
  {
    title: "Weekend Cycling",
    category: "Outdoor",
    people: "8 people interested",
    icon: "🚴",
  },
  {
    title: "Coffee & Conversations",
    category: "Social",
    people: "12 people interested",
    icon: "☕",
  },
];

export default function DashboardPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-violet-900 p-8 text-white shadow-xl md:p-10">
          <div className="relative z-10 max-w-3xl">
            <div className="flex items-center gap-3">
              <span className="h-px w-8 bg-amber-300" />

              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-amber-200">
                Your Vynk space
              </p>
            </div>

            <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
              Make today
              <br />
              beautifully yours.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
              Discover meaningful experiences, interesting people, and
              moments that fit your world.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="button"
                className="rounded-xl bg-amber-100 px-5 py-3 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-white"
              >
                Start exploring
              </button>

              <button
                type="button"
                className="rounded-xl border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/15"
              >
                View recommendations
              </button>
            </div>
          </div>

          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full border border-amber-200/10" />
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-violet-500/10" />
          <div className="absolute -bottom-28 right-32 h-64 w-64 rounded-full border border-white/10" />

          <div className="absolute right-12 top-12 hidden h-2 w-2 rounded-full bg-amber-300 md:block" />
          <div className="absolute right-28 top-24 hidden h-1.5 w-1.5 rounded-full bg-white/50 md:block" />
        </section>

        <section>
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-600">
              Curated for you
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
              Where would you like to begin?
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {quickActions.map((action) => (
              <article
                key={action.title}
                className="group rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 transition duration-200 hover:-translate-y-1 hover:shadow-lg"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-50 to-violet-50 text-xl text-violet-700">
                  {action.icon}
                </div>

                <h3 className="mt-5 text-xl font-semibold text-slate-900">
                  {action.title}
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {action.description}
                </p>

                <button
                  type="button"
                  className="mt-5 text-sm font-semibold text-violet-700 transition group-hover:text-amber-600"
                >
                  Explore →
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl bg-gradient-to-br from-indigo-950 to-violet-900 p-7 text-white shadow-md">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">
                Your Vynk vibe
              </p>

              <span className="text-amber-300">✦</span>
            </div>

            <h2 className="mt-5 text-2xl font-semibold">
              Curious & social
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-300">
              You enjoy discovering new places, meeting interesting people,
              and keeping life full of experiences.
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {["Travel", "Music", "Coffee", "Photography"].map(
                (interest) => (
                  <span
                    key={interest}
                    className="rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-200"
                  >
                    {interest}
                  </span>
                ),
              )}
            </div>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 lg:col-span-2">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-600">
                  What's happening
                </p>

                <h2 className="mt-2 text-2xl font-semibold text-slate-900">
                  Trending around you
                </h2>
              </div>

              <button
                type="button"
                className="text-sm font-semibold text-violet-700 transition hover:text-amber-600"
              >
                View all
              </button>
            </div>

            <div className="mt-6 space-y-3">
              {trending.map((item) => (
                <article
                  key={item.title}
                  className="flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50/70 p-4 transition hover:border-violet-100 hover:bg-violet-50/40"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-2xl shadow-sm ring-1 ring-slate-100">
                    {item.icon}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold uppercase tracking-wide text-violet-600">
                      {item.category}
                    </p>

                    <h3 className="mt-1 truncate text-sm font-semibold text-slate-900">
                      {item.title}
                    </h3>

                    <p className="mt-1 text-xs text-slate-500">
                      {item.people}
                    </p>
                  </div>

                  <button
                    type="button"
                    className="shrink-0 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-violet-700"
                  >
                    View
                  </button>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden rounded-2xl border border-amber-100 bg-gradient-to-r from-amber-50 via-white to-violet-50 p-6 md:p-8">
          <div className="relative z-10 max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-600">
              A little inspiration
            </p>

            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
              Your next memorable moment could be closer than you think.
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Explore recommendations shaped around your interests, your
              activities, and the experiences you want more of.
            </p>

            <button
              type="button"
              className="mt-5 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-700"
            >
              Discover more
            </button>
          </div>

          <div className="absolute -right-12 -top-12 h-32 w-32 rounded-full bg-amber-200/30" />
          <div className="absolute -bottom-16 right-20 h-40 w-40 rounded-full bg-violet-200/20" />
        </section>
      </div>
    </PageContainer>
  );
}