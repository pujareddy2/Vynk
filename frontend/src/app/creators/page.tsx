import PageContainer from "../../components/PageContainer";

const creators = [
  {
    name: "Ballerina Cappuccino",
    category: "Brainrot Creator",
    followers: "50K followers",
    bio: "A viral AI-generated character combining ballet elegance with a cappuccino-inspired design.",
    avatar: "B",
    location: "Internet",
    specialty: "Italian Brainrot",
    engagement: "Very High",
    tags: ["AI Character", "Comedy", "Memes"],
  },
  {
    name: "TungTung Sahur",
    category: "Brainrot Creator",
    followers: "100K followers",
    bio: "A viral Indonesian-origin AI character inspired by the traditional sahur wake-up call during Ramadan.",
    avatar: "T",
    location: "Indonesia",
    specialty: "Viral Memes",
    engagement: "Very High",
    tags: ["Memes", "AI Character", "Viral"],
  },
  {
    name: "Maya Kapoor",
    category: "Photography",
    followers: "12.4K followers",
    bio: "Street photographer sharing hidden corners, visual stories, and creative walks around the city.",
    avatar: "M",
    location: "Hyderabad",
    specialty: "Street Photography",
    engagement: "High",
    tags: ["Photography", "Travel", "Creative"],
  },
  {
    name: "Riya Sharma",
    category: "Lifestyle",
    followers: "8.7K followers",
    bio: "Exploring cafés, experiences, fashion, and little moments worth discovering and sharing.",
    avatar: "R",
    location: "Hyderabad",
    specialty: "Lifestyle",
    engagement: "High",
    tags: ["Coffee", "Fashion", "Lifestyle"],
  },
  {
    name: "Arjun Mehta",
    category: "Fitness",
    followers: "15.2K followers",
    bio: "Fitness creator helping people make movement fun, social, and sustainable through everyday habits.",
    avatar: "A",
    location: "Hyderabad",
    specialty: "Fitness",
    engagement: "High",
    tags: ["Fitness", "Sports", "Wellness"],
  },
  {
    name: "Nisha Rao",
    category: "Travel",
    followers: "10.8K followers",
    bio: "Weekend explorer finding beautiful places, hidden gems, and easy travel ideas for curious people.",
    avatar: "N",
    location: "Hyderabad",
    specialty: "Travel",
    engagement: "Medium",
    tags: ["Travel", "Adventure", "Exploring"],
  },
];

const categories = [
  "All",
  "Brainrot",
  "Lifestyle",
  "Photography",
  "Fitness",
  "Travel",
];

export default function CreatorsPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        {/* HERO */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#123B46] via-[#275B5D] to-[#C59B73] p-8 shadow-lg ring-1 ring-[#B99372] md:p-10">
          <div className="relative z-10 max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#DCEBE6]">
              Discover creators
            </p>

            <h1 className="mt-3 text-4xl font-bold text-white md:text-5xl">
              Find people worth following.
            </h1>

            <p className="mt-4 leading-7 text-[#E7E0D7]">
              Discover creators, personalities, and viral internet characters
              that bring something interesting to your Vynk experience.
            </p>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#A9D1C7]/20" />

          <div className="absolute -bottom-20 right-24 h-48 w-48 rounded-full bg-[#E4B98D]/20" />

          <div className="absolute right-10 top-9 text-3xl text-[#F0D8B9]/60">
            ✦
          </div>
        </section>

        {/* FILTERS */}
        <section>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium text-[#46766F]">
                Creator community
              </p>

              <h2 className="mt-1 text-2xl font-bold text-[#35251E]">
                Creators you may like
              </h2>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-1">
              {categories.map((category) => (
                <button
                  key={category}
                  type="button"
                  className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${
                    category === "All"
                      ? "bg-[#3B241A] text-[#F4DEC3] shadow-sm"
                      : "bg-white text-[#75675F] ring-1 ring-[#E1D5CC] hover:bg-[#F3E8DE] hover:text-[#795039]"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* CREATOR CARDS */}
          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            {creators.map((creator, index) => (
              <article
                key={creator.name}
                className="rounded-[1.75rem] bg-white p-6 shadow-sm ring-1 ring-[#E4D9D0] transition hover:-translate-y-1 hover:shadow-lg"
              >
                {/* HEADER */}
                <div className="flex items-start gap-4">
                  <div
                    className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl text-2xl font-bold ${
                      index === 0
                        ? "bg-[#DCEBE6] text-[#2E625B]"
                        : index === 1
                          ? "bg-[#EAD9C8] text-[#704B31]"
                          : index === 2
                            ? "bg-[#D6E5DF] text-[#3B665D]"
                            : index === 3
                              ? "bg-[#F0DFD0] text-[#775038]"
                              : index === 4
                                ? "bg-[#DCEBE6] text-[#35645C]"
                                : "bg-[#F0DFD0] text-[#775038]"
                    }`}
                  >
                    {creator.avatar}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="text-xl font-bold text-[#35241D]">
                          {creator.name}
                        </h3>

                        <p className="mt-1 text-sm font-medium text-[#5B8178]">
                          {creator.category}
                        </p>
                      </div>

                      <span className="shrink-0 rounded-full bg-[#F0E4D8] px-3 py-1.5 text-xs font-semibold text-[#76533D]">
                        Creator
                      </span>
                    </div>
                  </div>
                </div>

                {/* BIO */}
                <p className="mt-5 text-sm leading-6 text-[#756A63]">
                  {creator.bio}
                </p>

                {/* CREATOR INFO */}
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl bg-[#F8F3EE] p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[#8A6A55]">
                      Location
                    </p>

                    <p className="mt-1 text-sm font-semibold text-[#463027]">
                      {creator.location}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-[#F8F3EE] p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[#8A6A55]">
                      Specialty
                    </p>

                    <p className="mt-1 text-sm font-semibold text-[#463027]">
                      {creator.specialty}
                    </p>
                  </div>
                </div>

                {/* TAGS */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {creator.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-[#E4EEE9] px-3 py-1.5 text-xs font-medium text-[#477066]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* FOOTER */}
                <div className="mt-5 flex flex-col gap-4 border-t border-[#E9DFD8] pt-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-bold text-[#463027]">
                      {creator.followers}
                    </p>

                    <p className="mt-1 text-xs text-[#81746D]">
                      {creator.engagement} engagement
                    </p>
                  </div>

                  <button
                    type="button"
                    className="rounded-xl bg-[#3B241A] px-5 py-3 text-sm font-semibold text-[#F3DEC6] transition hover:bg-[#573526]"
                  >
                    Follow
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="rounded-3xl bg-gradient-to-r from-[#DCEAE5] via-[#EFE2D5] to-[#E4CDB8] p-6 ring-1 ring-[#D8C9BC] md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#4B756D]">
                Share your creativity
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#38261E]">
                Want to become a creator on Vynk?
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-[#756A63]">
                Share your interests, ideas, and experiences with people who
                enjoy the same things.
              </p>
            </div>

            <button
              type="button"
              className="rounded-xl bg-[#3B241A] px-5 py-3 text-sm font-semibold text-[#F3DEC6] transition hover:bg-[#573526]"
            >
              Become a creator
            </button>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}