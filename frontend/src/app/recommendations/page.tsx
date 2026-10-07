import PageContainer from "../../components/PageContainer";

const recommendations = [
  {
    title: "Sunset Photography Walk",
    type: "Activity",
    description:
      "A relaxed evening walk for photography lovers and people who enjoy discovering new spots.",
    icon: "📷",
  },
  {
    title: "Weekend Coffee Meetup",
    type: "Social",
    description:
      "Meet new people over coffee, conversations, and easy weekend vibes.",
    icon: "☕",
  },
  {
    title: "Creative Community",
    type: "Community",
    description:
      "A friendly space for people interested in art, music, photography, and creative ideas.",
    icon: "🎨",
  },
  {
    title: "Fitness & Adventure",
    type: "Experience",
    description:
      "Find active people for workouts, outdoor plans, and spontaneous weekend adventures.",
    icon: "🏃",
  },
];

export default function RecommendationsPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        {/* HERO */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#17101F] via-[#2B1833] to-[#D8B8D0] p-8 shadow-lg ring-1 ring-[#D8B9D0] md:p-10">
          <div className="relative z-10 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#E7C9E1]">
              Made for you
            </p>

            <h1 className="mt-3 text-4xl font-bold text-white md:text-5xl">
              Recommendations that feel like you.
            </h1>

            <p className="mt-4 leading-7 text-[#EBDCE9]">
              Discover activities, communities, and experiences based on your
              interests and the things you enjoy.
            </p>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#CDA5C8]/20" />

          <div className="absolute -bottom-20 right-28 h-48 w-48 rounded-full bg-[#F4E4A9]/15" />

          <div className="absolute right-10 top-9 text-3xl text-[#F0D5EA]/60">
            ✦
          </div>
        </section>

        {/* RECOMMENDATIONS */}
        <section>
          <div>
            <p className="text-sm font-medium text-[#815477]">
              Recommended for you
            </p>

            <h2 className="mt-1 text-2xl font-bold text-[#281A29]">
              Things you might enjoy
            </h2>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {recommendations.map((recommendation, index) => (
              <article
                key={recommendation.title}
                className="rounded-[1.75rem] bg-white p-6 shadow-sm ring-1 ring-[#E4D8E2] transition hover:-translate-y-1 hover:shadow-lg"
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl text-3xl ${
                      index === 0
                        ? "bg-[#E7D0E3]"
                        : index === 1
                          ? "bg-[#F0E4C6]"
                          : index === 2
                            ? "bg-[#DCCBE2]"
                            : "bg-[#E9D8C7]"
                    }`}
                  >
                    {recommendation.icon}
                  </div>

                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-[#875C7C]">
                      {recommendation.type}
                    </span>

                    <h3 className="mt-1 text-xl font-bold text-[#302032]">
                      {recommendation.title}
                    </h3>
                  </div>
                </div>

                <p className="mt-5 text-sm leading-6 text-[#716472]">
                  {recommendation.description}
                </p>

                <div className="mt-5 flex items-center justify-between">
                  <span className="rounded-full bg-[#F2E8F0] px-3 py-1.5 text-xs font-medium text-[#76536D]">
                    Recommended
                  </span>

                  <button
                    type="button"
                    className="rounded-xl bg-[#2B1833] px-4 py-2.5 text-sm font-semibold text-[#F2DDF0] transition hover:bg-[#422347]"
                  >
                    Explore
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* PERSONALIZATION */}
        <section className="rounded-3xl bg-gradient-to-r from-[#EEE0EC] via-[#F5EAF0] to-[#F3E8C9] p-6 ring-1 ring-[#E0D2D9] md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#79506F]">
                Make recommendations better
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#2D202B]">
                Tell Vynk what you're into.
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-[#716873]">
                Update your interests and preferences to discover experiences
                that fit you even better.
              </p>
            </div>

            <button
              type="button"
              className="rounded-xl bg-[#2B1833] px-5 py-3 text-sm font-semibold text-[#F2DCEB] transition hover:bg-[#422347]"
            >
              Update interests
            </button>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}