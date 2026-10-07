"use client";

import Link from "next/link";
import { useState } from "react";

const moods = [
  {
    label: "Meet people",
    icon: "👋",
    color: "bg-[#DDF5F0]",
    text: "text-[#176D65]",
    title: "Find people who get you.",
    description:
      "Discover people nearby who share your interests, energy, and plans.",
  },
  {
    label: "Try something",
    icon: "✨",
    color: "bg-[#E8E4FA]",
    text: "text-[#5B4DB5]",
    title: "Find something exciting.",
    description:
      "Explore activities and experiences that match what you're feeling.",
  },
  {
    label: "Find a community",
    icon: "🌎",
    color: "bg-[#F8E7C9]",
    text: "text-[#856426]",
    title: "Find your people.",
    description:
      "Join communities built around interests, hobbies, and shared experiences.",
  },
];

const discoveries = [
  {
    name: "Evening Badminton",
    icon: "🏸",
    people: "6 people interested",
    tag: "Sports",
  },
  {
    name: "Coffee & Conversations",
    icon: "☕",
    people: "12 people interested",
    tag: "Social",
  },
  {
    name: "Photography Walk",
    icon: "📷",
    people: "10 people interested",
    tag: "Creative",
  },
];

const discoveryCards = [
  {
    icon: "👋",
    title: "People",
    text: "Meet people who are into the same things.",
    bg: "bg-[#DDF5F0]",
  },
  {
    icon: "⚡",
    title: "Activities",
    text: "Find something fun to do right now.",
    bg: "bg-[#E8E4FA]",
  },
  {
    icon: "💫",
    title: "Communities",
    text: "Find spaces where you naturally belong.",
    bg: "bg-[#F8E7C9]",
  },
];

const steps = [
  {
    number: "01",
    title: "Say what you want",
    text: "A simple thought is enough.",
  },
  {
    number: "02",
    title: "Vynk finds possibilities",
    text: "People, activities, and communities appear around your intent.",
  },
  {
    number: "03",
    title: "Choose your next move",
    text: "Join, connect, explore, or create something yourself.",
  },
];

export default function HomePage() {
  const [selectedMood, setSelectedMood] = useState(0);
  const [showDiscoveries, setShowDiscoveries] = useState(false);

  const mood = moods[selectedMood];

  return (
    <main className="overflow-hidden bg-[#F7F6F2] text-[#172033]">
      {/* HERO */}
      <section className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-[#172033]">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -right-40 -top-40 h-[34rem] w-[34rem] animate-pulse rounded-full bg-[#6C5CE7]/30 blur-3xl" />

          <div
            className="absolute -bottom-48 -left-40 h-[34rem] w-[34rem] animate-pulse rounded-full bg-[#20C8BE]/20 blur-3xl"
            style={{ animationDelay: "1.5s" }}
          />

          <div
            className="absolute left-[42%] top-[15%] h-32 w-32 animate-bounce rounded-full border border-white/10"
            style={{ animationDuration: "6s" }}
          />

          <div
            className="absolute right-[12%] top-[60%] h-20 w-20 animate-ping rounded-full bg-[#F3D69C]/5"
            style={{ animationDuration: "4s" }}
          />

          <div
            className="absolute bottom-[15%] left-[18%] h-16 w-16 animate-pulse rounded-full bg-[#48DED5]/10"
            style={{ animationDuration: "3s" }}
          />
        </div>

        <div className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-14 px-6 py-16 lg:grid-cols-[1fr_0.9fr] lg:py-20">
          {/* HERO CONTENT */}
          <div>
            <div className="inline-flex animate-[fadeIn_0.8s_ease-out] items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-[#D8D9E5] backdrop-blur">
              <span className="h-2 w-2 animate-pulse rounded-full bg-[#48DED5]" />
              Your next experience starts here
            </div>

            <h1 className="mt-7 max-w-3xl text-5xl font-bold leading-[0.98] tracking-tight text-white sm:text-6xl lg:text-7xl">
              What do you feel like{" "}
              <span className="inline-block animate-pulse text-[#48DED5]">
                doing?
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-lg leading-8 text-[#C4C8D4]">
              Tell Vynk what you're in the mood for. We'll help you discover
              people, activities, and communities that fit.
            </p>

            {/* MOOD BUTTONS */}
            <div className="mt-9 flex flex-wrap gap-3">
              {moods.map((item, index) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => {
                    setSelectedMood(index);
                    setShowDiscoveries(false);
                  }}
                  className={`transform rounded-2xl px-5 py-3 text-sm font-semibold transition-all duration-300 hover:-translate-y-1 ${
                    selectedMood === index
                      ? `${item.color} ${item.text} scale-105 shadow-lg`
                      : "border border-white/10 bg-white/5 text-white hover:bg-white/10"
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>

            {/* BUTTONS */}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="transform rounded-2xl bg-[#F3D69C] px-6 py-3.5 text-center text-sm font-bold text-[#172033] shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-[#F8E5B9] hover:shadow-xl"
              >
                Start discovering
              </Link>

              <Link
                href="/activities"
                className="transform rounded-2xl border border-white/15 bg-white/5 px-6 py-3.5 text-center text-sm font-semibold text-white transition-all duration-300 hover:-translate-y-1 hover:bg-white/10"
              >
                Explore activities
              </Link>
            </div>
          </div>

          {/* INTERACTIVE CARD */}
          <div className="relative mx-auto w-full max-w-lg">
            <div className="animate-[float_6s_ease-in-out_infinite] rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#48DED5]">
                    Your Vynk moment
                  </p>

                  <h2 className="mt-2 text-2xl font-bold text-white transition-all duration-300">
                    {mood.title}
                  </h2>
                </div>

                <div
                  className={`flex h-12 w-12 animate-pulse items-center justify-center rounded-2xl ${mood.color} text-2xl`}
                >
                  {mood.icon}
                </div>
              </div>

              <p className="mt-4 leading-6 text-[#C5C9D5]">
                {mood.description}
              </p>

              <div className="mt-6 rounded-2xl bg-[#F9F8F4] p-5 transition-transform duration-300 hover:scale-[1.02]">
                <p className="text-xs font-bold uppercase tracking-wide text-[#858A96]">
                  Try saying
                </p>

                <p className="mt-3 text-lg font-semibold leading-7 text-[#242B3A]">
                  “I want to meet some people and play badminton this
                  Saturday.”
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setShowDiscoveries((current) => !current)
                }
                className="mt-4 flex w-full transform items-center justify-center gap-2 rounded-2xl bg-[#48DED5] px-5 py-3.5 text-sm font-bold text-[#123E3B] transition-all duration-300 hover:-translate-y-1 hover:bg-[#69E9E2] hover:shadow-lg"
              >
                {showDiscoveries
                  ? "Hide discoveries"
                  : "Show my discoveries"}

                <span
                  className={`transition-transform duration-300 ${
                    showDiscoveries ? "rotate-180" : ""
                  }`}
                >
                  ↓
                </span>
              </button>

              {/* DISCOVERY LIST */}
              <div
                className={`grid transition-all duration-500 ${
                  showDiscoveries
                    ? "mt-4 grid-rows-[1fr] opacity-100"
                    : "grid-rows-[0fr] opacity-0"
                }`}
              >
                <div className="overflow-hidden">
                  <div className="space-y-3">
                    {discoveries.map((item) => (
                      <div
                        key={item.name}
                        className="flex transform items-center gap-3 rounded-2xl bg-white/10 p-3 transition-all duration-300 hover:translate-x-2 hover:bg-white/15"
                      >
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-xl">
                          {item.icon}
                        </div>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-bold text-white">
                            {item.name}
                          </p>

                          <p className="mt-0.5 text-xs text-[#AEB3C0]">
                            {item.people}
                          </p>
                        </div>

                        <span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-semibold text-[#D5D8E1]">
                          {item.tag}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* FLOATING BADGES */}
            <div className="absolute -bottom-6 -left-6 hidden animate-[float_5s_ease-in-out_infinite] rounded-2xl border border-[#F3D69C]/20 bg-[#282F42] px-5 py-4 shadow-xl sm:block">
              <p className="text-xs text-[#AEB3C0]">Vynk philosophy</p>

              <p className="mt-1 font-bold text-[#F3D69C]">
                Start with what you want.
              </p>
            </div>

            <div className="absolute -right-5 -top-8 hidden animate-[float_4s_ease-in-out_infinite] rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-md sm:block">
              <p className="text-xs text-[#AEB3C0]">Discover</p>
              <p className="font-bold text-white">Something new ✨</p>
            </div>
          </div>
        </div>
      </section>

      {/* DISCOVERY */}
      <section className="bg-[#F7F6F2] px-6 py-20 md:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="text-center">
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#6558D7]">
              One app. Many possibilities.
            </p>

            <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-5xl">
              Discover more than a profile.
            </h2>

            <p className="mx-auto mt-5 max-w-2xl leading-7 text-[#687080]">
              Vynk is built around what you want to experience, not just who
              you are.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {discoveryCards.map((item, index) => (
              <article
                key={item.title}
                className={`group transform rounded-[2rem] ${item.bg} p-7 transition-all duration-500 hover:-translate-y-3 hover:shadow-2xl`}
                style={{
                  animation: `float ${5 + index}s ease-in-out infinite`,
                }}
              >
                <div className="flex h-14 w-14 transform items-center justify-center rounded-2xl bg-white text-2xl shadow-sm transition-transform duration-300 group-hover:rotate-6 group-hover:scale-110">
                  {item.icon}
                </div>

                <h3 className="mt-8 text-2xl font-bold">{item.title}</h3>

                <p className="mt-3 leading-7 text-[#606878]">
                  {item.text}
                </p>

                <span className="mt-7 inline-block text-2xl transition-transform duration-300 group-hover:translate-x-3">
                  →
                </span>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-white px-6 py-20 md:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#19A9A1]">
                How Vynk works
              </p>

              <h2 className="mt-4 text-4xl font-bold leading-tight md:text-5xl">
                Less searching.
                <br />
                More doing.
              </h2>

              <p className="mt-5 max-w-md leading-7 text-[#697180]">
                You bring the intention. Vynk helps turn it into a real
                possibility.
              </p>

              <div className="mt-8 inline-flex animate-pulse items-center gap-2 rounded-full bg-[#DDF5F0] px-4 py-2 text-sm font-semibold text-[#176D65]">
                <span>●</span>
                Your next move starts here
              </div>
            </div>

            <div className="space-y-4">
              {steps.map((step, index) => (
                <div
                  key={step.number}
                  className="group flex transform gap-5 rounded-3xl border border-[#E8E6E0] bg-[#FAF9F6] p-6 transition-all duration-300 hover:-translate-x-2 hover:border-[#BFC4EF] hover:bg-[#F8F7FD] hover:shadow-lg"
                >
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-sm font-bold transition-transform duration-300 group-hover:rotate-6 group-hover:scale-110 ${
                      index === 0
                        ? "bg-[#DDF5F0] text-[#176D65]"
                        : index === 1
                          ? "bg-[#E8E4FA] text-[#5B4DB5]"
                          : "bg-[#F8E7C9] text-[#856426]"
                    }`}
                  >
                    {step.number}
                  </div>

                  <div>
                    <h3 className="text-lg font-bold">{step.title}</h3>

                    <p className="mt-1 text-sm leading-6 text-[#6C7280]">
                      {step.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="bg-[#F7F6F2] px-6 py-20 md:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="relative overflow-hidden rounded-[2.5rem] bg-[#172033] px-7 py-12 text-center md:px-12 md:py-16">
            <div className="absolute -left-20 -top-24 h-64 w-64 animate-pulse rounded-full bg-[#48DED5]/10 blur-2xl" />

            <div
              className="absolute -bottom-24 -right-20 h-72 w-72 animate-pulse rounded-full bg-[#7568EA]/20 blur-2xl"
              style={{ animationDelay: "1s" }}
            />

            <div className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full border border-white/5" />

            <div className="relative">
              <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#48DED5]">
                Your next thing is waiting
              </p>

              <h2 className="mx-auto mt-4 max-w-3xl text-3xl font-bold text-white md:text-5xl">
                Don't just wonder what could happen.
                <span className="text-[#F3D69C]"> Vynk it.</span>
              </h2>

              <p className="mx-auto mt-5 max-w-xl leading-7 text-[#C5C9D5]">
                Start with one idea, one interest, or one “I feel like...”
              </p>

              <Link
                href="/signup"
                className="mt-8 inline-flex transform rounded-2xl bg-[#F3D69C] px-7 py-3.5 text-sm font-bold text-[#172033] shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-[#F8E5B9] hover:shadow-2xl"
              >
                Create your Vynk
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ANIMATION STYLES */}
      <style jsx>{`
        @keyframes float {
          0%,
          100% {
            transform: translateY(0px);
          }

          50% {
            transform: translateY(-10px);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(12px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </main>
  );
}