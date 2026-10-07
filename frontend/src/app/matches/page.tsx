"use client";

import PageContainer from "../../components/PageContainer";
import { useState } from "react";

const matches = [
  {
    name: "Maya",
    age: 24,
    location: "Hyderabad",
    match: 94,
    bio: "Always looking for new places, good conversations, and spontaneous plans.",
    interests: ["Travel", "Coffee", "Photography"],
    avatar: "M",
    color: "bg-[#FFF1A8] text-[#514A18]",
    reason: "You both love exploring new places",
  },
  {
    name: "Riya",
    age: 25,
    location: "Hyderabad",
    match: 89,
    bio: "Creative soul who enjoys music, movies, and finding hidden gems around the city.",
    interests: ["Music", "Movies", "Art"],
    avatar: "R",
    color: "bg-[#FFE680] text-[#574C12]",
    reason: "You share a strong interest in music",
  },
  {
    name: "Arjun",
    age: 26,
    location: "Hyderabad",
    match: 86,
    bio: "Into fitness, weekend adventures, and meeting people who enjoy trying new things.",
    interests: ["Fitness", "Sports", "Travel"],
    avatar: "A",
    color: "bg-[#FFF3B8] text-[#5C531D]",
    reason: "You both enjoy active weekends",
  },
  {
    name: "Nisha",
    age: 23,
    location: "Hyderabad",
    match: 82,
    bio: "Photography enthusiast, café explorer, and always ready for a creative weekend.",
    interests: ["Photography", "Coffee", "Creative"],
    avatar: "N",
    color: "bg-[#FFE58A] text-[#574B10]",
    reason: "Your interests overlap in photography",
  },
];

const filters = ["All", "Nearby", "High match", "Shared interests"];

export default function MatchesPage() {
  const [activeFilter, setActiveFilter] = useState("All");
  const [likedMatches, setLikedMatches] = useState<string[]>([]);
  const [passedMatches, setPassedMatches] = useState<string[]>([]);

  const visibleMatches = matches.filter((match) => {
    if (passedMatches.includes(match.name)) {
      return false;
    }

    if (activeFilter === "Nearby") {
      return match.location === "Hyderabad";
    }

    if (activeFilter === "High match") {
      return match.match >= 90;
    }

    if (activeFilter === "Shared interests") {
      return match.interests.length >= 3;
    }

    return true;
  });

  const handleLike = (name: string) => {
    setLikedMatches((current) =>
      current.includes(name)
        ? current.filter((item) => item !== name)
        : [...current, name],
    );
  };

  const handlePass = (name: string) => {
    setPassedMatches((current) => [...current, name]);
    setLikedMatches((current) =>
      current.filter((item) => item !== name),
    );
  };

  return (
    <PageContainer>
      <div className="space-y-8">
        {/* HERO */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#111111] via-[#191919] to-[#242424] p-8 shadow-lg ring-1 ring-[#333333] md:p-10">
          <div className="relative z-10 max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#F4D35E]">
              Find your people
            </p>

            <h1 className="mt-3 text-4xl font-bold text-white md:text-5xl">
              People you might click with.
            </h1>

            <p className="mt-4 max-w-2xl leading-7 text-[#C8C8C8]">
              Discover people who share your interests, energy, and the kind
              of experiences you enjoy.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <div className="rounded-2xl bg-[#252525] px-4 py-3 ring-1 ring-[#3A3A3A]">
                <p className="text-xl font-bold text-[#F4D35E]">24</p>
                <p className="text-xs text-[#AFAFAF]">Potential matches</p>
              </div>

              <div className="rounded-2xl bg-[#252525] px-4 py-3 ring-1 ring-[#3A3A3A]">
                <p className="text-xl font-bold text-[#F4D35E]">8</p>
                <p className="text-xs text-[#AFAFAF]">Shared interests</p>
              </div>

              <div className="rounded-2xl bg-[#252525] px-4 py-3 ring-1 ring-[#3A3A3A]">
                <p className="text-xl font-bold text-[#F4D35E]">4</p>
                <p className="text-xs text-[#AFAFAF]">Nearby</p>
              </div>
            </div>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#F4D35E]/10" />

          <div className="absolute -bottom-20 right-32 h-48 w-48 rounded-full bg-[#F4D35E]/5" />

          <div className="absolute right-12 top-10 text-4xl text-[#F4D35E]/40">
            ✦
          </div>
        </section>

        {/* FILTERS */}
        <section>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-medium text-[#9A8018]">
                Your matches
              </p>

              <h2 className="mt-1 text-2xl font-bold text-[#181818]">
                People worth meeting
              </h2>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-1">
              {filters.map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setActiveFilter(filter)}
                  className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${
                    activeFilter === filter
                      ? "bg-[#111111] text-[#F4D35E] shadow-sm"
                      : "bg-white text-[#666666] ring-1 ring-[#DCDCDC] hover:bg-[#FFF9D9] hover:text-[#8A7418]"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {/* MATCH CARDS */}
          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {visibleMatches.map((person) => {
              const isLiked = likedMatches.includes(person.name);

              return (
                <article
                  key={person.name}
                  className="group rounded-[1.75rem] bg-white p-6 shadow-sm ring-1 ring-[#E0E0E0] transition hover:-translate-y-1 hover:shadow-lg"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex min-w-0 items-center gap-4">
                      <div
                        className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl text-2xl font-bold ${person.color}`}
                      >
                        {person.avatar}
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-xl font-bold text-[#202020]">
                            {person.name}, {person.age}
                          </h3>

                          <span className="h-2 w-2 rounded-full bg-[#D5B82F]" />
                        </div>

                        <p className="mt-1 text-sm text-[#858585]">
                          {person.location} · Active recently
                        </p>
                      </div>
                    </div>

                    <div className="shrink-0 rounded-2xl bg-[#FFF4B8] px-3 py-2 text-center">
                      <p className="text-lg font-bold text-[#796513]">
                        {person.match}%
                      </p>

                      <p className="text-[10px] font-semibold uppercase tracking-wide text-[#9A831E]">
                        Match
                      </p>
                    </div>
                  </div>

                  <p className="mt-5 text-sm leading-6 text-[#707070]">
                    {person.bio}
                  </p>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {person.interests.map((interest, index) => (
                      <span
                        key={interest}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                          index === 0
                            ? "bg-[#FFF4B8] text-[#796513]"
                            : index === 1
                              ? "bg-[#FFF0C7] text-[#806B27]"
                              : "bg-[#F1F1F1] text-[#666666]"
                        }`}
                      >
                        {interest}
                      </span>
                    ))}
                  </div>

                  <div className="mt-5 rounded-2xl bg-[#FAFAFA] p-4 ring-1 ring-[#EEEEEE]">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[#927B1A]">
                      Why you match
                    </p>

                    <p className="mt-1 text-sm text-[#707070]">
                      {person.reason}
                    </p>
                  </div>

                  <div className="mt-5 flex gap-3">
                    <button
                      type="button"
                      onClick={() => handlePass(person.name)}
                      className="flex-1 rounded-xl border border-[#D9D9D9] bg-white px-4 py-3 text-sm font-semibold text-[#777777] transition hover:bg-[#F5F5F5]"
                    >
                      Pass
                    </button>

                    <button
                      type="button"
                      onClick={() => handleLike(person.name)}
                      className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                        isLiked
                          ? "bg-[#D9B92E] text-[#171717] hover:bg-[#C8A91F]"
                          : "bg-[#111111] text-[#F4D35E] hover:bg-[#242424]"
                      }`}
                    >
                      {isLiked ? "Connected ✓" : "Connect ♡"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>

          {visibleMatches.length === 0 && (
            <div className="mt-6 rounded-3xl bg-[#FAFAFA] p-10 text-center ring-1 ring-[#E4E4E4]">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#FFF4B8] text-2xl">
                ✦
              </div>

              <h3 className="mt-4 text-lg font-bold text-[#292929]">
                No matches here yet
              </h3>

              <p className="mt-2 text-sm text-[#7A7A7A]">
                Try another filter to discover more people.
              </p>

              <button
                type="button"
                onClick={() => setActiveFilter("All")}
                className="mt-5 rounded-xl bg-[#111111] px-5 py-3 text-sm font-semibold text-[#F4D35E] transition hover:bg-[#292929]"
              >
                Show all matches
              </button>
            </div>
          )}
        </section>

        {/* DISCOVERY CTA */}
        <section className="rounded-3xl bg-gradient-to-r from-[#FFF4B8] via-[#FFF8D9] to-[#F3F3F3] p-6 ring-1 ring-[#E6DFB7] md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#8A7317]">
                Keep discovering
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#202020]">
                Your next great connection could be nearby.
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-[#6E6E6E]">
                Update your interests and preferences to make your matches
                even more relevant.
              </p>
            </div>

            <button
              type="button"
              className="rounded-xl bg-[#111111] px-5 py-3 text-sm font-semibold text-[#F4D35E] transition hover:bg-[#292929]"
            >
              Update preferences
            </button>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}