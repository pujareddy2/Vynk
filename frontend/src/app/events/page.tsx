import PageContainer from "../../components/PageContainer";

const events = [
  {
    title: "Sunset Beach Walk",
    category: "Outdoor",
    time: "Today · 6:00 PM",
    people: "12 people interested",
    location: "Seaside Promenade",
    icon: "🌅",
  },
  {
    title: "Garden Coffee Meetup",
    category: "Social",
    time: "Tomorrow · 11:00 AM",
    people: "8 people interested",
    location: "Moss Garden Cafe",
    icon: "☕",
  },
  {
    title: "Weekend Board Games",
    category: "Games",
    time: "Saturday · 4:00 PM",
    people: "16 people interested",
    location: "The Green Room",
    icon: "🎲",
  },
  {
    title: "Morning Nature Walk",
    category: "Wellness",
    time: "Sunday · 7:30 AM",
    people: "11 people interested",
    location: "Botanical Gardens",
    icon: "🌿",
  },
  {
    title: "Open Air Art Evening",
    category: "Creative",
    time: "Sunday · 5:00 PM",
    people: "9 people interested",
    location: "Lakeside Studio",
    icon: "🎨",
  },
  {
    title: "Live Acoustic Night",
    category: "Music",
    time: "Friday · 8:00 PM",
    people: "21 people interested",
    location: "The Greenhouse",
    icon: "🎸",
  },
];

const filters = [
  "All",
  "Outdoor",
  "Social",
  "Games",
  "Wellness",
  "Creative",
  "Music",
];

export default function EventsPage() {
  return (
    <PageContainer>
      <div className="space-y-8">
        {/* Hero */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#102F24] via-[#173F2D] to-[#315A3A] p-8 text-white shadow-xl md:p-10">
          <div className="relative z-10 max-w-2xl">
            <div className="flex items-center gap-3">
              <span className="h-px w-10 bg-[#A7B86A]" />

              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[#C9D6A0]">
                Gather · Explore · Experience
              </p>
            </div>

            <h1 className="mt-6 text-4xl font-bold leading-tight md:text-5xl">
              Make plans
              <br />
              worth remembering.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-7 text-[#D9E3D5]">
              Discover events, meet interesting people, and find something
              beautiful to look forward to.
            </p>

            <button
              type="button"
              className="mt-8 rounded-xl bg-[#D7E1B0] px-5 py-3 text-sm font-semibold text-[#173F2D] shadow-sm transition hover:bg-white"
            >
              Explore events →
            </button>
          </div>

          <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full border border-[#A7B86A]/20" />

          <div className="absolute -right-8 -top-8 h-48 w-48 rounded-full bg-[#71884D]/20" />

          <div className="absolute -bottom-28 right-28 h-64 w-64 rounded-full border border-[#C9D6A0]/15" />

          <div className="absolute right-14 top-12 text-4xl text-[#A7B86A]/50">
            ✦
          </div>
        </section>

        {/* Filters */}
        <section>
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#61753F]">
                What's happening
              </p>

              <h2 className="mt-1 text-2xl font-bold text-[#183328]">
                Upcoming events
              </h2>

              <p className="mt-1 text-sm text-[#66756C]">
                Find something worth stepping out for.
              </p>
            </div>

            <span className="text-sm font-medium text-[#71806F]">
              6 events
            </span>
          </div>

          <div className="flex gap-2 overflow-x-auto pb-2">
            {filters.map((filter) => (
              <button
                key={filter}
                type="button"
                className={`whitespace-nowrap rounded-full px-4 py-2.5 text-sm font-medium transition ${
                  filter === "All"
                    ? "bg-[#61753F] text-white shadow-sm"
                    : "bg-[#FBFCF7] text-[#536357] ring-1 ring-[#D9E0D3] hover:bg-[#E8EDDB] hover:text-[#4E6533]"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </section>

        {/* Event cards */}
        <section>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {events.map((event, index) => (
              <article
                key={event.title}
                className="group overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-[#DDE4DB] transition duration-200 hover:-translate-y-1 hover:shadow-xl"
              >
                <div
                  className={`relative flex h-40 items-center justify-center ${
                    index % 3 === 0
                      ? "bg-gradient-to-br from-[#DDE7CE] via-[#EEF2E5] to-[#C8D5B7]"
                      : index % 3 === 1
                        ? "bg-gradient-to-br from-[#D4DFCA] via-[#F0F3E9] to-[#DDE5CF]"
                        : "bg-gradient-to-br from-[#C9D8BE] via-[#E9EFE1] to-[#D2DFC5]"
                  }`}
                >
                  <div className="text-6xl transition duration-200 group-hover:scale-110">
                    {event.icon}
                  </div>

                  <span className="absolute left-4 top-4 rounded-full bg-[#F9FBF5]/95 px-3 py-1 text-xs font-semibold text-[#536B38] shadow-sm">
                    {event.category}
                  </span>

                  <button
                    type="button"
                    aria-label={`Save ${event.title}`}
                    className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full bg-[#F9FBF5]/95 text-lg text-[#637064] shadow-sm transition hover:text-[#61753F]"
                  >
                    ♡
                  </button>
                </div>

                <div className="p-6">
                  <h3 className="text-xl font-bold text-[#183328]">
                    {event.title}
                  </h3>

                  <div className="mt-4 space-y-2.5">
                    <p className="text-sm font-medium text-[#506259]">
                      🕒 {event.time}
                    </p>

                    <p className="text-sm text-[#718078]">
                      📍 {event.location}
                    </p>

                    <p className="text-sm text-[#718078]">
                      ♡ {event.people}
                    </p>
                  </div>

                  <div className="mt-6 flex items-center justify-between gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#61753F]">
                      {event.category}
                    </span>

                    <button
                      type="button"
                      className="rounded-xl bg-[#173F2D] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#61753F]"
                    >
                      View event
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* Featured event */}
        <section className="relative overflow-hidden rounded-[2rem] bg-[#173F2D] p-7 text-white shadow-lg md:p-9">
          <div className="relative z-10 flex flex-col gap-7 md:flex-row md:items-center md:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#A7B86A]">
                Featured this week
              </p>

              <h2 className="mt-3 text-2xl font-bold md:text-3xl">
                Sometimes the best plans are the unexpected ones.
              </h2>

              <p className="mt-3 text-sm leading-6 text-[#CBD8CE]">
                Explore something new, bring a friend, or simply show up and
                see who you meet.
              </p>
            </div>

            <button
              type="button"
              className="shrink-0 rounded-xl bg-[#A7B86A] px-6 py-3 text-sm font-semibold text-[#173F2D] transition hover:bg-[#C9D6A0]"
            >
              Discover more
            </button>
          </div>

          <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[#71884D]/25" />

          <div className="absolute -bottom-20 right-40 h-48 w-48 rounded-full border border-[#A7B86A]/15" />

          <div className="absolute right-16 top-10 text-3xl text-[#A7B86A]/50">
            ✦
          </div>
        </section>
      </div>
    </PageContainer>
  );
}