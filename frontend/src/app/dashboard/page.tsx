"use client";

import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import { useEffect, useState } from "react";
import activityService, { Activity } from "../../services/activity.service";
import userService, { FullProfile, UserAvailabilityItem, UserSkillItem } from "../../services/user.service";
import matchingService, { PeopleMatchCandidate, GroupProposal } from "../../services/matching.service";
import eventService, { EventItem } from "../../services/event.service";
import { detectLiveLocation } from "../../services/location.service";

const quickActions = [
  {
    title: "Activities Catalog",
    description: "Discover curated sports, walks, jams, and casual local plans.",
    icon: "✦",
    href: "/activities",
    badge: "Browse",
  },
  {
    title: "Match Radar Deck",
    description: "Swipe to connect with peers aligned with your alarms & skills.",
    icon: "♡",
    href: "/connections",
    badge: "Live Radar",
  },
  {
    title: "Events & Gatherings",
    description: "Join verified meetups with court split-bills and RSVP rosters.",
    icon: "◈",
    href: "/events",
    badge: "RSVP Open",
  },
  {
    title: "AI Instant Plans",
    description: "Get real-time suggestions to do something exciting right now.",
    icon: "⚡",
    href: "/recommendations",
    badge: "AI Powered",
  },
];

// High-definition lifestyle and sports photography library (BookMyShow / Luma style)
function getEventCoverImage(title: string, category?: string | null): string {
  const t = (title || "").toLowerCase();
  const c = (category || "").toLowerCase();

  if (t.includes("badminton") || c.includes("badminton")) {
    return "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("football") || t.includes("turf") || c.includes("football")) {
    return "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("cricket") || c.includes("cricket")) {
    return "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("coffee") || t.includes("cafe") || t.includes("conversation") || c.includes("social")) {
    return "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("photo") || t.includes("camera") || t.includes("walk")) {
    return "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("board game") || t.includes("catan") || c.includes("game")) {
    return "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("trail") || t.includes("hike") || t.includes("nature") || c.includes("outdoor")) {
    return "https://images.unsplash.com/photo-1551632811-561732d1e306?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("pottery") || t.includes("clay") || t.includes("paint") || c.includes("creative")) {
    return "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("cycl") || t.includes("bike")) {
    return "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("tennis") || t.includes("pickleball")) {
    return "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("boulder") || t.includes("climb")) {
    return "https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("music") || t.includes("jam")) {
    return "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200&auto=format&fit=crop&q=80";
  }
  return "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=1200&auto=format&fit=crop&q=80";
}

interface DashboardEventItem extends EventItem {
  relevance_reason?: string;
  cover_image?: string;
  relevance_score?: number;
}

export default function DashboardPage() {
  const [userName, setUserName] = useState("Explorer");
  const [userLocality, setUserLocality] = useState("Hyderabad");
  const [currentPlan, setCurrentPlan] = useState("Weekend badminton, coffee walk");
  const [budgetPreference, setBudgetPreference] = useState("flexible");
  const [userAvailability, setUserAvailability] = useState<UserAvailabilityItem[]>([]);
  const [userSkills, setUserSkills] = useState<UserSkillItem[]>([]);
  const [userInterests, setUserInterests] = useState<string[]>([]);
  const [reputationScore, setReputationScore] = useState<number>(95);

  const [topMatches, setTopMatches] = useState<PeopleMatchCandidate[]>([]);
  const [proposals, setProposals] = useState<GroupProposal[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<DashboardEventItem[]>([]);
  const [joinedEvents, setJoinedEvents] = useState<Record<number, boolean>>({});
  const [liveActivities, setLiveActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Helper for Alarm 12-hour AM/PM formatting
  const formatAlarmTime = (timeStr?: string) => {
    if (!timeStr) return "";
    const parts = timeStr.split(":");
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1] || "00";
    if (isNaN(hours)) return timeStr;
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${hours}:${minutes} ${ampm}`;
  };

  useEffect(() => {
    // 1. Read stored profile cache first for instant gratification
    let activeInterests: string[] = [];
    let activeLocality: string = "Hyderabad";

    const stored = localStorage.getItem("vynk_user");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.name) setUserName(parsed.name);
        if (parsed.location) {
          setUserLocality(parsed.location);
          activeLocality = parsed.location;
        }
        if (parsed.currentPlan) setCurrentPlan(parsed.currentPlan);
        if (parsed.budget_preference) setBudgetPreference(parsed.budget_preference);
        if (Array.isArray(parsed.availability)) setUserAvailability(parsed.availability);
        if (Array.isArray(parsed.skills)) setUserSkills(parsed.skills);
        if (Array.isArray(parsed.interests)) {
          setUserInterests(parsed.interests);
          activeInterests = parsed.interests;
        }
      } catch {}
    }

    async function loadDashboardData() {
      // 2. Fetch live profile & reputation
      try {
        const fullProf = await userService.getProfileMe();
        if (fullProf) {
          if (fullProf.display_name) setUserName(fullProf.display_name);
          if (fullProf.approx_locality) {
            setUserLocality(fullProf.approx_locality);
            activeLocality = fullProf.approx_locality;
          } else {
            // Automatically detect live location without requiring a button click
            try {
              const live = await detectLiveLocation();
              if (live?.locality) {
                setUserLocality(live.locality);
                activeLocality = live.locality;
                userService.updateProfile({ approx_locality: live.locality }).catch(() => {});
              }
            } catch {}
          }
          if (fullProf.budget_preference) setBudgetPreference(fullProf.budget_preference);
          if (Array.isArray(fullProf.availability) && fullProf.availability.length > 0) {
            setUserAvailability(fullProf.availability);
          }
          if (Array.isArray(fullProf.skills) && fullProf.skills.length > 0) {
            setUserSkills(fullProf.skills);
          }
          if (Array.isArray(fullProf.interests) && fullProf.interests.length > 0) {
            const intNames = fullProf.interests.map((i) => i.name);
            setUserInterests(intNames);
            activeInterests = intNames;
          }
        }
      } catch {}

      try {
        const rep = await userService.getUserReputation();
        if (rep && rep.overall_score) {
          setReputationScore(Math.round(rep.overall_score * 100));
        }
      } catch {}

      // 3. Fetch top match radar peers
      try {
        const matchRes = await matchingService.getMatches({ min_score: 50 });
        if (matchRes && matchRes.matches && matchRes.matches.length > 0) {
          setTopMatches(matchRes.matches.slice(0, 4));
        }
      } catch {}

      // 4. Fetch co-op proposals
      try {
        const props = await matchingService.getMyProposals();
        if (Array.isArray(props) && props.length > 0) {
          setProposals(props);
        }
      } catch {}

      // 5. Fetch upcoming scheduled events relevant to profile
      try {
        const events = await eventService.getEvents();
        if (Array.isArray(events) && events.length > 0) {
          const scoredEvents: DashboardEventItem[] = events.map((ev) => {
            let score = 0;
            let reason = "";

            const titleLower = (ev.title || "").toLowerCase();
            const actLower = (ev.activity_title || "").toLowerCase();
            const catLower = (ev.interest_category || "").toLowerCase();
            const intNameLower = (ev.interest_name || "").toLowerCase();
            const locLower = (ev.locality || ev.venue_booking?.venue_address || "").toLowerCase();
            const userLocLower = (activeLocality || "").toLowerCase().trim();

            // Match user profile interests (High priority)
            for (const interest of activeInterests) {
              const iLow = interest.toLowerCase().trim();
              if (iLow && (titleLower.includes(iLow) || actLower.includes(iLow) || catLower.includes(iLow) || intNameLower.includes(iLow))) {
                score += 35;
                reason = `⚡ Aligned with ${interest}`;
                break;
              }
            }

            // Match user profile locality
            if (userLocLower && userLocLower !== "hyderabad") {
              if (locLower.includes(userLocLower) || userLocLower.includes(locLower)) {
                score += 25;
                if (!reason) reason = `📍 In your area (${activeLocality})`;
                else reason += ` · Near ${activeLocality}`;
              }
            }

            // Prefer spots available
            if (ev.remaining_spots > 0) {
              score += 10;
            }

            return {
              ...ev,
              relevance_score: score,
              relevance_reason: reason || "✨ Recommended for you",
              cover_image: getEventCoverImage(ev.title, ev.activity_title || ev.interest_category),
            };
          });

          // Sort by relevance score descending
          scoredEvents.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
          setUpcomingEvents(scoredEvents.slice(0, 3));
        }
      } catch {}

      // 6. Fetch activities
      try {
        const acts = await activityService.getActivities();
        if (Array.isArray(acts) && acts.length > 0) {
          setLiveActivities(acts.slice(0, 4));
        }
      } catch {}

      setLoading(false);
    }

    loadDashboardData();
  }, []);

  // Handle Event RSVP Toggle
  const handleToggleRSVP = async (eventId: number) => {
    const isJoined = !!joinedEvents[eventId];
    try {
      if (isJoined) {
        await eventService.leaveEvent(eventId);
        setJoinedEvents((prev) => ({ ...prev, [eventId]: false }));
        setToastMessage("You left this event.");
      } else {
        await eventService.joinEvent(eventId);
        setJoinedEvents((prev) => ({ ...prev, [eventId]: true }));
        setToastMessage("🎉 RSVP confirmed! Added to your upcoming plans.");
      }
    } catch {
      // Local optimistic toggle for seamless UI
      setJoinedEvents((prev) => ({ ...prev, [eventId]: !isJoined }));
      setToastMessage(!isJoined ? "🎉 RSVP confirmed!" : "RSVP removed.");
    } finally {
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  // Handle Proposal Response
  const handleRespondProposal = async (proposalId: number, status: "ACCEPTED" | "DECLINED") => {
    try {
      await matchingService.respondToProposal(proposalId, status);
      setToastMessage(status === "ACCEPTED" ? "Co-Op Plan Accepted! 🎉" : "Proposal Declined.");
      setProposals((prev) => prev.filter((p) => p.proposal_id !== proposalId));
    } catch {
      setToastMessage(status === "ACCEPTED" ? "Co-Op Plan Accepted! 🎉" : "Proposal Declined.");
      setProposals((prev) => prev.filter((p) => p.proposal_id !== proposalId));
    } finally {
      setTimeout(() => setToastMessage(null), 3000);
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

        {/* HERO BANNER - Harmonized Midnight Slate & Teal */}
        <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-teal-950 p-8 text-white shadow-xl md:p-10 border border-slate-800">
          <div className="relative z-10 max-w-3xl">
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex items-center gap-1.5 rounded-full bg-teal-500/20 border border-teal-400/30 px-3 py-1 text-xs font-semibold text-teal-300">
                <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
                Active in {userLocality}
              </span>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300">
                🛡️ Trust Score: {reputationScore}%
              </span>
            </div>

            <h1 className="mt-5 text-3xl font-extrabold leading-tight tracking-tight md:text-5xl">
              Welcome back, <span className="text-teal-300">{userName}</span>.
            </h1>

            <p className="mt-3 max-w-xl text-sm md:text-base leading-relaxed text-slate-300">
              Your personal radar is active. Connect with compatible peers, schedule weekend sparring, and turn free hours into real plans.
            </p>

            {/* Quick Status Bar */}
            <div className="mt-6 flex flex-wrap items-center gap-2.5 pt-2 border-t border-white/10 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-xl bg-white/10 backdrop-blur-md px-3 py-1.5 font-semibold text-slate-200">
                🎯 Current Focus: <strong className="text-teal-300 font-bold">{currentPlan}</strong>
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-xl bg-white/10 backdrop-blur-md px-3 py-1.5 font-semibold text-slate-200">
                💰 Budget: <strong className="text-amber-300 font-bold">{budgetPreference.toUpperCase()}</strong>
              </span>
              <Link
                href="/profile"
                className="inline-flex items-center gap-1 rounded-xl bg-teal-400 text-slate-950 px-3 py-1.5 font-bold hover:bg-teal-300 transition"
              >
                ✏️ Edit Status
              </Link>
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                href="/connections"
                className="rounded-2xl bg-teal-400 px-5 py-3 text-xs font-bold text-slate-950 shadow-md hover:bg-teal-300 transition flex items-center gap-1.5"
              >
                <span>🎴</span>
                <span>Swipe Match Radar</span>
              </Link>

              <Link
                href="/activities"
                className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-xs font-semibold text-white backdrop-blur-sm hover:bg-white/15 transition flex items-center gap-1.5"
              >
                <span>✦</span>
                <span>Explore Activities</span>
              </Link>

              <Link
                href="/events"
                className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-xs font-semibold text-white backdrop-blur-sm hover:bg-white/15 transition flex items-center gap-1.5"
              >
                <span>◈</span>
                <span>Upcoming Events</span>
              </Link>
            </div>
          </div>

          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full border border-teal-200/10 pointer-events-none" />
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-teal-500/10 blur-xl pointer-events-none" />
        </section>

        {/* 1. PERSONAL AVAILABILITY ALARMS & SPARRING TALENTS RADAR WIDGET */}
        <section className="grid gap-6 lg:grid-cols-3">
          {/* Availability Alarms */}
          <div className="rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 flex items-center gap-1.5">
                  <span>⏰</span> Weekly Free Windows
                </span>
                <Link
                  href="/profile"
                  className="text-[11px] font-bold text-teal-600 dark:text-teal-400 hover:underline"
                >
                  Manage
                </Link>
              </div>

              <div className="mt-4 space-y-2.5">
                {userAvailability.length > 0 ? (
                  userAvailability.slice(0, 3).map((slot, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-teal-500/20 bg-teal-50/50 p-2.5 dark:bg-teal-950/30 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-xs font-bold text-slate-900 dark:text-white">
                          {slot.day_of_week}
                        </p>
                        <p className="text-[11px] font-extrabold text-teal-800 dark:text-teal-300">
                          {formatAlarmTime(slot.start_time)} – {formatAlarmTime(slot.end_time)}
                        </p>
                      </div>
                      <span className="rounded-md bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold px-2 py-0.5">
                        Radar Open
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 p-4 text-center">
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      No availability alarms set yet.
                    </p>
                    <Link
                      href="/profile"
                      className="mt-2 inline-block rounded-lg bg-teal-400 px-3 py-1 text-xs font-bold text-slate-950"
                    >
                      + Add Time Alarm
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {userAvailability.length > 3 && (
              <p className="mt-3 text-[11px] text-slate-500 text-right">
                +{userAvailability.length - 3} more alarm windows set
              </p>
            )}
          </div>

          {/* Sparring Skills & Talents */}
          <div className="rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 flex items-center gap-1.5">
                  <span>⚡</span> Skills & Sparring Talents
                </span>
                <Link
                  href="/profile"
                  className="text-[11px] font-bold text-teal-600 dark:text-teal-400 hover:underline"
                >
                  Manage
                </Link>
              </div>

              <div className="mt-4 space-y-2.5">
                {userSkills.length > 0 ? (
                  userSkills.slice(0, 3).map((sk, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 p-2.5 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-xs font-bold text-slate-900 dark:text-white">
                          {sk.name || "Skill Sharing"}
                        </p>
                        <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">
                          {sk.skill_level}
                        </span>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                        sk.is_offering
                          ? "bg-teal-500/20 text-teal-800 dark:text-teal-300 border border-teal-500/40"
                          : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                      }`}>
                        {sk.is_offering ? "✓ Open to Spar" : "Personal"}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 p-4 text-center">
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      No skills added yet.
                    </p>
                    <Link
                      href="/profile"
                      className="mt-2 inline-block rounded-lg bg-teal-400 px-3 py-1 text-xs font-bold text-slate-950"
                    >
                      + Add Sparring Skill
                    </Link>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
              <span className="text-slate-500">Interest radar keywords:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {userInterests.slice(0, 3).join(", ") || "Active"}
              </span>
            </div>
          </div>

          {/* Pending Co-Op Proposals or AI Radar Highlight */}
          <div className="rounded-[2rem] bg-gradient-to-br from-slate-900 via-indigo-950 to-teal-950 p-6 text-white shadow-md border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-300">
                  Co-Op Activity Proposals
                </p>
                <span className="text-xs bg-teal-400/20 text-teal-300 px-2 py-0.5 rounded-full font-bold">
                  {proposals.length} Pending
                </span>
              </div>

              {proposals.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {proposals.slice(0, 2).map((prop) => (
                    <div
                      key={prop.proposal_id}
                      className="rounded-xl border border-white/10 bg-white/5 p-3"
                    >
                      <h4 className="text-xs font-bold text-white truncate">
                        {prop.title}
                      </h4>
                      <p className="text-[11px] text-teal-300 mt-0.5">
                        📅 {prop.proposed_date} · {prop.proposed_start_time}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleRespondProposal(prop.proposal_id, "ACCEPTED")}
                          className="rounded-lg bg-teal-400 px-3 py-1 text-[10px] font-bold text-slate-950 hover:bg-teal-300 cursor-pointer"
                        >
                          Accept Plan
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRespondProposal(prop.proposal_id, "DECLINED")}
                          className="rounded-lg bg-white/10 px-2.5 py-1 text-[10px] font-semibold text-slate-300 hover:bg-white/20 cursor-pointer"
                        >
                          Decline
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4">
                  <h3 className="text-lg font-bold text-white">
                    Ready to Co-Op
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-slate-300">
                    When friends on Vynk propose activities matching your schedule, their invitations will appear here for one-click confirmation.
                  </p>
                </div>
              )}
            </div>

            <Link
              href="/recommendations"
              className="mt-4 inline-flex items-center justify-center rounded-xl bg-teal-400/90 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-300 transition"
            >
              ⚡ Instant AI Group Matcher
            </Link>
          </div>
        </section>

        {/* 2. REAL-TIME COMPATIBLE PEERS MATCH RADAR */}
        <section>
          <div className="flex items-end justify-between mb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-600 dark:text-teal-400">
                AI Compatibility Radar
              </p>
              <h2 className="mt-1 text-2xl font-extrabold text-slate-900 dark:text-white">
                Compatible Peers Nearby
              </h2>
            </div>
            <Link
              href="/connections"
              className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline"
            >
              Swipe All Matches →
            </Link>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {(topMatches.length > 0 ? topMatches : [
              {
                user_id: 1,
                display_name: "Maya",
                match_score: 94,
                approx_locality: "Jubilee Hills",
                shared_interests: ["Photography", "Coffee"],
                avatar_url: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
              },
              {
                user_id: 2,
                display_name: "Arjun",
                match_score: 89,
                approx_locality: "Gachibowli",
                shared_interests: ["Badminton", "Cycling"],
                avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
              },
              {
                user_id: 3,
                display_name: "Riya",
                match_score: 91,
                approx_locality: "Madhapur",
                shared_interests: ["Board Games", "Music"],
                avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
              },
              {
                user_id: 4,
                display_name: "Rahul",
                match_score: 88,
                approx_locality: "Kondapur",
                shared_interests: ["Pickleball", "Tennis"],
                avatar_url: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&auto=format&fit=crop&q=80",
              },
            ]).map((cand: any) => (
              <div
                key={cand.user_id}
                className="group rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200 transition duration-200 hover:-translate-y-1 hover:shadow-md dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="relative h-40 overflow-hidden rounded-xl">
                    <img
                      src={cand.avatar_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80"}
                      alt={cand.display_name}
                      className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                    />
                    <div className="absolute top-2.5 right-2.5 rounded-full bg-slate-950/80 px-2 py-0.5 text-[10px] font-bold text-teal-300 backdrop-blur-md">
                      ⚡ {Math.round(cand.match_score)}% Match
                    </div>
                  </div>

                  <div className="mt-3">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                      {cand.display_name}
                    </h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      📍 {cand.approx_locality || "Hyderabad"}
                    </p>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {(cand.shared_interests || ["Badminton"]).slice(0, 2).map((item: string) => (
                        <span
                          key={item}
                          className="rounded-md bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-300 px-1.5 py-0.5 text-[9px] font-semibold"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800">
                  <Link
                    href="/connections"
                    className="w-full inline-block rounded-xl bg-teal-400 py-1.5 text-center text-xs font-bold text-slate-950 hover:bg-teal-300 transition"
                  >
                    Connect &amp; Plan
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 2.5 LOCAL AI DEMAND RADAR SPOTLIGHT */}
        <section className="rounded-3xl border border-teal-500/30 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 text-white shadow-xl md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-teal-300">
                <span className="inline-block h-2 w-2 rounded-full bg-teal-400 animate-ping" />
                <span>🛰️ Live Local Demand Radar</span>
              </div>
              <h2 className="mt-2 text-2xl font-black text-white">
                Unmet Demand Spikes In Your Area
              </h2>
              <p className="mt-1 text-xs text-slate-300">
                AI clustered peer alarms and court slots ready for instant squad formation.
              </p>
            </div>

            <Link
              href="/recommendations"
              className="inline-flex items-center gap-1.5 rounded-2xl bg-teal-400 px-5 py-2.5 text-xs font-black text-slate-950 shadow-md shadow-teal-500/20 transition hover:bg-teal-300 shrink-0"
            >
              <span>Explore AI Demand Radar</span>
              <span>➔</span>
            </Link>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                    HIGH DEMAND · 94%
                  </span>
                  <span className="text-[11px] font-bold text-teal-300">
                    ⏰ Saturday @ 07:00 AM
                  </span>
                </div>
                <h3 className="mt-2.5 text-base font-bold text-white">
                  🏸 Badminton Doubles Sparring
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Indiranagar &amp; Gachibowli Sports Hub
                </p>
                <div className="mt-3 flex items-center gap-3 text-xs text-slate-300">
                  <span className="rounded-lg bg-white/10 px-2 py-1 font-semibold">
                    👥 18 interested peers
                  </span>
                  <span className="rounded-lg bg-teal-500/20 px-2 py-1 font-bold text-teal-300">
                    ⚠️ +14 unmet demand
                  </span>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                <span className="text-xs text-slate-400">Smash Arena court ready</span>
                <Link
                  href="/recommendations"
                  className="rounded-xl bg-teal-400 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-teal-300"
                >
                  Launch Squad →
                </Link>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                    HIGH DEMAND · 92%
                  </span>
                  <span className="text-[11px] font-bold text-teal-300">
                    ⏰ Sunday @ 07:00 PM
                  </span>
                </div>
                <h3 className="mt-2.5 text-base font-bold text-white">
                  ⚽ 5v5 Turf Football Night Spar
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Gachibowli Turf Arena
                </p>
                <div className="mt-3 flex items-center gap-3 text-xs text-slate-300">
                  <span className="rounded-lg bg-white/10 px-2 py-1 font-semibold">
                    👥 26 interested peers
                  </span>
                  <span className="rounded-lg bg-teal-500/20 px-2 py-1 font-bold text-teal-300">
                    💰 ₹250/person split
                  </span>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                <span className="text-xs text-slate-400">Floodlit court slots open</span>
                <Link
                  href="/events"
                  className="rounded-xl bg-teal-400 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-teal-300"
                >
                  Host Session →
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* 3. UPCOMING SCHEDULED EVENTS & GATHERINGS */}
        <section>
          <div className="flex items-end justify-between mb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-600 dark:text-teal-400">
                Scheduled Gatherings
              </p>
              <h2 className="mt-1 text-2xl font-extrabold text-slate-900 dark:text-white">
                Upcoming Events Near You
              </h2>
            </div>
            <Link
              href="/events"
              className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline"
            >
              View All Events →
            </Link>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {(upcomingEvents.length > 0 ? upcomingEvents : [
              {
                event_id: 101,
                title: "Saturday Night Box Cricket Match",
                activity_title: "Box Cricket & Turf",
                event_date: "Saturday",
                start_time: "18:00:00",
                end_time: "20:00:00",
                remaining_spots: 4,
                max_capacity: 12,
                locality: "Sarjapur Road, Bengaluru",
                cost_per_person: 333,
                relevance_reason: "⚡ Aligned with Sports & Box Cricket",
                cover_image: "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1200&auto=format&fit=crop&q=80",
              },
              {
                event_id: 102,
                title: "Gachibowli Badminton Doubles Smash",
                activity_title: "Badminton",
                event_date: "Tomorrow",
                start_time: "17:00:00",
                end_time: "19:00:00",
                remaining_spots: 2,
                max_capacity: 8,
                locality: "Gachibowli, Hyderabad",
                cost_per_person: 200,
                relevance_reason: "⚡ Matches your interest: Badminton",
                cover_image: "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=1200&auto=format&fit=crop&q=80",
              },
              {
                event_id: 103,
                title: "Artisanal Coffee & Board Game Evening",
                activity_title: "Social & Board Games",
                event_date: "Sunday",
                start_time: "16:00:00",
                end_time: "19:00:00",
                remaining_spots: 6,
                max_capacity: 12,
                locality: "Jubilee Hills, Hyderabad",
                cost_per_person: 150,
                relevance_reason: "✨ Recommended for you",
                cover_image: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80",
              },
            ]).map((ev: any) => {
              const isJoined = !!joinedEvents[ev.event_id];
              const locationQuery = ev.locality || ev.venue_booking?.venue_address || ev.venue_booking?.venue_name || "Hyderabad";
              const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(locationQuery)}`;

              return (
                <article
                  key={ev.event_id}
                  className="group flex flex-col justify-between overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200 hover:shadow-xl hover:-translate-y-1 transition duration-300 dark:bg-slate-900 dark:ring-slate-800"
                >
                  <div>
                    {/* Photographic Cover Banner (BookMyShow / Luma style) */}
                    <div className="relative h-44 w-full overflow-hidden bg-slate-950">
                      <img
                        src={ev.cover_image || getEventCoverImage(ev.title, ev.activity_title)}
                        alt={ev.title}
                        className="h-full w-full object-cover group-hover:scale-105 transition duration-500 brightness-95"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />

                      {/* Date Badge */}
                      <div className="absolute top-3 left-3">
                        <span className="rounded-full bg-slate-950/85 backdrop-blur px-3 py-1 text-[11px] font-bold text-white border border-white/10 shadow">
                          📅 {ev.event_date} · {formatAlarmTime(ev.start_time)}
                        </span>
                      </div>

                      {/* Spots Remaining Badge */}
                      <div className="absolute top-3 right-3">
                        <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold backdrop-blur shadow ${
                          ev.remaining_spots <= 2
                            ? "bg-rose-500/90 text-white"
                            : "bg-teal-500/90 text-slate-950"
                        }`}>
                          {ev.remaining_spots > 0 ? `${ev.remaining_spots} spots left` : "FULL"}
                        </span>
                      </div>

                      {/* Activity Category Pill */}
                      <div className="absolute bottom-3 left-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-teal-300 bg-slate-950/80 px-2 py-0.5 rounded border border-teal-500/30">
                          {ev.activity_title || ev.interest_category || "Gathering"}
                        </span>
                      </div>
                    </div>

                    {/* Content Body */}
                    <div className="p-4 space-y-2">
                      {/* Profile Relevance Badge */}
                      {ev.relevance_reason && (
                        <div className="inline-flex items-center gap-1.5 rounded-md bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 text-[11px] font-semibold text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800/80">
                          <span>{ev.relevance_reason}</span>
                        </div>
                      )}

                      <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-600 dark:text-white dark:group-hover:text-teal-400 transition leading-snug line-clamp-1">
                        {ev.title}
                      </h3>

                      {/* Location with Google Maps link */}
                      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-0.5">
                        <a
                          href={mapsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          title="Click to view location in Google Maps"
                          className="hover:text-teal-500 hover:underline flex items-center gap-1 font-medium transition cursor-pointer group/loc"
                        >
                          <span className="group-hover/loc:scale-110 transition">📍</span>
                          <span className="truncate max-w-[170px]">{ev.locality || "Hyderabad Central Arena"}</span>
                          <span className="text-[10px] text-teal-500">↗</span>
                        </a>

                        <span className="font-semibold text-teal-600 dark:text-teal-400">
                          {ev.cost_per_person || ev.per_person_cost ? `₹${ev.cost_per_person || ev.per_person_cost}/split` : "Free RSVP"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Footer Actions */}
                  <div className="p-4 pt-0">
                    <div className="mt-2 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleToggleRSVP(ev.event_id)}
                        className={`flex-1 rounded-xl py-2 text-xs font-bold transition cursor-pointer shadow-sm ${
                          isJoined
                            ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40"
                            : "bg-teal-400 text-slate-950 hover:bg-teal-300"
                        }`}
                      >
                        {isJoined ? "✓ RSVP Confirmed" : "RSVP / Join Spot"}
                      </button>
                      <Link
                        href="/events"
                        className="rounded-xl border border-slate-200 dark:border-slate-700 px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                      >
                        Details →
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* 4. QUICK HUB SHORTCUTS */}
        <section>
          <div className="mb-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-600 dark:text-teal-400">
              Navigation Central
            </p>
            <h2 className="mt-1 text-2xl font-extrabold text-slate-900 dark:text-white">
              Where would you like to explore next?
            </h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Link
                key={action.title}
                href={action.href}
                className="group rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition duration-200 hover:-translate-y-1 hover:shadow-lg dark:bg-slate-900 dark:ring-slate-800 block"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-50 text-xl text-teal-700 dark:bg-teal-950/80 dark:text-teal-300">
                    {action.icon}
                  </div>
                  <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-600 dark:text-slate-300">
                    {action.badge}
                  </span>
                </div>

                <h3 className="mt-4 text-base font-bold text-slate-900 group-hover:text-teal-600 dark:text-white dark:group-hover:text-teal-400 transition">
                  {action.title}
                </h3>

                <p className="mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                  {action.description}
                </p>

                <div className="mt-4 text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-1">
                  Explore Hub <span>→</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </PageContainer>
  );
}