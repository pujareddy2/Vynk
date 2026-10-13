"use client";

import { useState } from "react";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";

const initialCreators = [
  {
    name: "Vikram Reddy",
    category: "Sports",
    followers: "18.4K followers",
    bio: "Badminton enthusiast and local tournament organizer hosting weekly matches across central Hyderabad.",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Badminton & Squash",
    engagement: "Very High",
    tags: ["Sports", "Tournament", "Badminton"],
  },
  {
    name: "Dr. Ananya Sen",
    category: "Wellness",
    followers: "14.2K followers",
    bio: "Mindfulness practitioner organizing Sunday nature walks, yoga retreats, and sound bath sessions.",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Nature Walks & Yoga",
    engagement: "High",
    tags: ["Wellness", "Outdoor", "Meditation"],
  },
  {
    name: "Maya Kapoor",
    category: "Photography",
    followers: "12.4K followers",
    bio: "Street photographer sharing hidden architectural corners, golden hour walks, and camera workshops.",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Street Photography",
    engagement: "High",
    tags: ["Photography", "Travel", "Creative"],
  },
  {
    name: "Riya Sharma",
    category: "Lifestyle",
    followers: "8.7K followers",
    bio: "Curating cozy café meetups, book discussions, and creative conversations for thoughtful people.",
    avatar: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Café Meetups",
    engagement: "High",
    tags: ["Coffee", "Books", "Lifestyle"],
  },
  {
    name: "Arjun Mehta",
    category: "Fitness",
    followers: "15.2K followers",
    bio: "Cycling and outdoor fitness lead making movement social, high-energy, and sustainable.",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Cycling & HIIT",
    engagement: "High",
    tags: ["Fitness", "Cycling", "Wellness"],
  },
  {
    name: "Nisha Rao",
    category: "Travel",
    followers: "10.8K followers",
    bio: "Weekend explorer leading city heritage trails, lake trails, and spontaneous getaway groups.",
    avatar: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&auto=format&fit=crop&q=80",
    location: "Hyderabad",
    specialty: "Heritage Trails",
    engagement: "Medium",
    tags: ["Travel", "Adventure", "Exploring"],
  },
];

const categories = [
  "All",
  "Sports",
  "Photography",
  "Fitness",
  "Lifestyle",
  "Travel",
];

export default function CreatorsPage() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [followed, setFollowed] = useState<Record<string, boolean>>({});
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyRole, setApplyRole] = useState("Activity Host");

  const toggleFollow = (name: string) => {
    setFollowed((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const visibleCreators = initialCreators.filter((creator) => {
    if (activeCategory === "All") return true;
    return creator.category.toLowerCase() === activeCategory.toLowerCase();
  });

  const handleApplySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setApplied(true);
    setTimeout(() => {
      setShowApplyModal(false);
      setApplied(false);
    }, 1500);
  };

  return (
    <PageContainer>
      <div className="space-y-8">
        {/* TOP FLOW BREADCRUMBS */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            <span>Navigation:</span>
            <Link href="/dashboard" className="hover:text-teal-500 transition">1. Dashboard</Link>
            <span>→</span>
            <Link href="/activities" className="hover:text-teal-500 transition">2. Activities</Link>
            <span>→</span>
            <Link href="/events" className="hover:text-teal-500 transition">3. Events Hub</Link>
            <span>→</span>
            <Link href="/communities" className="hover:text-teal-500 transition">4. Communities</Link>
            <span>→</span>
            <span className="text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950 px-2 py-0.5 rounded-md font-bold">
              ✦ 5. Verified Creators & Hosts
            </span>
            <span>→</span>
            <Link href="/connections" className="hover:text-teal-500 transition">6. Peer Match Deck</Link>
          </div>
        </div>

        {/* HERO */}
        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-900 via-indigo-950 to-teal-900 p-8 text-white shadow-lg ring-1 ring-white/10 md:p-10">
          <div className="relative z-10 max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-300">
              Community Hosts & Leaders
            </p>

            <h1 className="mt-3 text-4xl font-bold text-white md:text-5xl">
              Find leaders worth following.
            </h1>

            <p className="mt-4 leading-7 text-slate-300">
              Discover experienced organizers, sports hosts, and local curators
              who create memorable sessions across Vynk.
            </p>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-400/10" />
          <div className="absolute -bottom-20 right-24 h-48 w-48 rounded-full bg-indigo-500/10" />
        </section>

        {/* FILTERS */}
        <section>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium text-teal-600 dark:text-teal-400">
                Organizer Community
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                Featured Activity Leads
              </h2>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-1">
              {categories.map((category) => {
                const isActive = activeCategory === category;
                return (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setActiveCategory(category)}
                    className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition cursor-pointer ${
                      isActive
                        ? "bg-slate-900 text-white shadow-sm dark:bg-white dark:text-slate-900"
                        : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700"
                    }`}
                  >
                    {category}
                  </button>
                );
              })}
            </div>
          </div>

          {/* CREATOR CARDS */}
          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            {visibleCreators.map((creator) => {
              const isFollowing = !!followed[creator.name];

              return (
                <article
                  key={creator.name}
                  className="rounded-[1.75rem] bg-white p-6 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-1 hover:shadow-lg dark:bg-slate-900 dark:ring-slate-800"
                >
                  {/* HEADER */}
                  <div className="flex items-start gap-4">
                    <img
                      src={creator.avatar}
                      alt={creator.name}
                      className="h-16 w-16 shrink-0 rounded-2xl object-cover shadow-sm ring-1 ring-slate-200 dark:ring-slate-700"
                    />

                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                            {creator.name}
                          </h3>

                          <p className="mt-1 text-sm font-medium text-teal-600 dark:text-teal-400">
                            {creator.category}
                          </p>
                        </div>

                        <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          Host
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* BIO */}
                  <p className="mt-5 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {creator.bio}
                  </p>

                  {/* CREATOR INFO */}
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Location
                      </p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                        {creator.location}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Specialty
                      </p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                        {creator.specialty}
                      </p>
                    </div>
                  </div>

                  {/* TAGS */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {creator.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-teal-50 px-3 py-1.5 text-xs font-medium text-teal-700 dark:bg-teal-950/60 dark:text-teal-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* FOOTER */}
                  <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-white">
                        {creator.followers}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {creator.engagement} rating
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleFollow(creator.name)}
                      className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition cursor-pointer ${
                        isFollowing
                          ? "bg-teal-600 text-white hover:bg-teal-700"
                          : "bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                      }`}
                    >
                      {isFollowing ? "Following ✓" : "Follow"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* CTA */}
        <section className="rounded-3xl bg-gradient-to-r from-slate-900 to-indigo-950 p-6 text-white ring-1 ring-white/10 md:p-8">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-teal-300">
                Organize with Vynk
              </p>

              <h2 className="mt-1 text-xl font-bold text-white">
                Want to become a verified host or community lead?
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">
                Create events, facilitate group bookings, and build a local following around the activities you love.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowApplyModal(true)}
              className="rounded-xl bg-teal-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-teal-300 cursor-pointer"
            >
              Apply as Host
            </button>
          </div>
        </section>

        {/* HOST APPLICATION MODAL */}
        {showApplyModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-3xl bg-white p-7 shadow-2xl dark:bg-slate-900 dark:text-white">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold">Apply as a Vynk Host</h3>
                <button
                  type="button"
                  onClick={() => setShowApplyModal(false)}
                  className="rounded-lg p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {applied ? (
                <div className="py-8 text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-teal-100 text-2xl text-teal-600">
                    ✓
                  </div>
                  <h4 className="mt-4 text-lg font-bold">Application Received!</h4>
                  <p className="mt-2 text-sm text-slate-500">
                    We'll review your organizer profile and get back to you shortly.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleApplySubmit} className="mt-6 space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                      Primary Activity Domain
                    </label>
                    <select
                      value={applyRole}
                      onChange={(e) => setApplyRole(e.target.value)}
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                    >
                      <option value="Sports & Fitness">Sports & Fitness Host</option>
                      <option value="Creative & Arts">Creative & Photography Guide</option>
                      <option value="Social & Meetups">Social & Board Games Host</option>
                      <option value="Outdoor & Travel">Outdoor & Hiking Lead</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                      Past Hosting Experience / Short Bio
                    </label>
                    <textarea
                      required
                      placeholder="Tell us about the events or sessions you have organized..."
                      rows={3}
                      className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowApplyModal(false)}
                      className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="rounded-xl bg-slate-900 px-5 py-2 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-teal-500 dark:text-slate-950 cursor-pointer"
                    >
                      Submit Application
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
}