"use client";

import Link from "next/link";
import { useState } from "react";

const moods = [
  {
    label: "Meet people",
    icon: "👋",
    title: "Find people who match your energy.",
    description: "Discover verified locals nearby who share your exact interests, pace, and schedule.",
    prompt: "“I want to meet people who play badminton and grab coffee afterwards.”",
  },
  {
    label: "Try something",
    icon: "✨",
    title: "Discover spontaneous local activities.",
    description: "Explore curated sessions, weekend workshops, and evening sparring matches.",
    prompt: "“Looking for an outdoor sunset photography walk around the lake this weekend.”",
  },
  {
    label: "Find a community",
    icon: "👥",
    title: "Join communities where you belong.",
    description: "Connect with high-affinity micro-communities that host recurring local gatherings.",
    prompt: "“Join an active Hyderabad board gaming or cycling community.”",
  },
];

const discoveries = [
  {
    name: "Evening Badminton Sparring",
    icon: "🏸",
    people: "8 players interested",
    tag: "Sports",
  },
  {
    name: "Specialty Coffee & Conversations",
    icon: "☕",
    people: "14 members interested",
    tag: "Social",
  },
  {
    name: "Heritage Street Photography Walk",
    icon: "📷",
    people: "11 photographers interested",
    tag: "Creative",
  },
];

const discoveryCards = [
  {
    icon: "🎴",
    title: "People & Swipe Matching",
    text: "Swipe right to connect for sports, games, and hobbies with instant vibe matching.",
    href: "/connections",
  },
  {
    icon: "⚡",
    title: "Activities & Split-Cost",
    text: "Find or host activities with automated venue booking and split payments.",
    href: "/activities",
  },
  {
    icon: "💫",
    title: "Thriving Communities",
    text: "Join curated local circles with AI-assisted health monitoring and recurring meetups.",
    href: "/communities",
  },
];

const steps = [
  {
    number: "01",
    title: "Register & Pick Interests",
    text: "Set up your profile, choose your favorite activities, and define your local vibe.",
  },
  {
    number: "02",
    title: "Swipe & Express Intent",
    text: "Swipe right on people with shared hobbies, or state what you want to do in natural language.",
  },
  {
    number: "03",
    title: "Meet, Play & Belong",
    text: "Join scheduled events, split venue costs fairly, and build lasting friendships.",
  },
];

export default function HomePage() {
  const [selectedMood, setSelectedMood] = useState(0);
  const [showDiscoveries, setShowDiscoveries] = useState(false);

  const mood = moods[selectedMood];

  return (
    <main className="overflow-hidden bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-white transition-colors duration-300">
      {/* HERO */}
      <section className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-white">
        {/* Ambient Gradient Glows */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -right-40 -top-40 h-[36rem] w-[36rem] rounded-full bg-teal-500/15 blur-3xl" />
          <div className="absolute -bottom-48 -left-40 h-[36rem] w-[36rem] rounded-full bg-indigo-600/20 blur-3xl" />
          <div className="absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-emerald-500/10 blur-2xl" />
        </div>

        <div className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:py-20">
          {/* HERO CONTENT */}
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-teal-300 backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
              AI-Powered Local Connections &amp; Split-Cost Network
            </div>

            <h1 className="mt-6 text-4xl font-extrabold leading-[1.05] tracking-tight text-white sm:text-5xl lg:text-6xl">
              What do you feel like{" "}
              <span className="bg-gradient-to-r from-teal-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
                doing today?
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-300 sm:text-lg">
              Tell Vynk what you want to do. We connect you with people who share your passion, coordinate the venue, split costs automatically, and bring the plan to life.
            </p>

            {/* MOOD TABS */}
            <div className="mt-8 flex flex-wrap gap-2.5">
              {moods.map((item, index) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => {
                    setSelectedMood(index);
                    setShowDiscoveries(false);
                  }}
                  className={`rounded-2xl px-4 py-2.5 text-xs font-bold transition-all duration-200 cursor-pointer ${
                    selectedMood === index
                      ? "bg-teal-400 text-slate-950 shadow-md scale-105"
                      : "border border-slate-800 bg-slate-900/80 text-slate-300 hover:border-slate-700 hover:text-white"
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>

            {/* CALL TO ACTION BUTTONS */}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="rounded-2xl bg-teal-400 px-7 py-3.5 text-center text-sm font-bold text-slate-950 shadow-lg shadow-teal-500/20 transition hover:bg-teal-300 hover:scale-[1.02]"
              >
                Create Account &amp; Start
              </Link>

              <Link
                href="/connections"
                className="rounded-2xl border border-slate-700 bg-slate-900/80 px-6 py-3.5 text-center text-sm font-semibold text-white transition hover:border-teal-500/50 hover:bg-slate-800"
              >
                🎴 Try Swipe Matching
              </Link>
            </div>
          </div>

          {/* INTERACTIVE PREVIEW CARD */}
          <div className="relative mx-auto w-full max-w-lg">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-2xl backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-teal-400">
                    Your Vynk Match Radar
                  </p>
                  <h2 className="mt-1 text-2xl font-bold text-white">
                    {mood.title}
                  </h2>
                </div>

                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-500/20 text-2xl text-teal-300">
                  {mood.icon}
                </div>
              </div>

              <p className="mt-3 text-sm leading-relaxed text-slate-300">
                {mood.description}
              </p>

              <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Try Expressing Intent
                </p>
                <p className="mt-1.5 text-sm font-medium text-teal-200">
                  {mood.prompt}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowDiscoveries((c) => !c)}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-teal-500/20 border border-teal-500/30 px-5 py-3 text-xs font-bold text-teal-300 transition hover:bg-teal-500/30 cursor-pointer"
              >
                {showDiscoveries ? "Hide Live Discoveries ▲" : "Show Live Discoveries ▼"}
              </button>

              {showDiscoveries && (
                <div className="mt-4 space-y-2.5 pt-2 border-t border-slate-800">
                  {discoveries.map((item) => (
                    <div
                      key={item.name}
                      className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-950/50 p-3"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-lg">
                        {item.icon}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-bold text-white">
                          {item.name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {item.people}
                        </p>
                      </div>
                      <span className="rounded-full bg-teal-500/20 px-2.5 py-1 text-[10px] font-semibold text-teal-300">
                        {item.tag}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* FLOATING PHILOSOPHY BADGE */}
            <div className="absolute -bottom-5 -left-5 hidden sm:flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/95 px-4 py-3 shadow-xl backdrop-blur">
              <span className="text-lg">💡</span>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">The Vynk Flow</p>
                <p className="text-xs font-bold text-teal-300">Action &gt; Endless Swiping</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* DISCOVERY SECTION */}
      <section className="px-6 py-20 max-w-7xl mx-auto">
        <div className="text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400">
            One Unified Platform
          </p>
          <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
            Everything you need to do things in real life.
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            From discovering like-minded companions to booking badminton courts or joining weekend photo walks.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {discoveryCards.map((item) => (
            <Link
              key={item.title}
              href={item.href}
              className="group rounded-3xl bg-white p-7 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-1 hover:shadow-xl dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between"
            >
              <div>
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-2xl dark:bg-teal-950/60 transition group-hover:scale-110">
                  {item.icon}
                </div>
                <h3 className="mt-6 text-xl font-bold text-slate-900 dark:text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                  {item.text}
                </p>
              </div>
              <div className="mt-6 flex items-center gap-1 text-sm font-semibold text-teal-600 dark:text-teal-400 group-hover:translate-x-1 transition">
                <span>Explore</span>
                <span>→</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-slate-100/60 py-20 px-6 dark:bg-slate-900/40 border-y border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400">
                Step-by-step Experience
              </p>
              <h2 className="mt-2 text-3xl font-extrabold leading-tight text-slate-900 dark:text-white sm:text-4xl">
                Zero friction.
                <br />
                Pure connection.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                You bring your interest and free time. Vynk handles discovery, group consensus, venue split payments, and notification updates.
              </p>
            </div>

            <div className="space-y-4">
              {steps.map((step) => (
                <div
                  key={step.number}
                  className="flex gap-5 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-sm font-bold text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                    {step.number}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      {step.title}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      {step.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CALL TO ACTION */}
      <section className="px-6 py-20 max-w-7xl mx-auto">
        <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-teal-900 px-8 py-16 text-center text-white shadow-xl md:px-16">
          <div className="relative mx-auto max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-widest text-teal-300">
              Your Next Adventure Is Waiting
            </p>
            <h2 className="mt-3 text-3xl font-extrabold sm:text-4xl">
              Don&apos;t just stay at home.
              <span className="text-teal-300"> Vynk it.</span>
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-slate-300">
              Join thousands of locals sharing authentic passions, building communities, and experiencing life together.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/signup"
                className="w-full sm:w-auto rounded-2xl bg-teal-400 px-8 py-3.5 text-sm font-bold text-slate-950 shadow-lg hover:bg-teal-300 transition"
              >
                Sign Up Now — It&apos;s Free
              </Link>
              <Link
                href="/login"
                className="w-full sm:w-auto rounded-2xl border border-white/20 bg-white/10 px-6 py-3.5 text-sm font-semibold text-white hover:bg-white/20 transition"
              >
                Already have an account? Sign In
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}