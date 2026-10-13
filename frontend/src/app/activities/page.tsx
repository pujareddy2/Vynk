"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import activityService, { Activity } from "../../services/activity.service";
import userService, { MasterInterest } from "../../services/user.service";

interface ActivityItem {
  id: number;
  interest_id?: number;
  title: string;
  category: string;
  people: string;
  icon: string;
  description: string;
}

const initialActivities: ActivityItem[] = [
  {
    id: 1,
    interest_id: 1,
    title: "Weekend Cycling & Lake Trail",
    category: "Outdoor",
    people: "8 people interested",
    icon: "🚴",
    description: "Scenic 20km leisure ride around the lake trail with breakfast stop.",
  },
  {
    id: 2,
    interest_id: 2,
    title: "Coffee & Conversations Meetup",
    category: "Social",
    people: "12 people interested",
    icon: "☕",
    description: "Casual weekend meetup for coffee lovers and conversation seekers.",
  },
  {
    id: 3,
    interest_id: 3,
    title: "Evening Badminton Match & Sparring",
    category: "Sports",
    people: "6 people interested",
    icon: "🏸",
    description: "Friendly doubles matches for intermediate and casual players.",
  },
  {
    id: 4,
    interest_id: 4,
    title: "Golden Hour Photography Walk",
    category: "Creative",
    people: "10 people interested",
    icon: "📷",
    description: "Explore heritage alleys and capture golden light with fellow creators.",
  },
  {
    id: 5,
    interest_id: 5,
    title: "Board Game Night & Catan Match",
    category: "Games",
    people: "14 people interested",
    icon: "🎲",
    description: "Fun strategy tabletop games and social deduction games over snacks.",
  },
  {
    id: 6,
    interest_id: 6,
    title: "Sunrise Yoga & Breathwork",
    category: "Wellness",
    people: "9 people interested",
    icon: "🧘",
    description: "Calm outdoor stretch and mindful breathing session in the park.",
  },
];

const categoryFilters = ["All", "Sports", "Outdoor", "Creative", "Social", "Games", "Wellness"];

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<ActivityItem[]>(initialActivities);
  const [interestsCatalog, setInterestsCatalog] = useState<MasterInterest[]>([]);
  const [activeFilter, setActiveFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [joinedActivities, setJoinedActivities] = useState<Record<number, boolean>>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createdSuccess, setCreatedSuccess] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // New activity form
  const [newTitle, setNewTitle] = useState("");
  const [selectedInterestId, setSelectedInterestId] = useState<number>(1);
  const [newCategory, setNewCategory] = useState("Sports");
  const [newDesc, setNewDesc] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [backendActs, catalog] = await Promise.all([
          activityService.getActivities().catch(() => []),
          userService.getInterestsCatalog().catch(() => []),
        ]);

        if (Array.isArray(catalog) && catalog.length > 0) {
          setInterestsCatalog(catalog);
          setSelectedInterestId(catalog[0].interest_id);
        }

        if (Array.isArray(backendActs) && backendActs.length > 0) {
          const mapped: ActivityItem[] = backendActs.map((act) => {
            const cat = act.interest_category || "Social";
            const icon =
              cat === "Sports" ? "🏸" :
              cat === "Outdoor" ? "🚴" :
              cat === "Creative" ? "📷" :
              cat === "Music" ? "🎸" :
              cat === "Technology" ? "💻" : "✦";
            return {
              id: act.activity_id,
              interest_id: act.interest_id,
              title: act.title,
              category: cat,
              people: "Verified Community Experience",
              icon,
              description: act.description || `Community-led ${cat.toLowerCase()} experience in Hyderabad.`,
            };
          });
          setActivities(mapped);
        }
      } catch {}
    }
    loadData();
  }, []);

  const toggleInterest = (id: number, title: string) => {
    const isSaved = !!joinedActivities[id];
    setJoinedActivities((prev) => ({ ...prev, [id]: !isSaved }));
    setToastMessage(!isSaved ? `💖 Saved "${title}" to your radar!` : `Removed "${title}".`);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const visibleActivities = activities.filter((act) => {
    const matchesFilter = activeFilter === "All" || act.category.toLowerCase() === activeFilter.toLowerCase();
    const matchesSearch = !searchQuery.trim() ||
      act.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleCreateActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setIsSubmitting(true);
    try {
      const created = await activityService.createActivity({
        interest_id: selectedInterestId,
        title: newTitle.trim(),
        description: newDesc.trim(),
      });

      const newAct: ActivityItem = {
        id: created.activity_id || Date.now(),
        interest_id: selectedInterestId,
        title: newTitle.trim(),
        category: newCategory,
        people: "1 person interested",
        icon: newCategory === "Sports" ? "🏸" : newCategory === "Outdoor" ? "🚴" : newCategory === "Creative" ? "📷" : "✦",
        description: newDesc.trim() || `Community-led ${newCategory.toLowerCase()} meetup.`,
      };

      setActivities((prev) => [newAct, ...prev]);
      setJoinedActivities((prev) => ({ ...prev, [newAct.id]: true }));
      setCreatedSuccess(true);
      setToastMessage("🎉 Activity proposed & published to radar!");

      setTimeout(() => {
        setShowCreateModal(false);
        setCreatedSuccess(false);
        setNewTitle("");
        setNewDesc("");
        setToastMessage(null);
      }, 1500);
    } catch {
      // Local optimistic fallback
      const newAct: ActivityItem = {
        id: Date.now(),
        interest_id: selectedInterestId,
        title: newTitle.trim(),
        category: newCategory,
        people: "1 person interested",
        icon: newCategory === "Sports" ? "🏸" : newCategory === "Outdoor" ? "🚴" : "✦",
        description: newDesc.trim(),
      };
      setActivities((prev) => [newAct, ...prev]);
      setJoinedActivities((prev) => ({ ...prev, [newAct.id]: true }));
      setCreatedSuccess(true);
      setTimeout(() => {
        setShowCreateModal(false);
        setCreatedSuccess(false);
        setNewTitle("");
        setNewDesc("");
      }, 1500);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageContainer>
      <div className="space-y-8">
        {/* TOAST BANNER */}
        {toastMessage && (
          <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-2xl bg-slate-900/95 text-white px-5 py-2.5 text-xs font-semibold shadow-2xl backdrop-blur-md border border-teal-500/50 animate-in fade-in slide-in-from-top-4 duration-200">
            <span>✨</span> {toastMessage}
          </div>
        )}

        {/* HERO */}
        <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-teal-950 p-8 text-white shadow-xl md:p-10 border border-slate-800">
          <div className="relative z-10 max-w-2xl">
            <span className="flex items-center gap-1.5 rounded-full bg-teal-500/20 border border-teal-400/30 px-3 py-1 text-xs font-semibold text-teal-300 w-fit">
              <span>✦</span> Activities & Plans Catalog
            </span>

            <h1 className="mt-4 text-3xl font-extrabold text-white md:text-5xl tracking-tight">
              Find something you actually want to do.
            </h1>

            <p className="mt-3 leading-relaxed text-slate-300 text-sm md:text-base">
              Browse community activities based on your interests, sparring needs, and energy. Connect with local partners who share your plan.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="rounded-xl bg-teal-400 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 transition cursor-pointer"
              >
                + Propose New Activity
              </button>
              <Link
                href="/connections"
                className="rounded-xl border border-white/20 bg-white/10 px-5 py-2.5 text-xs font-semibold text-white hover:bg-white/15 transition"
              >
                Find Partners on Radar 🎴
              </Link>
            </div>
          </div>

          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-400/10 pointer-events-none" />
        </section>

        {/* SEARCH & FILTERS BAR */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search activities (e.g. Badminton, Cycling, Coffee, Board games)..."
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-2.5 pl-9 text-xs text-slate-900 placeholder:text-slate-400 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                🔍
              </span>
            </div>

            {/* Counter */}
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Showing {visibleActivities.length} activities
            </span>
          </div>

          {/* Category Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
            {categoryFilters.map((filter) => {
              const isActive = activeFilter === filter;
              return (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setActiveFilter(filter)}
                  className={`whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition cursor-pointer ${
                    isActive
                      ? "bg-teal-400 text-slate-950 font-bold shadow-sm"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700 dark:hover:bg-slate-750"
                  }`}
                >
                  {filter}
                </button>
              );
            })}
          </div>

          {/* ACTIVITY CARDS GRID */}
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {visibleActivities.map((activity) => {
              const isJoined = !!joinedActivities[activity.id];

              return (
                <article
                  key={activity.id}
                  className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-1 hover:shadow-md dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start gap-4">
                      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-2xl dark:bg-teal-950/80">
                        {activity.icon}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                            {activity.category}
                          </span>
                          <span className="text-[11px] text-slate-500 dark:text-slate-400">
                            {activity.people}
                          </span>
                        </div>

                        <h3 className="mt-1 text-base font-bold text-slate-900 dark:text-white leading-snug">
                          {activity.title}
                        </h3>

                        <p className="mt-1.5 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                          {activity.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Actions Toolbar */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/connections`}
                        className="rounded-xl border border-teal-500/30 bg-teal-50/60 px-3 py-1.5 text-[11px] font-bold text-teal-800 dark:bg-teal-950/40 dark:text-teal-300 hover:bg-teal-100 transition"
                      >
                        🎴 Find Sparring Partners
                      </Link>

                      <Link
                        href={`/events`}
                        className="rounded-xl border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                      >
                        ◈ Host Event
                      </Link>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleInterest(activity.id, activity.title)}
                      className={`rounded-xl px-4 py-1.5 text-xs font-bold transition cursor-pointer ${
                        isJoined
                          ? "bg-teal-600 text-white hover:bg-teal-700"
                          : "bg-slate-100 text-slate-800 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200"
                      }`}
                    >
                      {isJoined ? "Interested ✓" : "+ Save"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* CTA TO PROPOSE NEW ACTIVITY */}
        <section className="rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-teal-950 p-6 text-white border border-slate-800 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-teal-300">
              Have your own idea?
            </p>
            <h2 className="mt-1 text-xl font-bold text-white">
              Create an activity and bring people together.
            </h2>
            <p className="mt-1 text-xs text-slate-300">
              Propose a new sports sparring drill, photo walk, or gaming circle in Hyderabad.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="rounded-2xl bg-teal-400 px-6 py-3 text-xs font-bold text-slate-950 hover:bg-teal-300 transition cursor-pointer shrink-0"
          >
            + Propose Activity
          </button>
        </section>

        {/* CREATE ACTIVITY MODAL */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md rounded-[2.5rem] bg-white p-7 shadow-2xl dark:bg-slate-900 dark:text-white">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-bold">Propose a New Activity</h3>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {createdSuccess ? (
                <div className="py-8 text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-teal-100 text-2xl text-teal-600 animate-bounce">
                    ✓
                  </div>
                  <h4 className="mt-4 text-lg font-bold">Activity Published!</h4>
                  <p className="mt-2 text-xs text-slate-500">
                    Your activity is now live on the Vynk Radar for peers to join.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleCreateActivity} className="mt-5 space-y-4">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 block mb-1">
                      Activity Title
                    </label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Evening Pickleball Drills, Sunset Coffee Walk"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 block mb-1">
                        Category
                      </label>
                      <select
                        value={newCategory}
                        onChange={(e) => setNewCategory(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      >
                        <option value="Sports">Sports</option>
                        <option value="Outdoor">Outdoor</option>
                        <option value="Social">Social</option>
                        <option value="Creative">Creative</option>
                        <option value="Games">Games</option>
                        <option value="Wellness">Wellness</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 block mb-1">
                        Linked Interest
                      </label>
                      <select
                        value={selectedInterestId}
                        onChange={(e) => setSelectedInterestId(Number(e.target.value))}
                        className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      >
                        {interestsCatalog.length > 0 ? (
                          interestsCatalog.map((i) => (
                            <option key={i.interest_id} value={i.interest_id}>
                              {i.name}
                            </option>
                          ))
                        ) : (
                          <>
                            <option value={1}>Badminton</option>
                            <option value={2}>Cycling</option>
                            <option value={3}>Photography</option>
                            <option value={4}>Coffee</option>
                            <option value={5}>Board Games</option>
                          </>
                        )}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 block mb-1">
                      Short Description
                    </label>
                    <textarea
                      required
                      placeholder="What will you do? What should people bring?"
                      rows={3}
                      value={newDesc}
                      onChange={(e) => setNewDesc(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowCreateModal(false)}
                      className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="rounded-xl bg-teal-400 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-teal-300 transition cursor-pointer disabled:opacity-50"
                    >
                      {isSubmitting ? "Publishing..." : "Publish Activity"}
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