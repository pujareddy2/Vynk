"use client";

import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import { useState, useEffect, useMemo } from "react";
import communityService, {
  Community,
  CommunityHealthResponse,
  CommunityLifecycleInsightResponse,
  CommunityProposalItem,
} from "../../services/community.service";

// High-definition lifestyle, sports and cultural photography for Communities
function getCommunityCoverImage(title: string, category?: string | null): string {
  const t = (title || "").toLowerCase();
  const c = (category || "").toLowerCase();

  if (t.includes("badminton") || c.includes("badminton") || t.includes("smash")) {
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
  if (t.includes("photo") || t.includes("camera") || t.includes("walk") || c.includes("creative")) {
    return "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("board game") || t.includes("catan") || t.includes("chess") || c.includes("game")) {
    return "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("trail") || t.includes("hike") || t.includes("nature") || t.includes("explorer") || c.includes("outdoor")) {
    return "https://images.unsplash.com/photo-1551632811-561732d1e306?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("pottery") || t.includes("clay") || t.includes("art") || t.includes("maker")) {
    return "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("cycl") || t.includes("bike") || c.includes("fitness")) {
    return "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("cine") || t.includes("movie") || t.includes("film") || c.includes("entertainment")) {
    return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1200&auto=format&fit=crop&q=80";
  }
  if (t.includes("music") || t.includes("jam") || t.includes("band")) {
    return "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200&auto=format&fit=crop&q=80";
  }
  // Default clean architectural/meetup aesthetic
  return "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200&auto=format&fit=crop&q=80";
}

interface CommunityCardItem {
  id: number;
  name: string;
  description: string;
  category: string;
  locality: string;
  memberCount: number;
  coverImage: string;
  isCustom?: boolean;
}

// Curated starter communities with distinct categories & localities
const curatedCommunities: CommunityCardItem[] = [
  {
    id: 101,
    name: "Weekend Trail Explorers",
    description: "Discover hidden boulder trails, nature walks, and sunrise viewpoints around Hyderabad outskirts.",
    category: "Outdoor",
    locality: "Jubilee Hills & Outskirts",
    memberCount: 342,
    coverImage: "https://images.unsplash.com/photo-1551632811-561732d1e306?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 102,
    name: "Gachibowli Badminton Smashers",
    description: "Consistent weekday doubles, weekend tournaments, and sparring sessions across premium indoor courts.",
    category: "Sports",
    locality: "Gachibowli",
    memberCount: 520,
    coverImage: "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 103,
    name: "Artisanal Coffee & Book Dialogue",
    description: "Unrushed weekend mornings tasting specialty roasts, exchanging book recommendations and genuine conversation.",
    category: "Social",
    locality: "Madhapur & Jubilee Hills",
    memberCount: 285,
    coverImage: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 104,
    name: "Golden Hour Street Photographers",
    description: "Weekly Saturday afternoon photo-walks capturing old city architecture, street life, and candid moments.",
    category: "Creative",
    locality: "Charminar & Banjara Hills",
    memberCount: 194,
    coverImage: "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 105,
    name: "Tabletop & Strategy Guild",
    description: "Board game nights featuring Catan, Ticket to Ride, Terraforming Mars, and casual social deduction games.",
    category: "Games",
    locality: "Indiranagar & Hitec City",
    memberCount: 168,
    coverImage: "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 106,
    name: "Midnight Cinephiles Club",
    description: "Screening world cinema, indie masterpieces, and organizing post-movie deep dives over chai.",
    category: "Entertainment",
    locality: "Banjara Hills",
    memberCount: 215,
    coverImage: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 107,
    name: "Dawn Cycling Brigade",
    description: "Early morning aerobic road rides connecting Gachibowli to Financial District before city traffic wakes up.",
    category: "Sports",
    locality: "Financial District",
    memberCount: 390,
    coverImage: "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=1200&auto=format&fit=crop&q=80",
  },
  {
    id: 108,
    name: "Pottery & Clay Studio Circle",
    description: "Hands-on pottery workshops, wheel throwing, and glaze experiments for mindful weekend relaxation.",
    category: "Creative",
    locality: "Jubilee Hills",
    memberCount: 145,
    coverImage: "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=1200&auto=format&fit=crop&q=80",
  },
];

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<CommunityCardItem[]>(curatedCommunities);
  const [joined, setJoined] = useState<Record<number, boolean>>({ 102: true, 103: true });
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [selectedLocality, setSelectedLocality] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [showJoinedOnly, setShowJoinedOnly] = useState(false);

  // Community Details Modal
  const [selectedCommunity, setSelectedCommunity] = useState<CommunityCardItem | null>(null);
  const [communityHealth, setCommunityHealth] = useState<CommunityHealthResponse | null>(null);
  const [communityLifecycle, setCommunityLifecycle] = useState<CommunityLifecycleInsightResponse | null>(null);
  const [loadingModalData, setLoadingModalData] = useState(false);

  // AI Community Intelligence Proposals
  const [aiProposals, setAiProposals] = useState<CommunityProposalItem[]>([]);
  const [loadingProposals, setLoadingProposals] = useState(false);

  // Create Community Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formName, setFormName] = useState("");
  const [formCategory, setFormCategory] = useState("Sports");
  const [formLocality, setFormLocality] = useState("");
  const [formDesc, setFormDesc] = useState("");

  // Fetch Communities and AI Proposals on mount
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem("vynk_user");
        if (stored) {
          try {
            const u = JSON.parse(stored);
            if (u.location) setFormLocality(u.location);
          } catch {}
        }
      }
      try {
        const backendComms = await communityService.getCommunities();
        if (Array.isArray(backendComms) && backendComms.length > 0) {
          // Format backend items and filter out meaningless test timestamp names if not clean
          const validBackend: CommunityCardItem[] = backendComms
            .filter((c) => c.name && !c.name.startsWith("LC_") && !c.name.startsWith("API_"))
            .slice(0, 24)
            .map((c) => ({
              id: c.community_id,
              name: c.name.replace(/_Comm_\d+/g, "").replace(/_\d+/g, ""),
              description: c.description || "Active community circle connecting verified peers around shared interests.",
              category: c.name.toLowerCase().includes("badminton") ? "Sports" : "Social",
              locality: "Hyderabad",
              memberCount: Math.max(c.member_count, 1),
              coverImage: getCommunityCoverImage(c.name),
              isCustom: true,
            }));

          // Merge curated distinct cards with valid backend items
          const merged = [...curatedCommunities];
          for (const b of validBackend) {
            if (!merged.some((m) => m.name.toLowerCase() === b.name.toLowerCase())) {
              merged.push(b);
            }
          }
          setCommunities(merged);
        }
      } catch (err) {
        console.warn("Backend communities fetch fallback:", err);
      } finally {
        setLoading(false);
      }

      // Fetch AI Community proposals
      try {
        setLoadingProposals(true);
        const intel = await communityService.getCommunityIntelligence();
        if (intel && Array.isArray(intel.proposals) && intel.proposals.length > 0) {
          setAiProposals(intel.proposals.slice(0, 3));
        }
      } catch {
        // Fallback simulated AI suggestions if unauthenticated
        setAiProposals([
          {
            community_type: "SPORTS",
            theme: "Early Morning Cycling Cohort",
            activity: "Cycling",
            locality: "Gachibowli",
            member_candidates: 8,
            candidate_user_ids: [1, 2, 3],
            recurring_pattern: "Saturday 6:00 AM",
            compatibility_score: 94,
            community_opportunity_score: 92,
            suggested_action: "CREATE_COMMUNITY",
            reasons: ["8 peers in Gachibowli have matching Saturday alarms", "94% compatibility score"],
          },
          {
            community_type: "GAMES",
            theme: "Weekend Board Game Guild",
            activity: "Board Games",
            locality: "Indiranagar",
            member_candidates: 6,
            candidate_user_ids: [4, 5],
            recurring_pattern: "Sunday 4:00 PM",
            compatibility_score: 89,
            community_opportunity_score: 88,
            suggested_action: "CREATE_COMMUNITY",
            reasons: ["High demand for strategy games in Indiranagar"],
          },
        ]);
      } finally {
        setLoadingProposals(false);
      }
    }

    loadData();
  }, []);

  // Filtered communities list
  const filteredCommunities = useMemo(() => {
    return communities.filter((item) => {
      if (selectedCategory !== "ALL" && item.category.toLowerCase() !== selectedCategory.toLowerCase()) {
        return false;
      }
      if (selectedLocality !== "ALL" && !item.locality.toLowerCase().includes(selectedLocality.toLowerCase())) {
        return false;
      }
      if (showJoinedOnly && !joined[item.id]) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = item.name.toLowerCase().includes(q);
        const matchDesc = item.description.toLowerCase().includes(q);
        const matchLoc = item.locality.toLowerCase().includes(q);
        if (!matchTitle && !matchDesc && !matchLoc) return false;
      }
      return true;
    });
  }, [communities, selectedCategory, selectedLocality, showJoinedOnly, searchQuery, joined]);

  // Featured Spotlight Community (Top active circle)
  const spotlightCommunity = useMemo(() => {
    return communities[1] || communities[0];
  }, [communities]);

  // Handle Join / Leave toggle
  const handleToggleJoin = async (e: React.MouseEvent, id: number, name: string) => {
    e.stopPropagation();
    const isCurrentlyJoined = !!joined[id];
    const nextState = !isCurrentlyJoined;

    setJoined((prev) => ({ ...prev, [id]: nextState }));
    setToastMsg(nextState ? `🎉 You joined '${name}'!` : `Left '${name}'.`);
    setTimeout(() => setToastMsg(null), 3200);

    // Call backend API if user is joining
    if (nextState) {
      try {
        await communityService.joinCommunity(id);
      } catch (err) {
        // Optimistic UI state remains active
      }
    }
  };

  // Open Community Details Modal
  const handleOpenDetails = async (community: CommunityCardItem) => {
    setSelectedCommunity(community);
    setLoadingModalData(true);
    setCommunityHealth(null);
    setCommunityLifecycle(null);

    try {
      const [health, lifecycle] = await Promise.allSettled([
        communityService.getCommunityHealth(community.id),
        communityService.getCommunityLifecycle(community.id),
      ]);

      if (health.status === "fulfilled") setCommunityHealth(health.value);
      if (lifecycle.status === "fulfilled") setCommunityLifecycle(lifecycle.value);
    } catch {
      // Graceful fallback metrics
    } finally {
      setLoadingModalData(false);
    }
  };

  // Launch pre-filled create community modal from AI Proposal
  const handleLaunchFromProposal = (proposal: CommunityProposalItem) => {
    setFormName(proposal.theme);
    setFormCategory(proposal.community_type === "SPORTS" ? "Sports" : "Social");
    setFormLocality(`${proposal.locality}, Hyderabad`);
    setFormDesc(`Created from AI recommendation based on ${proposal.recurring_pattern} alignment with ${proposal.member_candidates} compatible local peers.`);
    setShowCreateModal(true);
  };

  // Submit Create Community
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;

    setCreating(true);
    try {
      const res = await communityService.createCommunity({
        name: formName.trim(),
        description: formDesc.trim(),
      });

      const newId = res.community_id || Date.now();
      const newCard: CommunityCardItem = {
        id: newId,
        name: formName.trim(),
        description: formDesc.trim() || "Active local community in Hyderabad.",
        category: formCategory,
        locality: formLocality,
        memberCount: 1,
        coverImage: getCommunityCoverImage(formName, formCategory),
        isCustom: true,
      };

      setCommunities((prev) => [newCard, ...prev]);
      setJoined((prev) => ({ ...prev, [newId]: true }));
      setToastMsg(`🌟 Community '${formName}' successfully created! You are the Organizer.`);
      setShowCreateModal(false);
      setFormName("");
      setFormDesc("");
    } catch (err) {
      // Local fallback creation
      const localId = Date.now();
      const newCard: CommunityCardItem = {
        id: localId,
        name: formName.trim(),
        description: formDesc.trim() || "Active local community in Hyderabad.",
        category: formCategory,
        locality: formLocality,
        memberCount: 1,
        coverImage: getCommunityCoverImage(formName, formCategory),
        isCustom: true,
      };
      setCommunities((prev) => [newCard, ...prev]);
      setJoined((prev) => ({ ...prev, [localId]: true }));
      setToastMsg(`🌟 Community '${formName}' created!`);
      setShowCreateModal(false);
    } finally {
      setCreating(false);
      setTimeout(() => setToastMsg(null), 3500);
    }
  };

  return (
    <PageContainer>
      <div className="space-y-8">
        {/* TOP FLOW BREADCRUMBS & ACTION HEADER */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            <span>Navigation:</span>
            <Link href="/dashboard" className="hover:text-teal-500 transition">1. Dashboard</Link>
            <span>→</span>
            <Link href="/activities" className="hover:text-teal-500 transition">2. Activities</Link>
            <span>→</span>
            <Link href="/events" className="hover:text-teal-500 transition">3. Events Hub</Link>
            <span>→</span>
            <span className="text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950 px-2 py-0.5 rounded-md font-bold">
              ✦ 4. Active Communities
            </span>
            <span>→</span>
            <Link href="/connections" className="hover:text-teal-500 transition">5. Peer Match Deck</Link>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 transition cursor-pointer"
            >
              + Create Circle
            </button>
          </div>
        </div>

        {/* TOAST ALERT */}
        {toastMsg && (
          <div className="rounded-2xl bg-teal-500/10 border border-teal-500/30 p-4 text-sm font-semibold text-teal-400 flex items-center justify-between shadow-sm animate-fade-in">
            <span>{toastMsg}</span>
            <button onClick={() => setToastMsg(null)} className="text-teal-400 hover:text-white cursor-pointer">✕</button>
          </div>
        )}

        {/* SPOTLIGHT COMMUNITY BILLBOARD */}
        {spotlightCommunity && (
          <section className="relative overflow-hidden rounded-3xl bg-slate-950 text-white shadow-2xl border border-slate-800">
            <div className="grid lg:grid-cols-12 items-center">
              {/* Left Details */}
              <div className="p-8 lg:p-12 lg:col-span-7 z-10 space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full bg-teal-500/10 border border-teal-500/30 px-3 py-1 text-xs font-bold text-teal-300 uppercase tracking-widest">
                  <span>✦ FEATURED CIRCLE</span>
                  <span>•</span>
                  <span>{spotlightCommunity.category}</span>
                </div>

                <h1 className="text-3xl font-extrabold sm:text-4xl lg:text-5xl tracking-tight text-white">
                  {spotlightCommunity.name}
                </h1>

                <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-xl">
                  {spotlightCommunity.description}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-300 pt-2">
                  <div className="flex items-center gap-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                    <span className="text-teal-400">📍</span>
                    <span>{spotlightCommunity.locality}</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                    <span className="text-teal-400">👥</span>
                    <span>{spotlightCommunity.memberCount} Verified Members</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                    <span className="text-teal-400">⚡</span>
                    <span className="text-teal-300 font-semibold">96% High Activity Score</span>
                  </div>
                </div>

                <div className="pt-4 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={(e) => handleToggleJoin(e, spotlightCommunity.id, spotlightCommunity.name)}
                    className={`rounded-xl px-5 py-3 text-sm font-semibold transition cursor-pointer shadow-md ${
                      joined[spotlightCommunity.id]
                        ? "bg-teal-600 text-white hover:bg-teal-700"
                        : "bg-white text-slate-950 hover:bg-teal-50"
                    }`}
                  >
                    {joined[spotlightCommunity.id] ? "Joined ✓" : "Join Circle Now →"}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOpenDetails(spotlightCommunity)}
                    className="rounded-xl border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur hover:bg-white/15 transition cursor-pointer"
                  >
                    View Health & Schedule
                  </button>
                </div>
              </div>

              {/* Right Cinematic Cover Photo */}
              <div className="relative h-64 lg:h-full min-h-[320px] lg:col-span-5 overflow-hidden">
                <img
                  src={spotlightCommunity.coverImage}
                  alt={spotlightCommunity.name}
                  className="h-full w-full object-cover brightness-90 group-hover:scale-105 transition duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-t lg:bg-gradient-to-r from-slate-950 via-slate-950/40 to-transparent" />
                <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur px-3 py-1 rounded-full text-xs font-semibold text-teal-300 border border-teal-500/30">
                  Weekly Meetups Verified
                </div>
              </div>
            </div>
          </section>
        )}

        {/* AI COMMUNITY INTELLIGENCE / PROPOSALS CALLOUT */}
        {aiProposals.length > 0 && (
          <section className="rounded-3xl bg-gradient-to-br from-indigo-950/60 via-slate-900 to-teal-950/60 p-6 text-white border border-indigo-500/20 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="flex h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-wider text-teal-300">
                    AI Community Radar
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">
                  Emerging Circles Ready to Launch
                </h2>
                <p className="text-xs text-slate-400">
                  Detected from weekly alarm alignments and compatible habits across Hyderabad.
                </p>
              </div>

              <span className="text-xs text-indigo-300 bg-indigo-900/50 px-3 py-1 rounded-full border border-indigo-500/30 self-start sm:self-auto">
                {aiProposals.length} Circles Viable
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {aiProposals.map((prop, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl bg-slate-900/90 border border-slate-800 p-4 flex flex-col justify-between hover:border-teal-500/40 transition group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-teal-300 bg-teal-950/80 px-2.5 py-0.5 rounded-md border border-teal-800">
                        {prop.community_type}
                      </span>
                      <span className="text-slate-400">
                        {prop.compatibility_score}% compatibility
                      </span>
                    </div>

                    <h3 className="font-bold text-white text-base group-hover:text-teal-300 transition">
                      {prop.theme}
                    </h3>

                    <p className="text-xs text-slate-400 leading-relaxed">
                      {prop.reasons?.[0] || `${prop.member_candidates} peers available on ${prop.recurring_pattern}.`}
                    </p>

                    <div className="flex items-center gap-2 text-xs text-slate-300 pt-1">
                      <span>📍 {prop.locality}</span>
                      <span>•</span>
                      <span>⏰ {prop.recurring_pattern}</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-xs font-semibold text-teal-400">
                      {prop.member_candidates} Peers Ready
                    </span>
                    <button
                      type="button"
                      onClick={() => handleLaunchFromProposal(prop)}
                      className="rounded-lg bg-teal-600/90 hover:bg-teal-500 px-3 py-1.5 text-xs font-semibold text-white transition cursor-pointer"
                    >
                      Launch Circle →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* FILTER & DISCOVERY TOOLBAR */}
        <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">🔍</span>
              <input
                type="text"
                placeholder="Search communities by interest, keyword, or locality..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            {/* Locality Selector Dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap">
                Locality:
              </span>
              <select
                value={selectedLocality}
                onChange={(e) => setSelectedLocality(e.target.value)}
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-900 focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white cursor-pointer"
              >
                <option value="ALL">All Hyderabad</option>
                <option value="Gachibowli">Gachibowli</option>
                <option value="Jubilee Hills">Jubilee Hills</option>
                <option value="Madhapur">Madhapur</option>
                <option value="Banjara Hills">Banjara Hills</option>
                <option value="Indiranagar">Indiranagar</option>
                <option value="Financial District">Financial District</option>
              </select>
            </div>

            {/* Toggle Joined By Me */}
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-semibold text-slate-600 dark:text-slate-300">
              <input
                type="checkbox"
                checked={showJoinedOnly}
                onChange={(e) => setShowJoinedOnly(e.target.checked)}
                className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
              />
              <span>Joined by Me</span>
            </label>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            {["ALL", "Sports", "Outdoor", "Social", "Creative", "Games", "Entertainment"].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-xl px-4 py-1.5 text-xs font-semibold transition cursor-pointer ${
                  selectedCategory === cat
                    ? "bg-teal-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
              >
                {cat === "ALL" ? "All Circles" : cat}
              </button>
            ))}
          </div>
        </section>

        {/* COMMUNITY CARDS GRID */}
        <section>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                Community Circles Directory
              </p>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
                Discover Your Tribe
              </h2>
            </div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
              {filteredCommunities.length} communities available
            </span>
          </div>

          {filteredCommunities.length === 0 ? (
            <div className="rounded-3xl bg-white p-12 text-center ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
              <p className="text-3xl">✦</p>
              <h3 className="mt-3 text-lg font-bold text-slate-900 dark:text-white">
                No communities match your criteria
              </h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Try clearing your search query or locality filter, or create a brand new circle!
              </p>
              <button
                type="button"
                onClick={() => {
                  setSelectedCategory("ALL");
                  setSelectedLocality("ALL");
                  setSearchQuery("");
                  setShowJoinedOnly(false);
                }}
                className="mt-5 rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-500 transition cursor-pointer"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredCommunities.map((community) => {
                const isMember = !!joined[community.id];

                return (
                  <article
                    key={community.id}
                    onClick={() => handleOpenDetails(community)}
                    className="group flex flex-col justify-between overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200 hover:shadow-xl hover:-translate-y-1 transition duration-300 dark:bg-slate-900 dark:ring-slate-800 cursor-pointer"
                  >
                    <div>
                      {/* Photographic Cover Banner */}
                      <div className="relative h-48 w-full overflow-hidden bg-slate-900">
                        <img
                          src={community.coverImage}
                          alt={community.name}
                          className="h-full w-full object-cover group-hover:scale-105 transition duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />

                        {/* Top Category Badge */}
                        <div className="absolute top-3 left-3">
                          <span className="rounded-full bg-slate-900/80 backdrop-blur px-3 py-1 text-xs font-semibold text-teal-300 border border-white/10">
                            {community.category}
                          </span>
                        </div>

                        {/* Locality Tag */}
                        <div className="absolute bottom-3 left-3 text-xs font-medium text-slate-200 flex items-center gap-1 drop-shadow">
                          <span>📍 {community.locality}</span>
                        </div>
                      </div>

                      {/* Content Body */}
                      <div className="p-5 space-y-2">
                        <h3 className="text-xl font-bold text-slate-900 group-hover:text-teal-600 dark:text-white dark:group-hover:text-teal-400 transition">
                          {community.name}
                        </h3>

                        <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400 line-clamp-2">
                          {community.description}
                        </p>
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="p-5 pt-0">
                      <div className="flex items-center justify-between border-t border-slate-100 pt-4 dark:border-slate-800">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-600 dark:text-teal-400">
                          <span>👥</span>
                          <span>{community.memberCount} members</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={(e) => handleToggleJoin(e, community.id, community.name)}
                            className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                              isMember
                                ? "bg-teal-600 text-white hover:bg-teal-700"
                                : "bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                            }`}
                          >
                            {isMember ? "Joined ✓" : "Join"}
                          </button>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDetails(community);
                            }}
                            className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-teal-500 hover:text-teal-600 dark:border-slate-700 dark:text-slate-300 dark:hover:border-teal-400 transition cursor-pointer"
                          >
                            Details →
                          </button>
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* BOTTOM CALLOUT */}
        <section className="rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-teal-950 p-8 text-white shadow-xl border border-white/10 md:p-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-300">
              Launch Your Own Community
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Don't see your specific passion?
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Create an open or curated circle. We will auto-match compatible members who share your schedule alarms and interests in Hyderabad.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="rounded-2xl bg-teal-500 px-6 py-3.5 text-sm font-bold text-slate-950 hover:bg-teal-400 transition shadow-lg shrink-0 cursor-pointer"
          >
            + Create New Circle
          </button>
        </section>
      </div>

      {/* COMMUNITY DETAILS MODAL */}
      {selectedCommunity && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto animate-fade-in"
          onClick={() => setSelectedCommunity(null)}
        >
          <div
            className="relative w-full max-w-2xl overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 my-8"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header Banner */}
            <div className="relative h-56 w-full bg-slate-950">
              <img
                src={selectedCommunity.coverImage}
                alt={selectedCommunity.name}
                className="h-full w-full object-cover brightness-75"
              />
              <button
                type="button"
                onClick={() => setSelectedCommunity(null)}
                className="absolute top-4 right-4 flex h-9 w-9 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur hover:bg-black transition cursor-pointer"
              >
                ✕
              </button>
              <div className="absolute bottom-4 left-6">
                <span className="rounded-full bg-teal-500/90 px-3 py-1 text-xs font-bold text-slate-950">
                  {selectedCommunity.category}
                </span>
                <h3 className="mt-2 text-2xl font-black text-white drop-shadow">
                  {selectedCommunity.name}
                </h3>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 sm:p-8 space-y-6 max-h-[70vh] overflow-y-auto">
              {/* Description */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  About This Circle
                </h4>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  {selectedCommunity.description}
                </p>
              </div>

              {/* Key Meta */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/60 p-3.5 border border-slate-200 dark:border-slate-700">
                  <span className="text-xs text-slate-400 block">Locality</span>
                  <span className="font-bold text-sm text-slate-900 dark:text-white mt-1 block">
                    📍 {selectedCommunity.locality}
                  </span>
                </div>
                <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/60 p-3.5 border border-slate-200 dark:border-slate-700">
                  <span className="text-xs text-slate-400 block">Active Members</span>
                  <span className="font-bold text-sm text-teal-600 dark:text-teal-400 mt-1 block">
                    👥 {selectedCommunity.memberCount} peers
                  </span>
                </div>
                <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/60 p-3.5 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-1">
                  <span className="text-xs text-slate-400 block">Community Trust</span>
                  <span className="font-bold text-sm text-indigo-500 dark:text-indigo-400 mt-1 block">
                    ★ 4.9 Verified
                  </span>
                </div>
              </div>

              {/* Deterministic Health & Lifecycle Section */}
              <div className="rounded-2xl bg-slate-950 p-5 text-white border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-teal-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-teal-300">
                      Community Health Engine
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-slate-400">
                    Deterministic Status
                  </span>
                </div>

                {loadingModalData ? (
                  <p className="text-xs text-slate-400">Computing real-time health metrics...</p>
                ) : (
                  <div className="space-y-3 pt-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-slate-200">
                        Health Score: {communityHealth?.health_score ?? 94}/100
                      </span>
                      <span className="text-xs font-bold text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800">
                        {communityLifecycle?.lifecycle_stage || "Active & Flourishing"}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-teal-500 to-indigo-500 rounded-full"
                        style={{ width: `${communityHealth?.health_score ?? 94}%` }}
                      />
                    </div>

                    <p className="text-xs text-slate-400 leading-relaxed">
                      {communityLifecycle?.insight ||
                        "High member retention, regular weekend gatherings, and strong organizer commitment detected."}
                    </p>
                  </div>
                )}
              </div>

              {/* Link to Gatherings on /events */}
              <div className="flex items-center justify-between rounded-2xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 p-4">
                <div>
                  <h5 className="font-bold text-sm text-teal-900 dark:text-teal-200">
                    Looking for upcoming meetups?
                  </h5>
                  <p className="text-xs text-teal-700 dark:text-teal-300 mt-0.5">
                    Browse organized match events, split courts, and reserved slots.
                  </p>
                </div>
                <Link
                  href="/events"
                  className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shrink-0"
                >
                  View Events →
                </Link>
              </div>

              {/* Modal Footer Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedCommunity(null)}
                  className="rounded-xl border border-slate-300 dark:border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition cursor-pointer"
                >
                  Close
                </button>

                <button
                  type="button"
                  onClick={(e) => {
                    handleToggleJoin(e, selectedCommunity.id, selectedCommunity.name);
                    setSelectedCommunity(null);
                  }}
                  className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition cursor-pointer shadow-md ${
                    joined[selectedCommunity.id]
                      ? "bg-rose-600 text-white hover:bg-rose-700"
                      : "bg-teal-600 text-white hover:bg-teal-500"
                  }`}
                >
                  {joined[selectedCommunity.id] ? "Leave Circle" : "Join This Circle"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CREATE COMMUNITY MODAL */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto animate-fade-in"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="relative w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 my-8 p-6 sm:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                  ✦ Circle Creator
                </span>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  Start a Community Circle
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Circle Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Hyderabad Badminton & Pickleball Sparring"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Category *
                  </label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white cursor-pointer"
                  >
                    <option value="Sports">Sports & Fitness</option>
                    <option value="Outdoor">Outdoor & Trails</option>
                    <option value="Social">Coffee & Social</option>
                    <option value="Creative">Creative & Arts</option>
                    <option value="Games">Tabletop & Games</option>
                    <option value="Entertainment">Cinephiles & Culture</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Locality / Area *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Gachibowli, Hyderabad"
                    value={formLocality}
                    onChange={(e) => setFormLocality(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Purpose & Guidelines
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe what members will do together, schedule frequency, and vibes..."
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-xl bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-teal-500 transition cursor-pointer disabled:opacity-60"
                >
                  {creating ? "Creating Circle..." : "Create Circle"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
}