import PageContainer from "../../components/PageContainer";

const activities = [
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
  {
    title: "Evening Badminton",
    category: "Sports",
    people: "6 people interested",
    icon: "🏸",
  },
  {
    title: "Photography Walk",
    category: "Creative",
    people: "10 people interested",
    icon: "📷",
  },
];

export default function ActivitiesPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#4A1F2D] via-[#6B2D3D] to-[#F3B6C8] p-8 shadow-lg ring-1 ring-[#E5A4B9] md:p-10">
          <div className="relative z-10 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#FFD9E4]">
              Discover & do
            </p>

            <h1 className="mt-3 text-4xl font-bold text-white md:text-5xl">
              Find something you actually want to do.
            </h1>

            <p className="mt-4 leading-7 text-[#FFE8EF]">
              Browse activities based on your interests, energy, and the
              people you want to meet.
            </p>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#F7C4D5]/20" />

          <div className="absolute -bottom-16 right-24 h-40 w-40 rounded-full bg-[#3A1623]/25" />

          <div className="absolute right-10 top-8 text-3xl text-[#FFD8E5]/60">
            ✦
          </div>
        </section>

        <section>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium text-[#B65370]">
                Explore activities
              </p>

              <h2 className="mt-1 text-2xl font-bold text-[#3A1E29]">
                What sounds good?
              </h2>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-1">
              {["All", "Outdoor", "Social", "Sports", "Creative"].map(
                (filter) => (
                  <button
                    key={filter}
                    type="button"
                    className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${
                      filter === "All"
                        ? "bg-[#5A2636] text-[#FFDDE7] shadow-sm"
                        : "bg-white text-[#806672] ring-1 ring-[#E5CBD4] hover:bg-[#FFF0F4] hover:text-[#9D405E]"
                    }`}
                  >
                    {filter}
                  </button>
                ),
              )}
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {activities.map((activity, index) => (
              <article
                key={activity.title}
                className="flex items-center gap-5 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-[#E8D5DC] transition hover:-translate-y-1 hover:shadow-md"
              >
                <div
                  className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl text-3xl ${
                    index === 0
                      ? "bg-[#F9D5E0]"
                      : index === 1
                        ? "bg-[#F6C5D5]"
                        : index === 2
                          ? "bg-[#FDE3EA]"
                          : "bg-[#EFD1DA]"
                  }`}
                >
                  {activity.icon}
                </div>

                <div className="min-w-0 flex-1">
                  <span className="text-xs font-semibold uppercase tracking-wide text-[#B65370]">
                    {activity.category}
                  </span>

                  <h3 className="mt-1 text-lg font-semibold text-[#3C202B]">
                    {activity.title}
                  </h3>

                  <p className="mt-1 text-sm text-[#866E78]">
                    {activity.people}
                  </p>
                </div>

                <button
                  type="button"
                  className="rounded-xl bg-[#F7D5DF] px-4 py-2 text-sm font-semibold text-[#7E3049] transition hover:bg-[#F1BFCE]"
                >
                  Join
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-3xl bg-gradient-to-r from-[#F8D5E0] via-[#FFE8EF] to-[#F1C5D2] p-6 ring-1 ring-[#E7C4CF] md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#A44461]">
                Have your own idea?
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#3A202A]">
                Create an activity and bring people together.
              </h2>
            </div>

            <button
              type="button"
              className="rounded-xl bg-[#542333] px-5 py-3 text-sm font-semibold text-[#FFDDE7] transition hover:bg-[#3D1927]"
            >
              Create activity
            </button>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}