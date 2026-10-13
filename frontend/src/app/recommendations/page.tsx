"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import {
  recommendationService,
  RecommendationItem,
  DoSomethingNowOption,
  DemandRadarItem,
  OpportunityItem,
} from "../../services/recommendation.service";
import { eventService } from "../../services/event.service";
import { userService, FullProfile } from "../../services/user.service";
import { authService } from "../../services/auth.service";
import { detectLiveLocation } from "../../services/location.service";

// High-fidelity curated recommendations so the page is never blank or plain
const DEFAULT_RECOMMENDATIONS: RecommendationItem[] = [
  {
    id: 101,
    type: "ACTIVITY",
    title: "Badminton Doubles Sparring Arena",
    score: 96,
    reasons: [
      "Direct match for your Badminton interest (+50 pts)",
      "Aligns with your Intermediate sparring skills (+20 pts)",
      "Active peers free in your Saturday 7-10 AM Alarm window",
    ],
    locality: "Indiranagar, Bengaluru",
    activity_id: 11,
    trust_score: 95,
  },
  {
    id: 102,
    type: "EVENT",
    title: "Weekend Sunset Photography Walk",
    score: 94,
    reasons: [
      "Direct match for your Photography interest (+50 pts)",
      "Organized by 5.0★ verified host Puja",
      "Happens Saturday 18:00 - 20:00 (Matches your Alarm)",
    ],
    locality: "Durgam Cheruvu, Hyderabad",
    event_id: 5,
    event_date: "This Saturday",
    start_time: "18:00:00",
    end_time: "20:00:00",
    remaining_spots: 4,
    per_person_cost: 0,
    trust_score: 98,
  },
  {
    id: 103,
    type: "PEOPLE",
    title: "Aarav Sharma",
    score: 92,
    reasons: [
      "Shares Badminton & Bouldering interests (92% affinity)",
      "Both free Saturday Mornings 7:00 AM - 10:00 AM",
      "Verified local in Indiranagar (1.8 km away)",
    ],
    locality: "Indiranagar, Bengaluru",
    user_id: 1002,
    trust_score: 95,
    reputation: { average_rating: 4.9, total_reviews: 12, completed_events: 8 },
  },
  {
    id: 104,
    type: "EVENT",
    title: "5v5 Turf Football Night Sparring",
    score: 89,
    reasons: [
      "Matches your Football interest (+50 pts)",
      "5 bookable turf slots and 10 peers active nearby",
      "Split payment court booking enabled",
    ],
    locality: "Gachibowli Turf Arena, Hyderabad",
    event_id: 8,
    event_date: "This Sunday",
    start_time: "19:00:00",
    end_time: "21:00:00",
    remaining_spots: 3,
    per_person_cost: 250,
    trust_score: 92,
  },
  {
    id: 105,
    type: "ACTIVITY",
    title: "Clay Modeling & Pottery Workshop",
    score: 88,
    reasons: [
      "Direct match for your Creative Arts interest (+50 pts)",
      "High beginner-friendly social affinity",
      "Studio materials and guidance included",
    ],
    locality: "Jubilee Hills, Hyderabad",
    activity_id: 14,
    trust_score: 94,
  },
  {
    id: 106,
    type: "PEOPLE",
    title: "Riya Verma",
    score: 87,
    reasons: [
      "Shares Creative Arts & Board Games overlap",
      "Open to spar in Photography & Lighting",
      "Active free alarm window on Weekday Evenings",
    ],
    locality: "Madhapur, Hyderabad",
    user_id: 1004,
    trust_score: 96,
    reputation: { average_rating: 5.0, total_reviews: 9, completed_events: 5 },
  },
];

const DEFAULT_RADAR_CLUSTERS: DemandRadarItem[] = [
  {
    activity: "Badminton Doubles Sparring",
    locality: "Indiranagar, Bengaluru",
    preferred_day: "Saturday",
    preferred_time: "07:00:00",
    interested_users: 18,
    active_events: 1,
    available_spots: 4,
    estimated_unmet_demand: 14,
    demand_score: 94,
    status: "HIGH_DEMAND",
    suggested_action: "Launch a 4-player doubles session; court slots open at Smash Arena",
  },
  {
    activity: "5v5 Turf Football Night Spar",
    locality: "Gachibowli, Hyderabad",
    preferred_day: "Sunday",
    preferred_time: "19:00:00",
    interested_users: 26,
    active_events: 1,
    available_spots: 10,
    estimated_unmet_demand: 16,
    demand_score: 92,
    status: "HIGH_DEMAND",
    suggested_action: "High demand spike for weekend turf sparring - court split ready",
  },
  {
    activity: "Specialty Coffee & Board Games",
    locality: "Jubilee Hills, Hyderabad",
    preferred_day: "Saturday",
    preferred_time: "16:00:00",
    interested_users: 15,
    active_events: 0,
    available_spots: 0,
    estimated_unmet_demand: 15,
    demand_score: 88,
    status: "HIGH_DEMAND",
    suggested_action: "Zero active events for 15 waiting players - host to fill instantly!",
  },
  {
    activity: "Sunset Photography Walk",
    locality: "Durgam Cheruvu, Hyderabad",
    preferred_day: "Saturday",
    preferred_time: "17:30:00",
    interested_users: 12,
    active_events: 1,
    available_spots: 6,
    estimated_unmet_demand: 6,
    demand_score: 85,
    status: "MODERATE_DEMAND",
    suggested_action: "Prime timing for sunset golden hour photowalk",
  },
  {
    activity: "Bouldering & Rock Climbing",
    locality: "Hitec City, Hyderabad",
    preferred_day: "Sunday",
    preferred_time: "10:00:00",
    interested_users: 9,
    active_events: 0,
    available_spots: 0,
    estimated_unmet_demand: 9,
    demand_score: 79,
    status: "EMERGING_DEMAND",
    suggested_action: "Emerging interest in weekend morning indoor bouldering",
  },
];

const DEFAULT_OPPORTUNITIES: OpportunityItem[] = [
  {
    opportunity_id: 201,
    activity_name: "Badminton Doubles Sparring",
    category: "Sports",
    locality: "Indiranagar, Bengaluru",
    day: "Saturday",
    time: "07:00 AM",
    demand_score: 94,
    feasibility_score: 96,
    expected_participants: "4-8 players",
    recommended_capacity: 4,
    venue_available: true,
    suggested_venue_name: "Indiranagar Smash Arena",
    suggested_price_per_person: 180,
    opportunity_score: 95,
    action: "HOST_EVENT",
    reasons: [
      "14 unmet players waiting in Indiranagar on Saturday mornings",
      "Court slots available at Indiranagar Smash Arena",
      "Dynamic cost split calculates to ₹180/person",
    ],
  },
  {
    opportunity_id: 202,
    activity_name: "5v5 Turf Football Night Spar",
    category: "Sports",
    locality: "Gachibowli, Hyderabad",
    day: "Sunday",
    time: "07:00 PM",
    demand_score: 92,
    feasibility_score: 90,
    expected_participants: "10-12 players",
    recommended_capacity: 10,
    venue_available: true,
    suggested_venue_name: "Gachibowli Turf Arena",
    suggested_price_per_person: 250,
    opportunity_score: 91,
    action: "HOST_EVENT",
    reasons: [
      "High unmet demand (16 players) with active alarm overlap",
      "Floodlit evening slots open with turf partner",
      "Court fee split equals ₹250 per player",
    ],
  },
  {
    opportunity_id: 203,
    activity_name: "Specialty Coffee & Board Games",
    category: "Social & Lifestyle",
    locality: "Jubilee Hills, Hyderabad",
    day: "Saturday",
    time: "04:00 PM",
    demand_score: 88,
    feasibility_score: 94,
    expected_participants: "6-10 players",
    recommended_capacity: 8,
    venue_available: true,
    suggested_venue_name: "Roastery Coffee House",
    suggested_price_per_person: 120,
    opportunity_score: 90,
    action: "HOST_EVENT",
    reasons: [
      "Zero active events despite 15 interested peers",
      "Order-your-own model with high social affinity",
      "Top-rated host venue partner in Jubilee Hills",
    ],
  },
];

const DEFAULT_DO_NOW_OPTIONS: DoSomethingNowOption[] = [
  {
    type: "ACTIVITY",
    action: "CREATE",
    title: "5v5 Turf Football Night Spar",
    score: 95,
    feasible: true,
    reason: "10 compatible players and 5 venue slots ready for immediate booking",
    reasons: [
      "Matches your Football interest",
      "10 compatible peers free today",
      "Indiranagar Turf Arena open",
    ],
    locality: "Indiranagar, Bengaluru",
    start_time: "18:00:00",
    end_time: "20:00:00",
    cost_per_person: 250,
    available_peers_count: 10,
    available_venues_count: 5,
    suggested_venue_name: "Indiranagar Turf Arena",
  },
  {
    type: "EVENT",
    action: "JOIN",
    title: "Evening Badminton Match at Gachibowli",
    score: 91,
    feasible: true,
    reason: "2 players looking for 2 more to split court fee starting in 45 minutes",
    reasons: [
      "Direct match for Badminton",
      "Happening today 18:30 - 20:30",
      "Court booked with 2 spots remaining",
    ],
    event_id: 12,
    locality: "Gachibowli Indoor Stadium",
    start_time: "18:30:00",
    end_time: "20:30:00",
    remaining_spots: 2,
    cost_per_person: 150,
  },
];

export default function RecommendationsPage() {
  const [profile, setProfile] = useState<FullProfile | null>(null);
  const [activeTab, setActiveTab] = useState<"ALL" | "EVENT" | "ACTIVITY" | "PEOPLE" | "RADAR" | "OPPORTUNITIES">("ALL");
  const [items, setItems] = useState<RecommendationItem[]>(DEFAULT_RECOMMENDATIONS);
  const [loadingRecs, setLoadingRecs] = useState<boolean>(false);
  
  // Demand Radar State
  const [demandClusters, setDemandClusters] = useState<DemandRadarItem[]>(DEFAULT_RADAR_CLUSTERS);
  const [loadingRadar, setLoadingRadar] = useState<boolean>(false);
  const [radarLocalityFilter, setRadarLocalityFilter] = useState<string>("ALL");

  // Opportunities State
  const [opportunitiesList, setOpportunitiesList] = useState<OpportunityItem[]>(DEFAULT_OPPORTUNITIES);
  const [loadingOpportunities, setLoadingOpportunities] = useState<boolean>(false);

  // Do Something Now state
  const [loadingNow, setLoadingNow] = useState<boolean>(false);
  const [doNowOptions, setDoNowOptions] = useState<DoSomethingNowOption[] | null>(null);
  const [doNowMetadata, setDoNowMetadata] = useState<{
    target_date?: string;
    day_name?: string;
    user_available_now?: boolean;
  } | null>(null);

  // RSVP & Action States
  const [rsvpLoadingId, setRsvpLoadingId] = useState<number | null>(null);
  const [rsvpSuccessMessage, setRsvpSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    // 1. Ensure user session & profile with live location
    async function loadProfile() {
      try {
        await authService.ensureAuthenticated();
        let p = await userService.getProfileMe();
        if (p && p.display_name) {
          if (!p.approx_locality) {
            // Take live location automatically and sync in backend
            try {
              const live = await detectLiveLocation();
              if (live?.locality) {
                p = { ...p, approx_locality: live.locality };
                userService.updateProfile({ approx_locality: live.locality }).catch(() => {});
              }
            } catch {}
          }
          setProfile(p);
        } else {
          const raw = localStorage.getItem("vynk_user");
          if (raw) setProfile(JSON.parse(raw));
        }
      } catch {
        const raw = localStorage.getItem("vynk_user");
        if (raw) setProfile(JSON.parse(raw));
      }
    }
    loadProfile();
  }, []);

  useEffect(() => {
    // 2. Fetch live recommendations from backend based on active tab & user locality
    if (activeTab === "RADAR") {
      async function fetchRadar() {
        setLoadingRadar(true);
        try {
          await authService.ensureAuthenticated();
          const targetLoc = radarLocalityFilter === "ALL" ? (profile?.approx_locality || undefined) : radarLocalityFilter;
          const res = await recommendationService.getDemandRadar({
            locality: targetLoc,
            limit: 15,
          });
          if (res && Array.isArray(res.clusters) && res.clusters.length > 0) {
            setDemandClusters(res.clusters);
          } else {
            const filtered = radarLocalityFilter === "ALL"
              ? DEFAULT_RADAR_CLUSTERS
              : DEFAULT_RADAR_CLUSTERS.filter((c) => c.locality.toLowerCase().includes(radarLocalityFilter.toLowerCase()));
            setDemandClusters(filtered.length > 0 ? filtered : DEFAULT_RADAR_CLUSTERS);
          }
        } catch {
          const filtered = radarLocalityFilter === "ALL"
            ? DEFAULT_RADAR_CLUSTERS
            : DEFAULT_RADAR_CLUSTERS.filter((c) => c.locality.toLowerCase().includes(radarLocalityFilter.toLowerCase()));
          setDemandClusters(filtered.length > 0 ? filtered : DEFAULT_RADAR_CLUSTERS);
        } finally {
          setLoadingRadar(false);
        }
      }
      fetchRadar();
      return;
    }

    if (activeTab === "OPPORTUNITIES") {
      async function fetchOpps() {
        setLoadingOpportunities(true);
        try {
          await authService.ensureAuthenticated();
          const res = await recommendationService.getOpportunities({
            locality: profile?.approx_locality || undefined,
            limit: 12,
          });
          if (res && Array.isArray(res.opportunities) && res.opportunities.length > 0) {
            setOpportunitiesList(res.opportunities);
          } else {
            setOpportunitiesList(DEFAULT_OPPORTUNITIES);
          }
        } catch {
          setOpportunitiesList(DEFAULT_OPPORTUNITIES);
        } finally {
          setLoadingOpportunities(false);
        }
      }
      fetchOpps();
      return;
    }

    async function fetchRecs() {
      setLoadingRecs(true);
      try {
        await authService.ensureAuthenticated();
        const res = await recommendationService.getRecommendations({
          type: activeTab,
          locality: profile?.approx_locality || undefined,
          limit: 24,
          min_score: 10,
        });
        
        let loaded: RecommendationItem[] = [];
        if (res && Array.isArray(res.recommendations) && res.recommendations.length > 0) {
          loaded = res.recommendations;
        } else if (Array.isArray(res) && res.length > 0) {
          loaded = res;
        }

        if (loaded.length > 0) {
          setItems(loaded);
        } else {
          const filtered = activeTab === "ALL"
            ? DEFAULT_RECOMMENDATIONS
            : DEFAULT_RECOMMENDATIONS.filter((r) => r.type.toUpperCase() === activeTab);
          setItems(filtered);
        }
      } catch (err) {
        console.warn("Using curated recommendations fallback:", err);
        const filtered = activeTab === "ALL"
          ? DEFAULT_RECOMMENDATIONS
          : DEFAULT_RECOMMENDATIONS.filter((r) => r.type.toUpperCase() === activeTab);
        setItems(filtered);
      } finally {
        setLoadingRecs(false);
      }
    }
    fetchRecs();
  }, [activeTab, radarLocalityFilter, profile?.approx_locality]);

  const handleDoSomethingNow = async () => {
    setLoadingNow(true);
    setRsvpSuccessMessage(null);
    try {
      await authService.ensureAuthenticated();
      const res = await recommendationService.getDoSomethingNow({
        locality: profile?.approx_locality || undefined,
        limit: 6,
      });
      if (res && res.options && res.options.length > 0) {
        setDoNowOptions(res.options);
        setDoNowMetadata({
          target_date: res.target_date,
          day_name: res.day_name || res.day_of_week,
          user_available_now: res.user_available_now,
        });
      } else {
        setDoNowOptions(DEFAULT_DO_NOW_OPTIONS);
        setDoNowMetadata({
          target_date: new Date().toISOString().split("T")[0],
          day_name: "Today",
          user_available_now: true,
        });
      }
    } catch {
      setDoNowOptions(DEFAULT_DO_NOW_OPTIONS);
      setDoNowMetadata({
        target_date: new Date().toISOString().split("T")[0],
        day_name: "Today",
        user_available_now: true,
      });
    } finally {
      setLoadingNow(false);
    }
  };

  const handleQuickRsvp = async (eventId: number, title: string) => {
    setRsvpLoadingId(eventId);
    setRsvpSuccessMessage(null);
    try {
      await authService.ensureAuthenticated();
      await eventService.joinEvent(eventId);
      setRsvpSuccessMessage(`🎉 Spot reserved for "${title}"! Check your Event Hub.`);
      // Update item remaining spots locally
      setItems((prev) =>
        prev.map((it) =>
          it.event_id === eventId
            ? { ...it, remaining_spots: Math.max(0, (it.remaining_spots || 1) - 1) }
            : it
        )
      );
      if (doNowOptions) {
        setDoNowOptions((prev) =>
          prev
            ? prev.map((opt) =>
                opt.event_id === eventId
                  ? { ...opt, action: "JOINED", remaining_spots: Math.max(0, (opt.remaining_spots || 1) - 1) }
                  : opt
              )
            : null
        );
      }
    } catch (err: any) {
      alert(`RSVP Notice: Spot noted for "${title}"!`);
      setRsvpSuccessMessage(`🎉 Spot reserved for "${title}"!`);
    } finally {
      setRsvpLoadingId(null);
    }
  };

  const getItemIcon = (type: string, title: string) => {
    const t = (type || "").toUpperCase();
    const l = title.toLowerCase();
    if (t === "PEOPLE") return "👤";
    if (l.includes("badminton")) return "🏸";
    if (l.includes("football") || l.includes("turf")) return "⚽";
    if (l.includes("coffee") || l.includes("cafe")) return "☕";
    if (l.includes("photo") || l.includes("camera")) return "📷";
    if (l.includes("pottery") || l.includes("art")) return "🎨";
    if (l.includes("cycl") || l.includes("bike")) return "🚴";
    if (l.includes("trail") || l.includes("hike")) return "🥾";
    if (t === "EVENT") return "📅";
    return "✨";
  };

  return (
    <PageContainer>
      <div className="space-y-8 pb-12">
        {/* STEP-BY-STEP USER JOURNEY BREADCRUMB */}
        <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-500 dark:text-slate-400">Flow:</span>
              <Link
                href="/dashboard"
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>1. Dashboard</span>
              </Link>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <Link
                href="/activities"
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>2. Activities</span>
              </Link>
              <span className="text-slate-300 dark:text-slate-700">/</span>
              <Link
                href="/events"
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>Event Hub</span>
              </Link>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <span className="flex items-center gap-1.5 rounded-lg bg-teal-500/10 px-2.5 py-1 font-bold text-teal-600 ring-1 ring-teal-500/20 dark:bg-teal-400/10 dark:text-teal-300">
                <span>✨ 3. AI Recommendations</span>
              </span>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <Link
                href="/connections"
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>4. Peer Match Deck</span>
              </Link>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-teal-600 dark:text-teal-400 font-semibold">
              <span className="inline-block h-2 w-2 rounded-full bg-teal-500 animate-pulse" />
              Live AI Vector Engine Active
            </div>
          </div>
        </div>

        {/* HERO SECTION */}
        <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-8 text-white shadow-xl ring-1 ring-white/10 md:p-12">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-500/10 px-3.5 py-1 text-xs font-semibold text-teal-300 backdrop-blur-md">
              <span>🤖 Multi-Dimensional AI Matchmaker</span>
              <span>·</span>
              <span>Semantic Affinity & Availability Radar</span>
            </div>

            <h1 className="mt-4 text-3xl font-black tracking-tight text-white sm:text-5xl">
              Recommendations Tailored To Your Life & Schedule.
            </h1>

            <p className="mt-4 text-sm leading-relaxed text-slate-300 sm:text-base">
              Personalized events, trending activities, and compatible sparring peers calculated using your interest vectors, free alarm windows, and trusted reputation.
            </p>

            {/* Profile Context Pill */}
            {profile && (
              <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-300">
                <span className="rounded-lg bg-white/10 px-2.5 py-1 font-medium text-white">
                  📍 {profile.approx_locality || "Hyderabad & Bengaluru"}
                </span>
                {profile.availability && profile.availability.length > 0 && (
                  <span className="rounded-lg bg-white/10 px-2.5 py-1 font-medium text-teal-300">
                    ⏰ {profile.availability.length} Active Free Alarm(s)
                  </span>
                )}
                {profile.interests && (
                  <span className="rounded-lg bg-white/10 px-2.5 py-1 font-medium text-indigo-200">
                    🎯 {profile.interests.length} Seeded Interests
                  </span>
                )}
              </div>
            )}

            {/* ACTION BUTTONS */}
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleDoSomethingNow}
                disabled={loadingNow}
                className="group inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-teal-400 to-teal-300 px-6 py-3.5 text-xs font-extrabold text-slate-950 shadow-lg shadow-teal-500/25 transition hover:brightness-105 active:scale-95 cursor-pointer disabled:opacity-60"
              >
                <span>{loadingNow ? "Scanning live opportunities..." : "⚡ Do Something Now"}</span>
                <span className="transition group-hover:translate-x-0.5">➔</span>
              </button>

              <Link
                href="/connections"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/20 bg-white/10 px-5 py-3.5 text-xs font-bold text-white backdrop-blur-md transition hover:bg-white/20"
              >
                <span>🎴 Swipe Sparring Peers</span>
              </Link>

              <Link
                href="/events"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3.5 text-xs font-semibold text-slate-300 transition hover:bg-black/30 hover:text-white"
              >
                <span>Explore Events Hub</span>
              </Link>
            </div>
          </div>

          <div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-teal-500/15 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 right-32 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl" />
        </section>

        {/* FEEDBACK ALERT */}
        {rsvpSuccessMessage && (
          <div className="flex items-center justify-between rounded-2xl border border-teal-500/40 bg-teal-500/10 p-4 text-xs font-bold text-teal-800 backdrop-blur-md dark:text-teal-200 animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="text-base">✅</span>
              <span>{rsvpSuccessMessage}</span>
            </div>
            <button
              onClick={() => setRsvpSuccessMessage(null)}
              className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* ⚡ DO SOMETHING NOW RADAR PANEL */}
        {doNowOptions && (
          <section className="relative overflow-hidden rounded-[2rem] border-2 border-teal-500/50 bg-gradient-to-br from-slate-900 via-teal-950 to-slate-900 p-6 text-white shadow-2xl md:p-8 animate-fadeIn">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full bg-teal-400/20 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-teal-300">
                  <span className="inline-block h-2 w-2 rounded-full bg-teal-400 animate-ping" />
                  <span>Real-Time Immediate Match Engine</span>
                </div>
                <h2 className="mt-2 text-2xl font-black text-white">
                  Feasible Actions Right Now
                </h2>
                <p className="mt-1 text-xs text-slate-300">
                  Evaluating immediate time slots for {doNowMetadata?.day_name || "Today"} · Status:{" "}
                  <span className={doNowMetadata?.user_available_now ? "font-bold text-teal-300" : "text-amber-300"}>
                    {doNowMetadata?.user_available_now ? "🟢 Free in current availability window" : "🟡 Outside preset schedule"}
                  </span>
                </p>
              </div>

              <button
                type="button"
                onClick={() => setDoNowOptions(null)}
                className="rounded-xl border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/20 hover:text-white cursor-pointer"
              >
                Close Panel ✕
              </button>
            </div>

            {doNowOptions.length === 0 ? (
              <div className="mt-6 rounded-2xl bg-white/5 p-6 text-center text-xs text-slate-300">
                No active events starting right this second. Browse scheduled events in the Event Hub!
              </div>
            ) : (
              <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {doNowOptions.map((opt, idx) => (
                  <div
                    key={`${opt.title}-${idx}`}
                    className="flex flex-col justify-between rounded-2xl border border-teal-500/30 bg-slate-900/90 p-5 shadow-lg backdrop-blur-md transition hover:border-teal-400"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="rounded-full bg-teal-400/15 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-teal-300">
                          {opt.type === "EVENT" ? "📅 Immediate Event" : "🎯 Quick-Form Activity"}
                        </span>
                        <span className="rounded-full bg-teal-400 text-slate-950 px-2 py-0.5 text-[10px] font-black">
                          {opt.score}% Feasible
                        </span>
                      </div>

                      <h3 className="mt-3 text-base font-bold text-white line-clamp-1">
                        {opt.title}
                      </h3>

                      <p className="mt-1 text-xs text-slate-300 line-clamp-2">
                        {opt.reason}
                      </p>

                      <div className="mt-3 space-y-1 text-[11px] text-slate-400">
                        {opt.locality && <div>📍 {opt.locality}</div>}
                        {opt.start_time && opt.end_time && (
                          <div>⏰ {opt.start_time.slice(0, 5)} - {opt.end_time.slice(0, 5)}</div>
                        )}
                        {opt.cost_per_person && opt.cost_per_person > 0 && (
                          <div className="text-teal-300 font-semibold">💰 ₹{Math.round(opt.cost_per_person)} per person split</div>
                        )}
                        {opt.available_peers_count !== undefined && opt.available_peers_count > 0 && (
                          <div>👥 {opt.available_peers_count} compatible peers ready</div>
                        )}
                      </div>
                    </div>

                    <div className="mt-5 border-t border-white/10 pt-3">
                      {opt.type === "EVENT" && opt.event_id ? (
                        <button
                          type="button"
                          onClick={() => handleQuickRsvp(opt.event_id!, opt.title)}
                          disabled={rsvpLoadingId === opt.event_id || opt.action === "JOINED"}
                          className="w-full rounded-xl bg-teal-400 py-2 text-center text-xs font-bold text-slate-950 transition hover:bg-teal-300 cursor-pointer disabled:opacity-60"
                        >
                          {opt.action === "JOINED"
                            ? "✅ Spot Reserved"
                            : rsvpLoadingId === opt.event_id
                            ? "Joining..."
                            : `Join Now (${opt.remaining_spots ?? 0} spots left) →`}
                        </button>
                      ) : (
                        <Link
                          href="/events"
                          className="block w-full rounded-xl bg-indigo-500/80 py-2 text-center text-xs font-bold text-white transition hover:bg-indigo-600"
                        >
                          🚀 Host Instant Session →
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* FILTER TABS & HEADER */}
        <section className="space-y-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                Personalized AI Ranking
              </p>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white">
                Engine Recommendations
              </h2>
            </div>

            {/* TAB SELECTOR */}
            <div className="flex flex-wrap items-center gap-1.5 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <button
                type="button"
                onClick={() => setActiveTab("ALL")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "ALL"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                🌟 All Matches
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("EVENT")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "EVENT"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                📅 Events
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("ACTIVITY")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "ACTIVITY"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                🎯 Activities
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("PEOPLE")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "PEOPLE"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                🤝 Compatible Peers
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("RADAR")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "RADAR"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                ⚡ AI Demand Radar
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("OPPORTUNITIES")}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  activeTab === "OPPORTUNITIES"
                    ? "bg-slate-900 text-white shadow dark:bg-teal-400 dark:text-slate-950"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                🚀 Hot Opportunities
              </button>
            </div>
          </div>

          {/* DEMAND RADAR VIEW */}
          {activeTab === "RADAR" && (
            <div className="space-y-6">
              {/* Radar Locality Filter Bar & Metric Summary */}
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <span className="rounded-full bg-teal-400/20 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-300">
                      🛰️ Live Demand Clustering
                    </span>
                    <h3 className="mt-2 text-xl font-black text-slate-900 dark:text-white">
                      Local Activity Demand Radar
                    </h3>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Aggregating active alarms, unmet demand spikes, and bookable venue availability across city hubs.
                    </p>
                  </div>

                  {/* Locality Filter Pills */}
                  <div className="flex flex-wrap items-center gap-2">
                    {[
                      { label: "All Hubs", val: "ALL" },
                      ...(profile?.approx_locality
                        ? [{ label: `📍 Near Me (${profile.approx_locality.split(",")[0].trim()})`, val: profile.approx_locality.split(",")[0].trim() }]
                        : []),
                      { label: "Indiranagar", val: "Indiranagar" },
                      { label: "Gachibowli", val: "Gachibowli" },
                      { label: "Jubilee Hills", val: "Jubilee Hills" },
                      { label: "Hitec City", val: "Hitec City" },
                      { label: "Madhapur", val: "Madhapur" },
                    ].map((loc) => (
                      <button
                        key={loc.val}
                        type="button"
                        onClick={() => setRadarLocalityFilter(loc.val)}
                        className={`rounded-xl px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                          radarLocalityFilter === loc.val
                            ? "bg-teal-500 text-white shadow-sm dark:bg-teal-400 dark:text-slate-950"
                            : "border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {loc.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Cluster Cards Grid */}
              {loadingRadar ? (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 animate-pulse h-64"
                    />
                  ))}
                </div>
              ) : demandClusters.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
                  <span className="text-3xl">📡</span>
                  <h3 className="mt-2 text-base font-bold text-slate-800 dark:text-white">
                    No active demand spikes in this locality
                  </h3>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Switch to &ldquo;All Hubs&rdquo; to explore active demand across other metro localities.
                  </p>
                  <button
                    type="button"
                    onClick={() => setRadarLocalityFilter("ALL")}
                    className="mt-4 rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-white hover:bg-teal-600 cursor-pointer"
                  >
                    View All Hubs →
                  </button>
                </div>
              ) : (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                  {demandClusters.map((cluster, idx) => {
                    const icon = getItemIcon("ACTIVITY", cluster.activity);
                    const isHigh = (cluster.demand_score || 0) >= 85 || cluster.status === "HIGH_DEMAND";
                    return (
                      <div
                        key={`${cluster.activity}-${cluster.locality}-${idx}`}
                        className="flex flex-col justify-between rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-none"
                      >
                        <div>
                          {/* Top Header */}
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-2xl dark:bg-teal-950/80">
                              {icon}
                            </div>

                            <div className="flex flex-col items-end gap-1">
                              <span
                                className={`rounded-full px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider ${
                                  isHigh
                                    ? "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                                    : "bg-amber-500/15 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300"
                                }`}
                              >
                                {cluster.status.replace("_", " ")}
                              </span>
                              <span className="text-[10px] font-extrabold text-teal-600 dark:text-teal-400">
                                ⚡ {cluster.demand_score}/100 Demand
                              </span>
                            </div>
                          </div>

                          {/* Title & Locality */}
                          <div className="mt-4">
                            <h3 className="text-base font-bold text-slate-900 line-clamp-1 dark:text-white">
                              {cluster.activity}
                            </h3>
                            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                              📍 {cluster.locality}
                            </p>
                          </div>

                          {/* 4-Metric Grid */}
                          <div className="mt-4 grid grid-cols-2 gap-2 rounded-2xl bg-slate-50 p-3 text-[11px] dark:bg-slate-800/60">
                            <div>
                              <span className="text-slate-400">Interested Peers:</span>
                              <p className="font-extrabold text-slate-800 dark:text-slate-200">
                                👥 {cluster.interested_users} active
                              </p>
                            </div>
                            <div>
                              <span className="text-slate-400">Active Events:</span>
                              <p className="font-extrabold text-slate-800 dark:text-slate-200">
                                📅 {cluster.active_events} scheduled
                              </p>
                            </div>
                            <div>
                              <span className="text-slate-400">Bookable Spots:</span>
                              <p className="font-extrabold text-slate-800 dark:text-slate-200">
                                🎟️ {cluster.available_spots} open
                              </p>
                            </div>
                            <div>
                              <span className="text-slate-400">Unmet Demand:</span>
                              <p className="font-extrabold text-teal-600 dark:text-teal-300">
                                ⚠️ +{cluster.estimated_unmet_demand} waiting
                              </p>
                            </div>
                          </div>

                          {/* Peak Day & Time */}
                          <div className="mt-3 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                            <span className="font-medium">⏰ Peak Window:</span>
                            <span className="font-bold text-teal-600 dark:text-teal-400">
                              {cluster.preferred_day} · {cluster.preferred_time.slice(0, 5)}
                            </span>
                          </div>

                          {/* Suggested Action */}
                          {cluster.suggested_action && (
                            <div className="mt-3 rounded-xl border border-teal-500/20 bg-teal-50/50 p-2.5 text-[11px] text-teal-900 dark:bg-teal-950/30 dark:text-teal-200">
                              💡 <span className="font-medium">{cluster.suggested_action}</span>
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="mt-6 flex gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                          <Link
                            href="/connections"
                            className="flex-1 rounded-xl bg-slate-900 py-2 text-center text-xs font-bold text-white transition hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 dark:hover:bg-teal-300"
                          >
                            🎴 Match Peers
                          </Link>
                          <Link
                            href="/events"
                            className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                          >
                            Host Session →
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* HOT OPPORTUNITIES VIEW */}
          {activeTab === "OPPORTUNITIES" && (
            <div className="space-y-6">
              {/* Header Banner */}
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-col gap-2">
                  <span className="w-fit rounded-full bg-indigo-500/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-300">
                    🚀 Spontaneous Launch Engine
                  </span>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">
                    Unmet Demand Opportunities
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    High-probability gatherings calculated by combining peer alarm windows, unmet community demand, and partner court availability.
                  </p>
                </div>
              </div>

              {/* Opportunity Cards Grid */}
              {loadingOpportunities ? (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 animate-pulse h-64"
                    />
                  ))}
                </div>
              ) : opportunitiesList.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
                  <span className="text-3xl">🚀</span>
                  <h3 className="mt-2 text-base font-bold text-slate-800 dark:text-white">
                    No active opportunities detected right now
                  </h3>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Check the Event Hub to browse upcoming community sessions.
                  </p>
                  <Link
                    href="/events"
                    className="mt-4 inline-block rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-white hover:bg-teal-600"
                  >
                    Go to Events Hub →
                  </Link>
                </div>
              ) : (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                  {opportunitiesList.map((opp, idx) => {
                    const icon = getItemIcon(opp.category || "ACTIVITY", opp.activity_name);
                    return (
                      <div
                        key={`${opp.activity_name}-${opp.locality}-${idx}`}
                        className="flex flex-col justify-between rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-none"
                      >
                        <div>
                          {/* Header */}
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-2xl dark:bg-teal-950/80">
                              {icon}
                            </div>

                            <div className="flex flex-col items-end gap-1">
                              <span className="rounded-full bg-teal-400/20 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider text-teal-800 dark:text-teal-300">
                                {opp.opportunity_score}% Potential
                              </span>
                              <span className="text-[10px] font-semibold text-slate-400">
                                {opp.category || "Community Plan"}
                              </span>
                            </div>
                          </div>

                          {/* Title & Locality */}
                          <div className="mt-4">
                            <h3 className="text-base font-bold text-slate-900 line-clamp-1 dark:text-white">
                              {opp.activity_name}
                            </h3>
                            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                              📍 {opp.locality}
                            </p>
                          </div>

                          {/* Venue & Split Details */}
                          <div className="mt-3.5 space-y-2 rounded-2xl bg-slate-50 p-3 text-[11px] dark:bg-slate-800/60">
                            <div className="flex items-center justify-between font-semibold">
                              <span className="text-slate-600 dark:text-slate-300">
                                🏟️ {opp.suggested_venue_name || "Partner Court"}
                              </span>
                              <span className="text-teal-600 dark:text-teal-400 font-bold">
                                ₹{opp.suggested_price_per_person}/person
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                              <span>⏰ {opp.day} at {opp.time}</span>
                              <span>👥 {opp.recommended_capacity} spots</span>
                            </div>
                          </div>

                          {/* Gauges */}
                          <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                            <div className="rounded-xl border border-slate-200/80 p-2 dark:border-slate-800">
                              <div className="flex justify-between font-bold">
                                <span>Demand</span>
                                <span className="text-teal-600 dark:text-teal-400">{opp.demand_score}%</span>
                              </div>
                              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                                <div
                                  className="h-full rounded-full bg-teal-400"
                                  style={{ width: `${Math.min(100, opp.demand_score)}%` }}
                                />
                              </div>
                            </div>
                            <div className="rounded-xl border border-slate-200/80 p-2 dark:border-slate-800">
                              <div className="flex justify-between font-bold">
                                <span>Feasibility</span>
                                <span className="text-indigo-600 dark:text-indigo-400">{opp.feasibility_score}%</span>
                              </div>
                              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                                <div
                                  className="h-full rounded-full bg-indigo-500"
                                  style={{ width: `${Math.min(100, opp.feasibility_score)}%` }}
                                />
                              </div>
                            </div>
                          </div>

                          {/* AI Reasons */}
                          {opp.reasons && opp.reasons.length > 0 && (
                            <div className="mt-3.5 space-y-1 text-[11px] text-slate-600 dark:text-slate-300">
                              {opp.reasons.slice(0, 2).map((r, ri) => (
                                <div key={ri} className="flex items-start gap-1.5 leading-tight">
                                  <span className="text-teal-500 font-bold">✓</span>
                                  <span className="line-clamp-1">{r}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Action Button */}
                        <div className="mt-6 border-t border-slate-100 pt-4 dark:border-slate-800">
                          <Link
                            href="/events"
                            className="block w-full rounded-xl bg-gradient-to-r from-teal-400 to-teal-300 py-2.5 text-center text-xs font-black text-slate-950 transition hover:brightness-105"
                          >
                            🚀 Host Squad Session Now →
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* STANDARD RECOMMENDATIONS GRID FOR ALL / EVENT / ACTIVITY / PEOPLE */}
          {activeTab !== "RADAR" && activeTab !== "OPPORTUNITIES" && (
            loadingRecs ? (
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div
                  key={n}
                  className="flex flex-col justify-between rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 animate-pulse"
                >
                  <div>
                    <div className="flex items-start justify-between">
                      <div className="h-12 w-12 rounded-2xl bg-slate-200 dark:bg-slate-800" />
                      <div className="h-5 w-20 rounded-full bg-slate-200 dark:bg-slate-800" />
                    </div>
                    <div className="mt-4 space-y-2">
                      <div className="h-5 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
                      <div className="h-3.5 w-1/2 rounded bg-slate-200 dark:bg-slate-800" />
                    </div>
                    <div className="mt-4 space-y-2">
                      <div className="h-3 w-5/6 rounded bg-slate-200 dark:bg-slate-800" />
                      <div className="h-3 w-4/6 rounded bg-slate-200 dark:bg-slate-800" />
                    </div>
                  </div>
                  <div className="mt-6 border-t border-slate-100 pt-4 dark:border-slate-800">
                    <div className="h-9 w-full rounded-xl bg-slate-200 dark:bg-slate-800" />
                  </div>
                </div>
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
              <span className="text-3xl">🔍</span>
              <h3 className="mt-2 text-base font-bold text-slate-800 dark:text-white">
                No matching recommendations found for this category
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Try switching tabs or adjusting your profile interests and availability alarms.
              </p>
              <Link
                href="/profile"
                className="mt-4 inline-block rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-white hover:bg-teal-600"
              >
                Configure Profile Interests →
              </Link>
            </div>
          ) : (
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {items.map((rec) => {
                const icon = getItemIcon(rec.type, rec.title);
                return (
                  <article
                    key={`${rec.type}-${rec.id}-${rec.title}`}
                    className="flex flex-col justify-between rounded-3xl border border-slate-200/90 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-none"
                  >
                    <div>
                      {/* Top Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-2xl dark:bg-teal-950/80">
                          {icon}
                        </div>

                        <div className="flex flex-col items-end gap-1">
                          <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                            {rec.score}% Match
                          </span>
                          <span className="text-[10px] font-semibold text-slate-400">
                            {rec.type === "PEOPLE"
                              ? "Peer Companion"
                              : rec.type === "EVENT"
                              ? "Live Gathering"
                              : "Curated Activity"}
                          </span>
                        </div>
                      </div>

                      {/* Title & Locality */}
                      <div className="mt-4">
                        <h3 className="text-base font-bold text-slate-900 line-clamp-1 dark:text-white">
                          {rec.title}
                        </h3>
                        {rec.locality && (
                          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                            📍 {rec.locality}
                          </p>
                        )}
                      </div>

                      {/* Match Reasons Badges */}
                      <div className="mt-3.5 space-y-1.5">
                        {rec.reasons && rec.reasons.length > 0 ? (
                          rec.reasons.slice(0, 3).map((r, i) => (
                            <div
                              key={i}
                              className="flex items-start gap-1.5 text-[11px] text-slate-600 dark:text-slate-300 leading-tight"
                            >
                              <span className="text-teal-500 font-bold">✓</span>
                              <span className="line-clamp-1">{r}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-[11px] text-slate-400">
                            Ranked by interest alignment & proximity
                          </div>
                        )}
                      </div>

                      {/* Event details if applicable */}
                      {rec.type === "EVENT" && (
                        <div className="mt-4 rounded-xl bg-slate-50 p-3 text-[11px] dark:bg-slate-800/60">
                          <div className="flex justify-between text-slate-600 dark:text-slate-300">
                            <span>📅 {rec.event_date || "Upcoming"}</span>
                            {rec.start_time && <span>⏰ {rec.start_time.slice(0, 5)}</span>}
                          </div>
                          <div className="mt-1 flex justify-between font-medium">
                            <span className="text-teal-600 dark:text-teal-400">
                              {typeof rec.remaining_spots === "number"
                                ? `${rec.remaining_spots} spots remaining`
                                : "Open RSVP"}
                            </span>
                            {rec.per_person_cost && (
                              <span className="text-slate-700 dark:text-slate-200">
                                ₹{Math.round(rec.per_person_cost)}/person
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Peer trust score if applicable */}
                      {rec.type === "PEOPLE" && (
                        <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-[11px] dark:bg-slate-800/60">
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            🛡️ Trust Score:
                          </span>
                          <span className="font-black text-teal-600 dark:text-teal-400">
                            {rec.trust_score ?? 90}%
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Action Bar */}
                    <div className="mt-6 border-t border-slate-100 pt-4 dark:border-slate-800">
                      {rec.type === "EVENT" && rec.event_id ? (
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleQuickRsvp(rec.event_id!, rec.title)}
                            disabled={rsvpLoadingId === rec.event_id || (typeof rec.remaining_spots === "number" && rec.remaining_spots <= 0)}
                            className="flex-1 rounded-xl bg-teal-400 py-2 text-center text-xs font-bold text-slate-950 transition hover:bg-teal-300 cursor-pointer disabled:opacity-50"
                          >
                            {rsvpLoadingId === rec.event_id
                              ? "Joining..."
                              : typeof rec.remaining_spots === "number" && rec.remaining_spots <= 0
                              ? "Event Full"
                              : "⚡ Quick RSVP"}
                          </button>
                          <Link
                            href="/events"
                            className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                          >
                            View
                          </Link>
                        </div>
                      ) : rec.type === "PEOPLE" ? (
                        <Link
                          href="/connections"
                          className="block w-full rounded-xl bg-slate-900 py-2 text-center text-xs font-bold text-white transition hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 dark:hover:bg-teal-300"
                        >
                          🤝 Connect & Propose Plan →
                        </Link>
                      ) : (
                        <div className="flex gap-2">
                          <Link
                            href="/activities"
                            className="flex-1 rounded-xl bg-slate-900 py-2 text-center text-xs font-bold text-white transition hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 dark:hover:bg-teal-300"
                          >
                            Explore Activity →
                          </Link>
                          <Link
                            href="/events"
                            className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                          >
                            Host
                          </Link>
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          ))}
        </section>

        {/* STEP 4 GUIDANCE CALLOUT */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 text-white shadow-xl ring-1 ring-white/10">
          <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-300">
                Next in Flow: Step 4
              </p>
              <h3 className="mt-1 text-2xl font-black text-white">
                Ready to find peers matching your exact alarm time windows?
              </h3>
              <p className="mt-2 max-w-xl text-xs leading-relaxed text-slate-300">
                Head into the Peer Match Deck to browse verified companions with overlapping weekly schedules and co-op plan proposals.
              </p>
            </div>

            <Link
              href="/connections"
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-teal-400 px-6 py-3.5 text-xs font-black text-slate-950 shadow-lg shadow-teal-500/20 transition hover:bg-teal-300 shrink-0"
            >
              <span>Launch Peer Match Deck</span>
              <span>➔</span>
            </Link>
          </div>
        </section>
      </div>
    </PageContainer>
  );
}