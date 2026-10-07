import PageContainer from "../../components/PageContainer";

const communities = [
  {
    name: "Weekend Explorers",
    description:
      "For people who love discovering new places, experiences, and hidden gems.",
    members: "2.4k members",
    icon: "✦",
  },
  {
    name: "Creative Corner",
    description:
      "Share ideas, projects, inspiration, and creative energy with others.",
    members: "1.8k members",
    icon: "✎",
  },
  {
    name: "Fitness Together",
    description:
      "Stay active, motivate each other, and make movement more enjoyable.",
    members: "3.1k members",
    icon: "⚡",
  },
  {
    name: "Coffee Conversations",
    description:
      "Meet people who enjoy good coffee and even better conversations.",
    members: "1.2k members",
    icon: "☕",
  },
  {
    name: "Movie Nights",
    description:
      "Talk movies, discover new favorites, and find people to watch with.",
    members: "2.1k members",
    icon: "◉",
  },
  {
    name: "Travel Stories",
    description:
      "Share destinations, travel memories, tips, and future adventures.",
    members: "3.6k members",
    icon: "◇",
  },
];

export default function CommunitiesPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950 via-blue-900 to-violet-800 p-8 text-white shadow-lg md:p-10">
          <div className="relative z-10 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wider text-violet-300">
              Find your circle
            </p>

            <h1 className="mt-3 text-4xl font-bold md:text-5xl">
              Somewhere you feel like you belong.
            </h1>

            <p className="mt-4 leading-7 text-slate-300">
              Join communities built around shared interests, conversations,
              passions, and experiences.
            </p>

            <button
              type="button"
              className="mt-7 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-indigo-900 shadow-sm transition hover:bg-violet-50"
            >
              Explore communities
            </button>
          </div>

          <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-violet-400/20" />
          <div className="absolute -bottom-20 right-32 h-48 w-48 rounded-full bg-blue-400/10" />
        </section>

        <section>
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium text-violet-600">
                Communities for you
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                Find your people
              </h2>
            </div>

            <span className="text-sm text-slate-500">
              6 communities
            </span>
          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {communities.map((community) => (
              <article
                key={community.name}
                className="group rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-1 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-100 text-xl font-bold text-violet-600">
                    {community.icon}
                  </div>

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
                    Community
                  </span>
                </div>

                <h3 className="mt-5 text-xl font-semibold text-slate-900">
                  {community.name}
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {community.description}
                </p>

                <div className="mt-5 flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-violet-600">
                    {community.members}
                  </span>

                  <button
                    type="button"
                    className="rounded-xl bg-indigo-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-600"
                  >
                    Join
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-2xl bg-gradient-to-r from-indigo-50 to-violet-50 p-6 ring-1 ring-violet-100 md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-violet-600">
                Create your own space
              </p>

              <h2 className="mt-2 text-2xl font-bold text-slate-900">
                Can't find your community?
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">
                Start something new and bring together people who share your
                interests.
              </p>
            </div>

            <button
              type="button"
              className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-600"
            >
              Create community
            </button>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}