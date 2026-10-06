"use client";

import {
  ArrowRight,
  Heart,
  MapPin,
  Users,
  Sparkles,
  Search,
} from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0b0f14] text-white">
      {/* Navigation */}
      <nav className="border-b border-white/10 bg-[#0b0f14]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black">
              <Sparkles size={19} />
            </div>

            <span className="text-2xl font-bold tracking-tight">
              Vynk
            </span>
          </div>

          <div className="hidden items-center gap-8 text-sm text-gray-300 md:flex">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>
            <a href="#about" className="transition hover:text-white">
              About
            </a>
            <a href="/login" className="transition hover:text-white">
              Login
            </a>

            <a
              href="/signup"
              className="rounded-full bg-white px-5 py-2.5 font-semibold text-black transition hover:bg-gray-200"
            >
              Get Started
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute left-1/2 top-20 h-72 w-72 -translate-x-1/2 rounded-full bg-purple-500/20 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-6 pb-24 pt-24 text-center md:pb-32 md:pt-32">
          <div className="mx-auto mb-6 flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-300">
            <Sparkles size={15} />
            Connect. Discover. Vynk.
          </div>

          <h1 className="mx-auto max-w-4xl text-5xl font-bold leading-tight tracking-tight md:text-7xl">
            Find people.
            <br />
            <span className="text-gray-400">Find your thing.</span>
          </h1>

          <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-gray-400 md:text-xl">
            Vynk helps you discover activities, people, communities and
            opportunities based on what you actually want to do.
          </p>

          <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">
            <a
              href="/signup"
              className="group flex items-center justify-center gap-2 rounded-full bg-white px-7 py-3.5 font-semibold text-black transition hover:scale-105"
            >
              Get Started
              <ArrowRight
                size={18}
                className="transition-transform group-hover:translate-x-1"
              />
            </a>

            <a
              href="/login"
              className="rounded-full border border-white/15 bg-white/5 px-7 py-3.5 font-semibold text-white transition hover:bg-white/10"
            >
              Sign In
            </a>
          </div>
        </div>
      </section>

      {/* Search Preview */}
      <section className="mx-auto max-w-5xl px-6 pb-24">
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl md:p-7">
          <div className="mb-5 flex items-center gap-3 text-sm text-gray-400">
            <Search size={17} />
            Try Vynk's intelligent search
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#11161d] p-5">
            <p className="text-sm text-gray-500">What are you looking for?</p>

            <p className="mt-2 text-lg text-gray-200">
              "I want to play badminton this Saturday evening."
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs text-gray-300">
                Badminton
              </span>

              <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs text-gray-300">
                Saturday
              </span>

              <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs text-gray-300">
                Evening
              </span>

              <span className="rounded-full bg-white/10 px-3 py-1.5 text-xs text-gray-300">
                Nearby
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-y border-white/10 bg-white/[0.02]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-widest text-gray-500">
              What Vynk does
            </p>

            <h2 className="mt-3 text-3xl font-bold md:text-4xl">
              One place to discover more.
            </h2>

            <p className="mt-4 text-gray-400">
              Discover activities and people that match your interests,
              location and availability.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            <FeatureCard
              icon={<Users size={22} />}
              title="Meet People"
              description="Find people with similar interests, skills and availability."
            />

            <FeatureCard
              icon={<MapPin size={22} />}
              title="Discover Activities"
              description="Explore activities and opportunities happening around you."
            />

            <FeatureCard
              icon={<Heart size={22} />}
              title="Build Communities"
              description="Join communities and connect with people who share your interests."
            />
          </div>
        </div>
      </section>

      {/* About */}
      <section id="about" className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid gap-12 md:grid-cols-2 md:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-gray-500">
              About Vynk
            </p>

            <h2 className="mt-3 text-3xl font-bold md:text-4xl">
              Turn intentions into connections.
            </h2>

            <p className="mt-6 leading-8 text-gray-400">
              Instead of searching through endless lists, simply tell Vynk
              what you want to do. Our platform is designed to help you
              discover relevant people, activities and communities.
            </p>

            <a
              href="/signup"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 font-semibold text-black transition hover:bg-gray-200"
            >
              Start with Vynk
              <ArrowRight size={17} />
            </a>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <StatCard number="01" text="Discover" />
            <StatCard number="02" text="Connect" />
            <StatCard number="03" text="Participate" />
            <StatCard number="04" text="Grow" />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-8 text-sm text-gray-500 md:flex-row md:items-center md:justify-between">
          <p>© 2026 Vynk. All rights reserved.</p>

          <p>Connect. Discover. Vynk.</p>
        </div>
      </footer>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-7 transition hover:-translate-y-1 hover:bg-white/[0.05]">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-black">
        {icon}
      </div>

      <h3 className="mt-6 text-xl font-semibold">{title}</h3>

      <p className="mt-3 leading-7 text-gray-400">{description}</p>
    </div>
  );
}

function StatCard({
  number,
  text,
}: {
  number: string;
  text: string;
}) {
  return (
    <div className="flex min-h-40 flex-col justify-between rounded-3xl border border-white/10 bg-white/[0.03] p-6">
      <span className="text-sm text-gray-500">{number}</span>

      <span className="text-xl font-semibold">{text}</span>
    </div>
  );
}