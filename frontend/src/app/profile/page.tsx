"use client";

import PageContainer from "../../components/PageContainer";
import { useState } from "react";

const initialInterests = [
  "Photography",
  "Travel",
  "Coffee",
  "Music",
  "Fitness",
  "Movies",
];

const quotes = [
  "Collect moments, not things.",
  "Good people make ordinary days feel special.",
  "Stay curious. Keep exploring.",
  "The best memories usually start with a simple yes.",
];

const stats = [
  { label: "Activities", value: "12" },
  { label: "Connections", value: "48" },
  { label: "Communities", value: "6" },
];

const vibes = [
  "Curious",
  "Social",
  "Explorer",
  "Creative",
  "Adventurous",
];

export default function ProfilePage() {
  const [interests, setInterests] = useState(initialInterests);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [likedVibes, setLikedVibes] = useState<string[]>([
    "Curious",
    "Social",
  ]);
  const [isEditing, setIsEditing] = useState(false);

  const toggleVibe = (vibe: string) => {
    setLikedVibes((current) =>
      current.includes(vibe)
        ? current.filter((item) => item !== vibe)
        : [...current, vibe],
    );
  };

  const removeInterest = (interest: string) => {
    setInterests((current) =>
      current.filter((item) => item !== interest),
    );
  };

  const addInterest = () => {
    const available = [
      "Reading",
      "Art",
      "Cooking",
      "Dance",
      "Nature",
      "Gaming",
    ];

    const nextInterest = available.find(
      (interest) => !interests.includes(interest),
    );

    if (nextInterest) {
      setInterests((current) => [...current, nextInterest]);
    }
  };

  const nextQuote = () => {
    setQuoteIndex((current) => (current + 1) % quotes.length);
  };

  return (
    <PageContainer>
      <div className="space-y-8">
        {/* PROFILE HEADER */}
        <section className="overflow-hidden rounded-[2rem] bg-white shadow-sm ring-1 ring-[#E2D8DD]">
          {/* COVER */}
          <div className="relative h-56 overflow-hidden bg-gradient-to-br from-[#421B29] via-[#71394D] to-[#AFCBE4] md:h-64">
            <div className="absolute left-8 top-8 max-w-xl">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#DCEAF7]">
                Your Vynk space
              </p>

              <h2 className="mt-3 text-3xl font-bold leading-tight text-white md:text-4xl">
                Your story is made of{" "}
                <span className="text-[#CFE4F5]">
                  little moments.
                </span>
              </h2>

              <p className="mt-3 max-w-lg text-sm leading-6 text-[#F0E5EA]">
                Keep discovering, keep connecting, and let your profile grow
                with the experiences that matter to you.
              </p>
            </div>

            <div className="absolute -right-16 -top-20 h-64 w-64 rounded-full border border-white/10" />

            <div className="absolute bottom-5 right-12 h-32 w-32 rounded-full bg-[#CFE4F5]/20 blur-2xl" />

            <div className="absolute bottom-7 right-10 text-4xl text-[#DCEAF7]/70">
              ✦
            </div>
          </div>

          {/* PROFILE INFORMATION */}
          <div className="px-6 pb-7 pt-6 md:px-8 md:pt-7">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                {/* AVATAR */}
                <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-3xl border-4 border-white bg-gradient-to-br from-[#713A4D] to-[#AFCBE4] text-4xl font-bold text-white shadow-lg">
                  A
                </div>

                <div>
                  <p className="text-sm font-semibold text-[#8C4F64]">
                    Vynk member
                  </p>

                  <h1 className="mt-1 text-3xl font-bold text-[#35212A]">
                    Ayu
                  </h1>

                  <p className="mt-1 text-sm text-[#777681]">
                    Hyderabad · Exploring new experiences
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsEditing(!isEditing)}
                className={`rounded-xl px-5 py-3 text-sm font-semibold transition ${
                  isEditing
                    ? "bg-[#DCEAF7] text-[#496983] hover:bg-[#CDE0F1]"
                    : "bg-[#4A202D] text-[#F8E5EB] hover:bg-[#6B3345]"
                }`}
              >
                {isEditing ? "Done editing" : "Edit profile"}
              </button>
            </div>

            <p className="mt-6 max-w-2xl text-sm leading-7 text-[#6E6870]">
              Love discovering new places, meeting interesting people, and
              finding simple things that make everyday life more fun.
            </p>

            {/* STATS */}
            <div className="mt-6 grid grid-cols-3 divide-x divide-[#E4DDE0] rounded-2xl bg-[#FAF8F9] py-5 ring-1 ring-[#E9E2E5]">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className="text-xl font-bold text-[#35212A]">
                    {stat.value}
                  </p>

                  <p className="mt-1 text-xs font-medium text-[#7A747B]">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* BEAUTIFUL QUOTE */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-r from-[#F3DCE5] via-[#E7EEF7] to-[#DCEAF7] p-7 ring-1 ring-[#D9E1E9] md:p-9">
          <div className="relative z-10">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#8C5266]">
              A little reminder
            </p>

            <blockquote className="mt-4 max-w-3xl text-2xl font-semibold leading-relaxed text-[#3B2931] md:text-3xl">
              “{quotes[quoteIndex]}”
            </blockquote>

            <button
              type="button"
              onClick={nextQuote}
              className="mt-6 rounded-xl bg-[#4A202D] px-4 py-2.5 text-sm font-semibold text-[#F8E5EB] transition hover:bg-[#6B3345]"
            >
              Another quote ✦
            </button>
          </div>

          <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-[#AFCBE4]/30" />

          <div className="absolute bottom-4 right-10 text-7xl font-serif text-[#8B5266]/10">
            “
          </div>
        </section>

        {/* INTERESTS + VIBE */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* INTERESTS */}
          <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-[#DCE5ED] lg:col-span-2 md:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-[#6688A7]">
                  About you
                </p>

                <h2 className="mt-1 text-2xl font-bold text-[#33252C]">
                  Your interests
                </h2>
              </div>

              {isEditing && (
                <button
                  type="button"
                  onClick={addInterest}
                  className="rounded-xl bg-[#DCEAF7] px-4 py-2 text-sm font-semibold text-[#55728E] transition hover:bg-[#CDE0F1]"
                >
                  + Add
                </button>
              )}
            </div>

            <p className="mt-2 text-sm leading-6 text-[#77727A]">
              The things you enjoy and the experiences that help Vynk
              understand you better.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {interests.map((interest, index) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => isEditing && removeInterest(interest)}
                  className={`rounded-full px-4 py-2.5 text-sm font-medium transition ${
                    index % 3 === 0
                      ? "bg-[#F4DDE5] text-[#87485E] hover:bg-[#EBC9D5]"
                      : index % 3 === 1
                        ? "bg-[#DCEAF7] text-[#55789A] hover:bg-[#CDE0F1]"
                        : "bg-[#E8DCE2] text-[#765365] hover:bg-[#DDCED6]"
                  }`}
                >
                  {interest}
                  {isEditing && " ×"}
                </button>
              ))}
            </div>

            {!isEditing && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="mt-7 rounded-xl border border-[#D7E0E8] bg-[#F7FAFC] px-4 py-2.5 text-sm font-semibold text-[#61788F] transition hover:border-[#B8D0E5] hover:bg-[#EEF6FC]"
              >
                Edit interests
              </button>
            )}
          </section>

          {/* VIBE */}
          <section className="rounded-3xl bg-gradient-to-br from-[#4A202D] via-[#683346] to-[#AFCBE4] p-6 text-white shadow-md">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-[#F0D6DE]">
                Your Vynk vibe
              </p>

              <span className="text-xl text-[#CFE4F5]">✦</span>
            </div>

            <h2 className="mt-5 text-2xl font-bold">
              Curious & social
            </h2>

            <p className="mt-3 text-sm leading-6 text-[#E7DDE1]">
              Pick the words that feel most like you.
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {vibes.map((vibe) => {
                const selected = likedVibes.includes(vibe);

                return (
                  <button
                    key={vibe}
                    type="button"
                    onClick={() => toggleVibe(vibe)}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                      selected
                        ? "bg-[#DCEAF7] text-[#425E78]"
                        : "bg-white/10 text-[#F4E8EC] hover:bg-white/20"
                    }`}
                  >
                    {selected ? "✓ " : ""}
                    {vibe}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              className="mt-7 rounded-xl bg-[#DCEAF7] px-4 py-3 text-sm font-semibold text-[#425E78] transition hover:bg-white"
            >
              Update preferences
            </button>
          </section>
        </div>

        {/* PROFILE COMPLETION */}
        <section className="rounded-3xl bg-gradient-to-r from-[#F4DDE5] via-[#E8EEF7] to-[#DCEAF7] p-6 ring-1 ring-[#D9E1E9] md:p-7">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#7D5063]">
                Profile strength
              </p>

              <h2 className="mt-2 text-2xl font-bold text-[#33252C]">
                You're 80% complete.
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-[#716E75]">
                Add a little more about yourself to help Vynk find even better
                people, activities, and experiences for you.
              </p>
            </div>

            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#713A4D] to-[#9DBEDB] text-xl font-bold text-white shadow-md">
              80%
            </div>
          </div>

          <div className="mt-6 h-2 overflow-hidden rounded-full bg-[#DCE1E7]">
            <div className="h-full w-4/5 rounded-full bg-gradient-to-r from-[#7A4053] to-[#AFCBE4]" />
          </div>

          <button
            type="button"
            onClick={() => setIsEditing(true)}
            className="mt-5 rounded-xl bg-[#4A202D] px-5 py-3 text-sm font-semibold text-[#F8E5EB] transition hover:bg-[#6B3345]"
          >
            Complete profile
          </button>
        </section>
      </div>
    </PageContainer>
  );
}