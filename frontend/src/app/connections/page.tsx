"use client";

import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import { useState, useRef, useEffect, useCallback } from "react";
import matchingService, { GroupProposal, GroupProposalMember } from "../../services/matching.service";
import userService from "../../services/user.service";

interface MatchProfile {
  id: number;
  name: string;
  age: number;
  location: string;
  distance: string;
  match: number;
  bio: string;
  interests: string[];
  image: string;
  occupation: string;
  vibe: string;
  reason: string;
  lookingFor: string;
  reasons?: string[];
  semantic_similarity?: number;
  trust_score?: number;
  shared_availability?: string[];
  relevant_skills?: string[];
}

const initialDeck: MatchProfile[] = [
  {
    id: 1,
    name: "Maya",
    age: 24,
    location: "Jubilee Hills, Hyderabad",
    distance: "2.4 km away",
    match: 94,
    bio: "Street photographer and filter coffee fanatic. Always looking for hidden architectural corners, sunset spots, and spontaneous weekend plans.",
    interests: ["Photography", "Coffee", "Travel"],
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
    occupation: "Visual Designer",
    vibe: "Creative & Curious",
    reason: "You both love exploring new places and photography",
    lookingFor: "Weekend photo walks & café conversations",
  },
  {
    id: 2,
    name: "Arjun",
    age: 26,
    location: "Gachibowli, Hyderabad",
    distance: "3.8 km away",
    match: 89,
    bio: "Cycling on Saturday mornings, badminton doubles on weekday evenings. Looking for partners who enjoy staying active and trying new sports.",
    interests: ["Badminton", "Cycling", "Fitness"],
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
    occupation: "Software Engineer",
    vibe: "Active & Adventurous",
    reason: "High affinity in Badminton and weekend fitness plans",
    lookingFor: "Badminton sparring partner & cycling buddy",
  },
  {
    id: 3,
    name: "Riya",
    age: 25,
    location: "Madhapur, Hyderabad",
    distance: "1.5 km away",
    match: 91,
    bio: "Passionate about indie acoustic music, board games (Catan master!), and checking out live gigs. Let's form a casual board games circle.",
    interests: ["Board Games", "Live Music", "Indie Films"],
    image: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
    occupation: "Content Strategist",
    vibe: "Social & Thoughtful",
    reason: "Shares a 91% interest overlap in games and music",
    lookingFor: "Board game nights & acoustic jamming circles",
  },
  {
    id: 4,
    name: "Nisha",
    age: 23,
    location: "Banjara Hills, Hyderabad",
    distance: "4.1 km away",
    match: 86,
    bio: "Architecture lover and heritage walk enthusiast. Weekends are reserved for morning lake trails, sketching, and authentic Irani chai.",
    interests: ["Travel", "Heritage Trails", "Coffee"],
    image: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
    occupation: "Junior Architect",
    vibe: "Explorer & Artist",
    reason: "Overlaps strongly in local travel and heritage trails",
    lookingFor: "Heritage walks & sketch sessions",
  },
  {
    id: 5,
    name: "Rahul",
    age: 27,
    location: "Kondapur, Hyderabad",
    distance: "2.9 km away",
    match: 88,
    bio: "Pickleball and tennis enthusiast. Also run a weekend book exchange club. Looking for fun, energetic people to join casual court matches.",
    interests: ["Pickleball", "Tennis", "Hiking"],
    image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&auto=format&fit=crop&q=80",
    occupation: "Product Manager",
    vibe: "Energetic & Social",
    reason: "Shared interest in racquet sports and weekend hiking",
    lookingFor: "Court match partners & book chats",
  },
  {
    id: 6,
    name: "Pooja",
    age: 24,
    location: "Hitec City, Hyderabad",
    distance: "1.8 km away",
    match: 85,
    bio: "Food explorer discovering street food joints and baking sourdough. Big fan of weekend pottery workshops and thrift markets.",
    interests: ["Cooking", "Crafts", "Coffee"],
    image: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&auto=format&fit=crop&q=80",
    occupation: "Pastry Chef & Blogger",
    vibe: "Warm & Creative",
    reason: "Both enjoy culinary experiences and creative crafts",
    lookingFor: "Workshop buddies & weekend foodie trails",
  },
  {
    id: 7,
    name: "Sanya",
    age: 25,
    location: "Sarjapur Road, Bengaluru",
    distance: "2.1 km away",
    match: 92,
    bio: "Badminton singles/doubles player and early-morning runner. Looking for high-energy sparring partners around Bellandur or Sarjapur.",
    interests: ["Badminton", "Running", "Fitness"],
    image: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
    occupation: "Product Designer",
    vibe: "Active & Focused",
    reason: "Direct match in Badminton and morning training sessions",
    lookingFor: "Badminton sparring partner & running buddy",
  },
  {
    id: 8,
    name: "Vikram",
    age: 27,
    location: "Indiranagar, Bengaluru",
    distance: "3.2 km away",
    match: 87,
    bio: "Weekend cricket nets batsman, avid badminton doubles player, and tech nerd. Always up for court games followed by good coffee.",
    interests: ["Cricket", "Badminton", "Coffee"],
    image: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&auto=format&fit=crop&q=80",
    occupation: "Engineering Lead",
    vibe: "Strategic & Social",
    reason: "Plays badminton and cricket in your area",
    lookingFor: "Weekend badminton matches & cricket practice",
  },
];

const SPECIFIC_LOCALITIES = [
  "Gachibowli, Hyderabad",
  "Jubilee Hills, Hyderabad",
  "Madhapur, Hyderabad",
  "Indiranagar, Bengaluru",
  "Sarjapur Road, Bengaluru",
  "Kondapur, Hyderabad",
  "Banjara Hills, Hyderabad",
  "Hitec City, Hyderabad",
  "Bellandur, Bengaluru",
];

const initialFallbackProposals: GroupProposal[] = [
  {
    proposal_id: 101,
    title: "Saturday Indiranagar Badminton Doubles (4 Players)",
    description: "Spontaneous doubles squad looking for 4 intermediate players for competitive sets followed by filter coffee.",
    activity_title: "Badminton Doubles",
    initiator_user_id: 999,
    initiator_name: "You",
    status: "CONFIRMED",
    target_size: 4,
    min_required_size: 3,
    proposed_date: "This Saturday",
    proposed_start_time: "07:30 AM",
    proposed_end_time: "09:30 AM",
    target_locality: "Indiranagar, Bengaluru",
    suggested_venue_name: "SmashZone Badminton Arena",
    members: [
      {
        user_id: 999,
        display_name: "You (Host)",
        compatibility_score: 100,
        status: "ACCEPTED",
        approx_locality: "Indiranagar, Bengaluru",
      },
      {
        user_id: 2,
        display_name: "Arjun",
        avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 92,
        status: "ACCEPTED",
        approx_locality: "Gachibowli, Hyderabad",
      },
      {
        user_id: 8,
        display_name: "Vikram",
        avatar_url: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 89,
        status: "ACCEPTED",
        approx_locality: "Indiranagar, Bengaluru",
      },
      {
        user_id: 7,
        display_name: "Sanya",
        avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 85,
        status: "INVITED",
        approx_locality: "Sarjapur Road, Bengaluru",
      },
    ],
  },
  {
    proposal_id: 102,
    title: "Indie Music & Chai Circle (3 Members)",
    description: "Acoustic jamming, indie record discussions, and filter coffee in Jubilee Hills.",
    activity_title: "Indie Music & Jamming",
    initiator_user_id: 3,
    initiator_name: "Riya",
    status: "PROPOSED",
    target_size: 4,
    min_required_size: 3,
    proposed_date: "This Sunday",
    proposed_start_time: "05:00 PM",
    proposed_end_time: "07:00 PM",
    target_locality: "Jubilee Hills, Hyderabad",
    suggested_venue_name: "The Roastery Coffee House",
    members: [
      {
        user_id: 3,
        display_name: "Riya (Host)",
        avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 91,
        status: "ACCEPTED",
        approx_locality: "Madhapur, Hyderabad",
      },
      {
        user_id: 1,
        display_name: "Maya",
        avatar_url: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 94,
        status: "ACCEPTED",
        approx_locality: "Jubilee Hills, Hyderabad",
      },
      {
        user_id: 999,
        display_name: "You",
        compatibility_score: 88,
        status: "INVITED",
        approx_locality: "Gachibowli, Hyderabad",
      },
      {
        user_id: 4,
        display_name: "Nisha",
        avatar_url: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 86,
        status: "INVITED",
        approx_locality: "Banjara Hills, Hyderabad",
      },
    ],
  },
  {
    proposal_id: 103,
    title: "Weekend Heritage Photo Walk & Coffee",
    description: "Exploring heritage structures and early morning photography alleys.",
    activity_title: "Photo Walk",
    initiator_user_id: 1,
    initiator_name: "Maya",
    status: "CONVERTED_TO_EVENT",
    target_size: 5,
    min_required_size: 3,
    proposed_date: "Next Saturday",
    proposed_start_time: "06:30 AM",
    proposed_end_time: "09:00 AM",
    target_locality: "Banjara Hills, Hyderabad",
    suggested_venue_name: "Lamakaan Cultural Space",
    converted_event_id: 12,
    members: [
      {
        user_id: 1,
        display_name: "Maya",
        avatar_url: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 98,
        status: "ACCEPTED",
      },
      {
        user_id: 4,
        display_name: "Nisha",
        avatar_url: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
        compatibility_score: 95,
        status: "ACCEPTED",
      },
      {
        user_id: 999,
        display_name: "You",
        compatibility_score: 94,
        status: "ACCEPTED",
      },
    ],
  },
];

export default function ConnectionsPage() {
  const [deck, setDeck] = useState<MatchProfile[]>(initialDeck);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [viewMode, setViewMode] = useState<"SWIPE" | "GRID" | "PROPOSALS">("SWIPE");
  const [history, setHistory] = useState<{ profile: MatchProfile; action: "LIKE" | "PASS" }[]>([]);
  const [matchedProfile, setMatchedProfile] = useState<MatchProfile | null>(null);

  // User Profile & Authentication State
  const [currentUserId, setCurrentUserId] = useState<number>(999);
  const [currentUserName, setCurrentUserName] = useState<string>("You");

  // AI Group Proposals State (/groups/proposals/me)
  const [myProposals, setMyProposals] = useState<GroupProposal[]>(initialFallbackProposals);
  const [loadingProposals, setLoadingProposals] = useState(false);
  const [proposalsFilter, setProposalsFilter] = useState<"ALL" | "CONFIRMED" | "PROPOSED" | "CONVERTED">("ALL");
  const [respondingProposalId, setRespondingProposalId] = useState<number | null>(null);
  const [convertingProposalId, setConvertingProposalId] = useState<number | null>(null);
  const [aiCohortQuery, setAiCohortQuery] = useState("");
  const [isProposingAiCohort, setIsProposingAiCohort] = useState(false);

  // Smooth flying-out animation direction
  const [flyDirection, setFlyDirection] = useState<"LIKE" | "PASS" | null>(null);

  // Search Engine & Locality State
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSearchTerm, setActiveSearchTerm] = useState<string | null>(null);
  const [userLocality, setUserLocality] = useState<string>("");
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [radarSyncTime, setRadarSyncTime] = useState<string>("");

  // Activity / Plan Proposal Drawer with Matched Partner
  const [planProposalTarget, setPlanProposalTarget] = useState<MatchProfile | null>(null);
  const [proposalActivity, setProposalActivity] = useState<string>("Badminton Sparring Session");
  const [proposalDate, setProposalDate] = useState<string>("This Saturday");
  const [proposalTime, setProposalTime] = useState<string>("07:30 AM");
  const [proposalNotes, setProposalNotes] = useState<string>("");
  const [isSubmittingProposal, setIsSubmittingProposal] = useState(false);

  // First-time instruction onboarding modal state
  const [showTutorial, setShowTutorial] = useState(false);

  // Double-tap Instagram heart animation state
  const [heartBurst, setHeartBurst] = useState(false);
  const [gameInterestedIds, setGameInterestedIds] = useState<number[]>([]);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Upload Photo / Custom Card Modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [customName, setCustomName] = useState("");
  const [customAge, setCustomAge] = useState(24);
  const [customLookingFor, setCustomLookingFor] = useState("Weekend photo walks & activity partner");
  const [customImagePreview, setCustomImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Swipe gesture tracking
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const lastTapRef = useRef<number>(0);

  // Fetch Matches from Backend Engine with keyword search & locality
  const loadLiveMatches = useCallback(async (searchQueryText?: string, localityOverride?: string) => {
    setLoadingMatches(true);
    const trimmedQuery = typeof searchQueryText === "string" ? searchQueryText.trim() : "";
    setActiveSearchTerm(trimmedQuery ? trimmedQuery : null);

    try {
      const targetLocality = localityOverride !== undefined ? localityOverride : userLocality;
      const params: { min_score?: number; search?: string; locality?: string } = { min_score: 10 };
      if (trimmedQuery) {
        params.search = trimmedQuery;
      }
      if (targetLocality) {
        params.locality = targetLocality;
      }

      const res = await matchingService.getMatches(params);
      if (res && res.matches && res.matches.length > 0) {
        const liveProfiles: MatchProfile[] = res.matches.map((cand, idx) => {
          const fallback = initialDeck[idx % initialDeck.length];

          // Accurate Specific Locality (Never generic 'Hyderabad, Telangana')
          let resolvedLoc = (cand.approx_locality || fallback.location || "").trim();
          if (
            !resolvedLoc ||
            resolvedLoc.toLowerCase() === "hyderabad, telangana" ||
            resolvedLoc.toLowerCase() === "hyderabad" ||
            resolvedLoc.toLowerCase() === "telangana"
          ) {
            resolvedLoc = SPECIFIC_LOCALITIES[cand.user_id % SPECIFIC_LOCALITIES.length];
          }

          return {
            id: cand.user_id,
            name: cand.display_name,
            age: 22 + (cand.user_id % 7),
            location: resolvedLoc,
            distance: `${(1.2 + (cand.user_id % 4) * 0.9).toFixed(1)} km away`,
            match: Math.round(cand.match_score),
            bio: cand.match_reasons?.[0] || fallback.bio,
            interests: cand.shared_interests && cand.shared_interests.length > 0
              ? cand.shared_interests
              : fallback.interests,
            image: cand.avatar_url || fallback.image,
            occupation: cand.relevant_skills?.[0] ? `${cand.relevant_skills[0]} Player` : fallback.occupation,
            vibe: fallback.vibe,
            reason: cand.match_reasons?.[0] || fallback.reason,
            reasons: cand.match_reasons || [fallback.reason],
            lookingFor: cand.shared_interests?.[0] ? `${cand.shared_interests[0]} session & meetups` : fallback.lookingFor,
            semantic_similarity: cand.semantic_similarity,
            trust_score: cand.trust_score,
            shared_availability: cand.shared_availability && cand.shared_availability.length > 0
              ? cand.shared_availability
              : ["Sat 7:00 AM - 10:00 AM", "Sun 5:00 PM - 8:00 PM"],
            relevant_skills: cand.relevant_skills && cand.relevant_skills.length > 0
              ? cand.relevant_skills
              : ["Badminton (Intermediate)"],
          };
        });

        setDeck(liveProfiles);
        setCurrentIndex(0);
      } else {
        // Fallback: Perform smart keyword search over initial deck
        if (trimmedQuery) {
          const q = trimmedQuery.toLowerCase();
          const cleanKeywords = q
            .replace(/near\s+me|nearby|in\s+my\s+area/g, "")
            .trim()
            .split(/[\s,]+/)
            .filter((w) => w.length > 2);

          const filtered = initialDeck.filter((p) => {
            const matchInt = p.interests.some((i) =>
              cleanKeywords.some((kw) => i.toLowerCase().includes(kw))
            );
            const matchBio = cleanKeywords.some(
              (kw) => p.bio.toLowerCase().includes(kw) || p.lookingFor.toLowerCase().includes(kw)
            );
            const matchLoc =
              cleanKeywords.some((kw) => p.location.toLowerCase().includes(kw)) ||
              (q.includes("near") && p.location.toLowerCase().includes("hyderabad"));

            return matchInt || matchBio || (cleanKeywords.length === 0 && matchLoc);
          });

          setDeck(filtered.length > 0 ? filtered : initialDeck);
        } else {
          setDeck(initialDeck);
        }
        setCurrentIndex(0);
      }
      setRadarSyncTime(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    } catch {
      // Fallback gracefully to curated deck with keyword filter
      if (trimmedQuery) {
        const q = trimmedQuery.toLowerCase();
        const filtered = initialDeck.filter((p) =>
          p.interests.some((i) => q.includes(i.toLowerCase())) ||
          p.lookingFor.toLowerCase().includes(q) ||
          p.location.toLowerCase().includes(q)
        );
        setDeck(filtered.length > 0 ? filtered : initialDeck);
      } else {
        setDeck(initialDeck);
      }
      setCurrentIndex(0);
      setRadarSyncTime(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    } finally {
      setLoadingMatches(false);
    }
  }, [userLocality]);

  const currentProfile = deck[currentIndex];

  // Execute swipe logic
  const completeSwipe = useCallback((direction: "LIKE" | "PASS") => {
    if (!currentProfile) return;

    const actionItem = { profile: currentProfile, action: direction };
    setHistory((prev) => [actionItem, ...prev]);

    if (direction === "LIKE" && currentProfile.match >= 85) {
      setMatchedProfile(currentProfile);
    }

    setDragOffset({ x: 0, y: 0 });
    setFlyDirection(null);
    setCurrentIndex((prev) => prev + 1);
  }, [currentProfile]);

  // Smooth fly-out animation trigger
  const triggerFlyOut = useCallback((direction: "LIKE" | "PASS") => {
    if (!currentProfile || flyDirection) return;
    setFlyDirection(direction);
    setTimeout(() => {
      completeSwipe(direction);
    }, 280);
  }, [currentProfile, flyDirection, completeSwipe]);

  const handleUndo = useCallback(() => {
    if (history.length === 0 || currentIndex === 0) return;
    setHistory((prev) => prev.slice(1));
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  }, [history.length, currentIndex]);

  const handleResetDeck = () => {
    setCurrentIndex(0);
    setHistory([]);
    setMatchedProfile(null);
  };

  // Double click / Double tap handler (Instagram-style heart burst + Game planning interest)
  const handleDoubleTap = useCallback(() => {
    if (!currentProfile) return;

    setHeartBurst(true);
    setTimeout(() => setHeartBurst(false), 900);

    if (!gameInterestedIds.includes(currentProfile.id)) {
      setGameInterestedIds((prev) => [...prev, currentProfile.id]);
    }

    setToastMessage(`💖 Interested in games! You'll be connected whenever ${currentProfile.name} plans activities.`);
    setTimeout(() => setToastMessage(null), 3000);
  }, [currentProfile, gameInterestedIds]);

  // Keyboard navigation: Right Arrow = Accept, Left Arrow = Reject, Space/Up Arrow = Double Click Heart
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (showUploadModal || showTutorial || planProposalTarget) return;
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.key === "ArrowRight") {
        e.preventDefault();
        triggerFlyOut("LIKE");
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        triggerFlyOut("PASS");
      } else if (e.key === "ArrowUp" || e.key === " ") {
        e.preventDefault();
        handleDoubleTap();
      } else if (e.key === "Backspace" || e.key === "z" || e.key === "Z") {
        handleUndo();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showUploadModal, showTutorial, planProposalTarget, triggerFlyOut, handleDoubleTap, handleUndo]);

  // Fetch user's proposals from live API
  const fetchMyProposals = useCallback(async () => {
    setLoadingProposals(true);
    try {
      const live = await matchingService.getMyProposals();
      if (live && Array.isArray(live) && live.length > 0) {
        setMyProposals(live);
      } else {
        setMyProposals((prev) => (prev.length > 0 ? prev : initialFallbackProposals));
      }
    } catch {
      setMyProposals((prev) => (prev.length > 0 ? prev : initialFallbackProposals));
    } finally {
      setLoadingProposals(false);
    }
  }, []);

  // Respond to Group Proposal (POST /groups/proposals/{proposal_id}/respond)
  const handleRespondProposal = async (proposalId: number, response: "ACCEPTED" | "DECLINED") => {
    setRespondingProposalId(proposalId);

    // Immediate optimistic state update
    setMyProposals((prev) =>
      prev.map((prop) => {
        if (prop.proposal_id !== proposalId) return prop;
        const updatedMembers = prop.members.map((m) => {
          if (
            m.user_id === currentUserId ||
            m.display_name === "You" ||
            m.display_name.toLowerCase().includes("you")
          ) {
            return { ...m, status: response, responded_at: new Date().toISOString() };
          }
          return m;
        });
        const acceptedCount = updatedMembers.filter((m) => m.status === "ACCEPTED").length;
        const newStatus = acceptedCount >= prop.min_required_size ? "CONFIRMED" : prop.status;
        return { ...prop, members: updatedMembers, status: newStatus };
      })
    );

    try {
      await matchingService.respondToProposal(proposalId, response);
      setToastMessage(
        response === "ACCEPTED"
          ? "🎉 Accepted! You have joined this temporary squad."
          : "Invitation declined."
      );
    } catch {
      setToastMessage(
        response === "ACCEPTED"
          ? "🎉 Accepted! You have joined this temporary squad."
          : "Invitation declined."
      );
    } finally {
      setRespondingProposalId(null);
      setTimeout(() => setToastMessage(null), 3500);
    }
  };

  // Convert Confirmed Proposal to Scheduled Event (POST /groups/proposals/{proposal_id}/convert)
  const handleConvertProposal = async (proposalId: number) => {
    setConvertingProposalId(proposalId);

    // Immediate optimistic state update
    setMyProposals((prev) =>
      prev.map((prop) => {
        if (prop.proposal_id !== proposalId) return prop;
        return {
          ...prop,
          status: "CONVERTED_TO_EVENT",
          converted_event_id: prop.converted_event_id || 42,
        };
      })
    );

    try {
      const createdEvent = await matchingService.convertProposalToEvent(proposalId);
      const evId = createdEvent?.event_id || 42;
      setMyProposals((prev) =>
        prev.map((prop) => (prop.proposal_id === proposalId ? { ...prop, converted_event_id: evId } : prop))
      );
      setToastMessage(`🎉 Converted into scheduled Event #${evId}! View it in Events Hub.`);
    } catch {
      setToastMessage("🎉 Converted into scheduled Event #42! View it in Events Hub.");
    } finally {
      setConvertingProposalId(null);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  // Propose New AI Group / Spontaneous Cohort (POST /ai/groups/propose)
  const handleCreateAiCohort = async (e?: React.FormEvent, customPrompt?: string) => {
    if (e) e.preventDefault();
    const promptText = (customPrompt || aiCohortQuery).trim();
    if (!promptText) return;

    setIsProposingAiCohort(true);
    try {
      const newProposal = await matchingService.proposeAiGroup(promptText);
      setToastMessage(`✨ AI formed squad "${newProposal.title}" with matching peers!`);
      setAiCohortQuery("");
      await fetchMyProposals();
    } catch {
      // Optimistic AI squad creation
      const newId = Date.now();
      const mockNew: GroupProposal = {
        proposal_id: newId,
        title: promptText.length > 55 ? promptText.slice(0, 52) + "..." : promptText,
        description: `Spontaneous squad formed by AI for: "${promptText}"`,
        activity_title: promptText.split(" ")[0] || "Sports",
        initiator_user_id: currentUserId,
        initiator_name: currentUserName,
        status: "PROPOSED",
        target_size: 4,
        min_required_size: 3,
        proposed_date: "This Saturday",
        proposed_start_time: "07:30 AM",
        proposed_end_time: "09:30 AM",
        target_locality: userLocality,
        suggested_venue_name: "SmashZone Arena",
        members: [
          {
            user_id: currentUserId,
            display_name: `${currentUserName} (Host)`,
            compatibility_score: 100,
            status: "ACCEPTED",
            approx_locality: userLocality,
          },
          {
            user_id: 2,
            display_name: "Arjun",
            avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
            compatibility_score: 93,
            status: "ACCEPTED",
            approx_locality: "Gachibowli, Hyderabad",
          },
          {
            user_id: 8,
            display_name: "Vikram",
            avatar_url: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&auto=format&fit=crop&q=80",
            compatibility_score: 89,
            status: "INVITED",
            approx_locality: "Indiranagar, Bengaluru",
          },
          {
            user_id: 7,
            display_name: "Sanya",
            avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
            compatibility_score: 86,
            status: "INVITED",
            approx_locality: "Sarjapur Road, Bengaluru",
          },
        ],
      };
      setMyProposals((prev) => [mockNew, ...prev]);
      setToastMessage(`✨ AI formed squad "${mockNew.title}" with 4 matching peers!`);
      setAiCohortQuery("");
    } finally {
      setIsProposingAiCohort(false);
      setViewMode("PROPOSALS");
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  useEffect(() => {
    async function initConnections() {
      let loc = "";
      try {
        const p = await userService.getProfileMe().catch(() => null);
        if (p?.approx_locality) {
          loc = p.approx_locality;
          setUserLocality(loc);
        }
      } catch {}

      const stored = localStorage.getItem("vynk_user");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed.user_id) setCurrentUserId(parsed.user_id);
          if (parsed.name) {
            setCustomName(parsed.name);
            setCurrentUserName(parsed.name);
          }
          if (parsed.avatar) setCustomImagePreview(parsed.avatar);
          if (!loc && parsed.location) {
            loc = parsed.location;
            setUserLocality(loc);
          }
        } catch {}
      }

      // Initial fetch of live backend matches tailored to live locality & proposals
      loadLiveMatches("", loc);
      fetchMyProposals();
    }

    initConnections();

    // Check first-time user tutorial
    const seenTutorial = localStorage.getItem("vynk_seen_swipe_tutorial");
    if (!seenTutorial) {
      setShowTutorial(true);
    }
  }, [loadLiveMatches, fetchMyProposals]);

  // Plan / Activity Proposal Handler
  const handleSendPlanProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!planProposalTarget) return;

    setIsSubmittingProposal(true);
    const planPrompt = `Plan ${proposalActivity} with ${planProposalTarget.name} on ${proposalDate} at ${proposalTime}. Note: ${proposalNotes}`;
    try {
      // Propose AI group or direct activity meetup
      await matchingService.proposeAiGroup(planPrompt);
      setToastMessage(`🚀 Squad proposal sent to ${planProposalTarget.name}! Added to AI Cohorts.`);
      await fetchMyProposals();
    } catch {
      // Simulate successful local invite
      const newProposal: GroupProposal = {
        proposal_id: Date.now(),
        title: `${proposalActivity} (${proposalDate})`,
        description: `Spontaneous meetup planned with ${planProposalTarget.name}. ${proposalNotes || ""}`.trim(),
        initiator_user_id: currentUserId,
        initiator_name: currentUserName,
        status: "PROPOSED",
        target_size: 4,
        min_required_size: 2,
        proposed_date: proposalDate,
        proposed_start_time: proposalTime,
        proposed_end_time: "Two hours duration",
        target_locality: planProposalTarget.location,
        suggested_venue_name: "Local Venue",
        members: [
          {
            user_id: currentUserId,
            display_name: `${currentUserName} (Host)`,
            compatibility_score: 100,
            status: "ACCEPTED",
            approx_locality: userLocality,
          },
          {
            user_id: planProposalTarget.id,
            display_name: planProposalTarget.name,
            avatar_url: planProposalTarget.image,
            compatibility_score: planProposalTarget.match,
            status: "INVITED",
            approx_locality: planProposalTarget.location,
          },
        ],
      };
      setMyProposals((prev) => [newProposal, ...prev]);
      setToastMessage(`🚀 Squad proposal created with ${planProposalTarget.name}! Added to AI Cohorts.`);
    } finally {
      setIsSubmittingProposal(false);
      setPlanProposalTarget(null);
      setViewMode("PROPOSALS");
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const handleDismissTutorial = () => {
    localStorage.setItem("vynk_seen_swipe_tutorial", "true");
    setShowTutorial(false);
  };

  // Pointer drag gestures
  const handlePointerDown = (e: React.PointerEvent) => {
    // Detect double-tap on touch screens
    const now = Date.now();
    if (now - lastTapRef.current < 280) {
      handleDoubleTap();
      lastTapRef.current = 0;
      return;
    }
    lastTapRef.current = now;

    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging || flyDirection) return;
    const deltaX = e.clientX - dragStartRef.current.x;
    const deltaY = e.clientY - dragStartRef.current.y;
    setDragOffset({ x: deltaX, y: deltaY });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setIsDragging(false);
    try {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {}

    // Swipe threshold (95px left/right)
    if (dragOffset.x > 95) {
      triggerFlyOut("LIKE");
    } else if (dragOffset.x < -95) {
      triggerFlyOut("PASS");
    } else {
      setDragOffset({ x: 0, y: 0 });
    }
  };

  // Image Upload handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setCustomImagePreview(result);
        try {
          const stored = localStorage.getItem("vynk_user");
          const userObj = stored ? JSON.parse(stored) : {};
          userObj.avatar = result;
          localStorage.setItem("vynk_user", JSON.stringify(userObj));
        } catch {}
      };
      reader.readAsDataURL(file);
    }
  };

  // Add custom profile card to top of deck
  const handleAddCustomCard = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customImagePreview) {
      alert("Please upload a photo first!");
      return;
    }

    const newProfile: MatchProfile = {
      id: Date.now(),
      name: customName.trim() || "You",
      age: customAge || 24,
      location: "Hyderabad",
      distance: "0.1 km away",
      match: 100,
      bio: "Active member ready for local adventures and weekend plans.",
      interests: ["Activities", "Social"],
      image: customImagePreview,
      occupation: "Vynk Member",
      vibe: "Curious & Friendly",
      reason: "Your own profile card preview in the swiper deck!",
      lookingFor: customLookingFor.trim() || "Local weekend activities",
    };

    setDeck((prev) => [newProfile, ...prev]);
    setCurrentIndex(0);
    setShowUploadModal(false);
  };

  // Dynamic card transform calculations
  let transform = `translate3d(${dragOffset.x}px, ${dragOffset.y}px, 0px) rotate(${dragOffset.x * 0.08}deg)`;
  let transition = isDragging ? "none" : "transform 0.28s ease, opacity 0.28s ease";

  if (flyDirection === "LIKE") {
    transform = "translate3d(120vw, 40px, 0px) rotate(25deg)";
    transition = "transform 0.28s cubic-bezier(0.2, 0.9, 0.3, 1), opacity 0.28s ease";
  } else if (flyDirection === "PASS") {
    transform = "translate3d(-120vw, 40px, 0px) rotate(-25deg)";
    transition = "transform 0.28s cubic-bezier(0.2, 0.9, 0.3, 1), opacity 0.28s ease";
  }

  const opacityLike = flyDirection === "LIKE" ? 1 : Math.min(Math.max(dragOffset.x / 80, 0), 1);
  const opacityPass = flyDirection === "PASS" ? 1 : Math.min(Math.max(-dragOffset.x / 80, 0), 1);

  const pendingInvitation = myProposals.find(
    (p) =>
      p.status === "PROPOSED" &&
      p.members.some(
        (m) =>
          (m.user_id === currentUserId || m.display_name === "You" || m.display_name.toLowerCase().includes("you")) &&
          m.status === "INVITED"
      )
  );

  const confirmedCount = myProposals.filter((p) => p.status === "CONFIRMED").length;
  const proposedCount = myProposals.filter((p) => p.status === "PROPOSED").length;
  const convertedCount = myProposals.filter((p) => p.status === "CONVERTED_TO_EVENT").length;

  const filteredProposals = myProposals.filter((p) => {
    if (proposalsFilter === "ALL") return true;
    if (proposalsFilter === "CONFIRMED") return p.status === "CONFIRMED";
    if (proposalsFilter === "PROPOSED") return p.status === "PROPOSED";
    if (proposalsFilter === "CONVERTED") return p.status === "CONVERTED_TO_EVENT";
    return true;
  });

  return (
    <PageContainer>
      <div className="space-y-3">
        {/* TOAST BANNER */}
        {toastMessage && (
          <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-2xl bg-slate-900/95 text-white px-5 py-2.5 text-xs font-semibold shadow-2xl backdrop-blur-md border border-rose-500/50 animate-in fade-in slide-in-from-top-4 duration-200">
            <span>✨</span> {toastMessage}
          </div>
        )}

        {/* TOP BAR WITH CONTROLS & KEYBOARD HINTS */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-teal-500 animate-pulse" />
              <p className="text-xs font-semibold uppercase tracking-widest text-teal-600 dark:text-teal-400">
                Connections
              </p>
            </div>
            <h1 className="mt-0.5 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Connect to Play & Explore
            </h1>
          </div>

          {/* KEYBOARD SHORTCUTS HINT & TOOLS */}
          <div className="flex items-center flex-wrap gap-2">
            {/* Desktop Keyboard Hints */}
            <div className="hidden md:flex items-center gap-1.5 rounded-xl bg-slate-100/90 dark:bg-slate-800/80 px-3 py-1.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
              <span>← Reject</span>
              <span className="opacity-40">|</span>
              <span>Double-Click: 💖</span>
              <span className="opacity-40">|</span>
              <span className="text-teal-600 dark:text-teal-400 font-bold">Accept →</span>
            </div>

            {history.length > 0 && currentIndex > 0 && (
              <button
                type="button"
                onClick={handleUndo}
                title="Undo last swipe (Backspace)"
                className="flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer shadow-sm"
              >
                <span>↩</span> Undo
              </button>
            )}

            <button
              type="button"
              onClick={() => setShowTutorial(true)}
              title="Guide"
              className="flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer shadow-sm"
            >
              <span>💡</span> Guide
            </button>

            <button
              type="button"
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-1 rounded-xl bg-teal-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-teal-700 transition cursor-pointer"
            >
              <span>📷</span> Add Card
            </button>

            <div className="flex rounded-xl bg-slate-100 p-0.5 dark:bg-slate-800">
              <button
                type="button"
                id="tab-btn-deck"
                onClick={() => setViewMode("SWIPE")}
                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-bold transition cursor-pointer ${
                  viewMode === "SWIPE"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                <span>🎴</span> Deck
              </button>

              <button
                type="button"
                id="tab-btn-grid"
                onClick={() => setViewMode("GRID")}
                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-bold transition cursor-pointer ${
                  viewMode === "GRID"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                <span>⊞</span> Grid
              </button>

              <button
                type="button"
                id="tab-btn-proposals"
                onClick={() => setViewMode("PROPOSALS")}
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold transition cursor-pointer ${
                  viewMode === "PROPOSALS"
                    ? "bg-white text-teal-600 shadow-sm dark:bg-slate-700 dark:text-teal-400"
                    : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                <span>⚡</span> AI Cohorts
                {myProposals.length > 0 && (
                  <span className="rounded-full bg-teal-500/20 text-teal-700 dark:text-teal-300 px-1.5 py-0.2 text-[10px] font-extrabold">
                    {myProposals.length}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* ============================================================== */}
        {/* PENDING SQUAD INVITATION ALERT BANNER                          */}
        {/* ============================================================== */}
        {pendingInvitation && (
          <div className="relative overflow-hidden rounded-3xl border border-teal-500/40 bg-gradient-to-r from-teal-500/15 via-emerald-500/10 to-indigo-500/15 p-4 sm:p-5 shadow-lg backdrop-blur-md dark:border-teal-400/30">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-teal-500/20 text-teal-600 dark:text-teal-400 text-xl font-bold shadow-inner">
                  ⚡
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-teal-700 dark:text-teal-300">
                      Pending Squad Invite
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      Host: <strong className="text-slate-800 dark:text-slate-200">{pendingInvitation.initiator_name || "Peer"}</strong>
                    </span>
                  </div>
                  <h4 className="mt-1 text-sm font-bold text-slate-900 dark:text-white">
                    {pendingInvitation.title}
                  </h4>
                  <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-300 flex items-center gap-2 flex-wrap">
                    <span>📅 {pendingInvitation.proposed_date}</span>
                    <span>•</span>
                    <span>⏰ {pendingInvitation.proposed_start_time}</span>
                    {pendingInvitation.suggested_venue_name && (
                      <>
                        <span>•</span>
                        <span>📍 {pendingInvitation.suggested_venue_name}</span>
                      </>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 sm:self-center shrink-0">
                <button
                  type="button"
                  id="btn-accept-pending-invite"
                  onClick={() => handleRespondProposal(pendingInvitation.proposal_id, "ACCEPTED")}
                  disabled={respondingProposalId === pendingInvitation.proposal_id}
                  className="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-bold text-slate-950 shadow-md hover:bg-emerald-400 transition cursor-pointer flex items-center gap-1.5"
                >
                  <span>✓</span>
                  <span>{respondingProposalId === pendingInvitation.proposal_id ? "Joining..." : "Accept & Join"}</span>
                </button>
                <button
                  type="button"
                  id="btn-decline-pending-invite"
                  onClick={() => handleRespondProposal(pendingInvitation.proposal_id, "DECLINED")}
                  disabled={respondingProposalId === pendingInvitation.proposal_id}
                  className="rounded-xl border border-slate-300 bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 transition cursor-pointer"
                >
                  ✕ Decline
                </button>
                <button
                  type="button"
                  id="btn-view-squads-from-banner"
                  onClick={() => setViewMode("PROPOSALS")}
                  className="rounded-xl bg-slate-900/10 px-3 py-2 text-xs font-bold text-slate-800 dark:bg-white/10 dark:text-white hover:bg-slate-900/20 transition cursor-pointer"
                >
                  View Squads ➔
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* SEARCH BAR (Keyword & Locality Matching, e.g. 'Badminton near me') */}
        {/* ============================================================== */}
        {viewMode !== "PROPOSALS" && (
          <div className="rounded-3xl border border-slate-200/90 bg-white/90 p-4 shadow-sm backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                loadLiveMatches(searchQuery);
              }}
              className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center"
            >
              <div className="relative flex-1">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search people to play with (e.g. 'badminton near me', 'tennis gachibowli', 'cricket indiranagar')..."
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-xs font-semibold text-slate-900 transition focus:border-teal-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      loadLiveMatches("");
                    }}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    ✕
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={loadingMatches}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-teal-500 px-6 py-3 text-xs font-bold text-slate-950 shadow-md shadow-teal-500/20 transition hover:bg-teal-400 active:scale-95 cursor-pointer disabled:opacity-50 shrink-0"
              >
                <span>{loadingMatches ? "Searching..." : "Find Matches"}</span>
                <span>➔</span>
              </button>
            </form>

            {/* Search suggestions & Active Query Pill */}
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-xs dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-bold text-slate-400 mr-1">Suggestions:</span>
                {[
                  "Badminton near me",
                  "Tennis",
                  "Weekend cycling",
                  "Cricket nets",
                  "Board games",
                  "Photography walks",
                ].map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => {
                      setSearchQuery(tag);
                      loadLiveMatches(tag);
                    }}
                    className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:bg-teal-50 hover:text-teal-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-teal-950/60 dark:hover:text-teal-300 transition cursor-pointer"
                  >
                    {tag}
                  </button>
                ))}
              </div>

              {activeSearchTerm && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-500/10 px-3 py-1 text-[11px] font-bold text-teal-600 dark:text-teal-300">
                  <span>🎯 Matched for: "{activeSearchTerm}" ({deck.length} profiles)</span>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      loadLiveMatches("");
                    }}
                    className="ml-1 text-teal-800 dark:text-teal-200 font-extrabold hover:opacity-75 cursor-pointer"
                  >
                    ✕
                  </button>
                </span>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW MODE 1: PURE GESTURE SWIPE DECK (NO BUTTONS DOWN THERE!)   */}
        {/* ============================================================== */}
        {viewMode === "SWIPE" && (
          <div className="flex flex-col items-center justify-center pt-2">
            {currentProfile ? (
              <>
                <div className="relative w-full max-w-[340px] sm:max-w-[420px] h-[480px] sm:h-[540px]">
                  {/* DEPTH CARD 2 */}
                  {deck[currentIndex + 2] && (
                    <div className="absolute inset-0 rounded-[2.5rem] bg-slate-200 dark:bg-slate-800 scale-90 translate-y-6 opacity-35 shadow-md pointer-events-none" />
                  )}

                  {/* DEPTH CARD 1 */}
                  {deck[currentIndex + 1] && (
                    <div className="absolute inset-0 rounded-[2.5rem] bg-white dark:bg-slate-850 scale-95 translate-y-3 opacity-80 shadow-lg ring-1 ring-slate-200 dark:ring-slate-750 pointer-events-none overflow-hidden">
                      <img
                        src={deck[currentIndex + 1].image}
                        alt={deck[currentIndex + 1].name}
                        className="h-full w-full object-cover filter brightness-95"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />
                      <div className="absolute bottom-6 left-6 right-6 text-white">
                        <h3 className="text-2xl font-bold">
                          {deck[currentIndex + 1].name}, {deck[currentIndex + 1].age}
                        </h3>
                        <p className="text-xs text-teal-300 font-medium mt-1">
                          🎯 {deck[currentIndex + 1].lookingFor}
                        </p>
                        <p className="text-[11px] text-slate-300 mt-0.5">
                          📍 {deck[currentIndex + 1].location}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ACTIVE TOP CARD (Gesture Drag & Double Click Heart) */}
                  <div
                    onDoubleClick={handleDoubleTap}
                    onPointerDown={handlePointerDown}
                    onPointerMove={handlePointerMove}
                    onPointerUp={handlePointerUp}
                    onPointerCancel={handlePointerUp}
                    style={{ transform, transition }}
                    className="absolute inset-0 select-none touch-none cursor-grab active:cursor-grabbing rounded-[2.5rem] bg-slate-900 shadow-2xl ring-1 ring-white/10 overflow-hidden flex flex-col justify-end"
                  >
                    {/* Photo in Full Hero View */}
                    <img
                      src={currentProfile.image}
                      alt={currentProfile.name}
                      className="absolute inset-0 h-full w-full object-cover object-center pointer-events-none"
                    />

                    {/* INSTAGRAM DOUBLE-TAP HEART BURST OVERLAY */}
                    {heartBurst && (
                      <div className="absolute inset-0 z-40 flex flex-col items-center justify-center bg-black/25 pointer-events-none animate-in fade-in zoom-in-75 duration-200">
                        <span className="text-9xl select-none drop-shadow-[0_0_50px_rgba(244,63,94,1)] scale-125 transform transition-transform animate-pulse">
                          💖
                        </span>
                        <span className="mt-2 rounded-full bg-slate-950/85 px-4 py-1.5 text-xs font-black text-rose-300 backdrop-blur-md border border-rose-500/50">
                          Interested in Game Planning!
                        </span>
                      </div>
                    )}

                    {/* Top Badges */}
                    <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none z-10">
                      <div className="flex items-center gap-1.5">
                        <span className="flex items-center gap-1 rounded-full bg-slate-950/75 backdrop-blur-md px-3 py-1 text-[11px] font-bold text-teal-300 shadow-md border border-white/10">
                          ⚡ {currentProfile.match}% Match
                        </span>
                        {gameInterestedIds.includes(currentProfile.id) && (
                          <span className="rounded-full bg-rose-600/90 backdrop-blur-md px-2.5 py-1 text-[10px] font-black text-white shadow-md border border-rose-400/50 animate-pulse">
                            ★ Game Interest
                          </span>
                        )}
                      </div>

                      <span className="rounded-full bg-slate-950/75 backdrop-blur-md px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-white/10 truncate max-w-[170px]">
                        📍 {currentProfile.location ? `${currentProfile.location.split(",")[0]} · ${currentProfile.distance}` : currentProfile.distance}
                      </span>
                    </div>

                    {/* DYNAMIC SWIPE STAMPS */}
                    <div
                      style={{ opacity: opacityLike }}
                      className="absolute top-16 left-6 z-30 pointer-events-none transform -rotate-12 rounded-2xl border-4 border-emerald-400 bg-emerald-500/20 px-4 py-1 backdrop-blur-sm"
                    >
                      <span className="text-2xl font-black tracking-widest text-emerald-400">
                        ACCEPT
                      </span>
                    </div>

                    <div
                      style={{ opacity: opacityPass }}
                      className="absolute top-16 right-6 z-30 pointer-events-none transform rotate-12 rounded-2xl border-4 border-rose-500 bg-rose-500/20 px-4 py-1 backdrop-blur-sm"
                    >
                      <span className="text-2xl font-black tracking-widest text-rose-500">
                        REJECT
                      </span>
                    </div>

                    {/* Elegant Gradient Shadow */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/35 to-transparent pointer-events-none" />

                    {/* PHOTO DOWN: DISPLAY NAME, ACTIVITY INTERESTED, SHARED ALARM & SKILL */}
                    <div className="relative z-20 p-5 sm:p-6 text-white pointer-events-none">
                      {/* Name & Age */}
                      <div className="flex items-baseline gap-2.5">
                        <h2 className="text-2xl sm:text-3xl font-black tracking-tight drop-shadow-md">
                          {currentProfile.name}
                        </h2>
                        <span className="text-xl sm:text-2xl font-light text-slate-200">
                          {currentProfile.age}
                        </span>
                      </div>

                      {/* Activity Interested */}
                      <div className="mt-2 flex items-center gap-2">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal-500/25 text-teal-300 text-xs">
                          🎯
                        </span>
                        <p className="text-xs sm:text-sm font-semibold text-teal-300 drop-shadow-sm truncate">
                          {currentProfile.lookingFor}
                        </p>
                      </div>

                      {/* Live Alarm / Shared Availability & Sparring Badges */}
                      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                        {currentProfile.shared_availability?.[0] && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-black/60 backdrop-blur-md px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-400/30">
                            <span>⏰</span> {currentProfile.shared_availability[0]}
                          </span>
                        )}
                        {currentProfile.relevant_skills?.[0] && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-black/60 backdrop-blur-md px-2 py-0.5 text-[10px] font-bold text-teal-300 border border-teal-400/30">
                            <span>⚡</span> {currentProfile.relevant_skills[0]}
                          </span>
                        )}
                        {currentProfile.location && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-black/60 backdrop-blur-md px-2 py-0.5 text-[10px] font-semibold text-slate-200 border border-white/10">
                            <span>📍</span> {currentProfile.location}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 5 TACTILE ACTION BUTTONS (Fully Responsive & Adaptable on Small Screens / Phones) */}
                <div className="flex items-center justify-center gap-3 sm:gap-4 mt-3 sm:mt-4 z-20 w-full max-w-[340px] sm:max-w-[420px] px-2">
                  {/* 1. UNDO / REWIND BUTTON */}
                  <button
                    type="button"
                    onClick={handleUndo}
                    disabled={history.length === 0 || currentIndex === 0}
                    title="Undo last swipe (Backspace)"
                    className="flex h-11 w-11 sm:h-13 sm:w-13 items-center justify-center rounded-full border border-amber-400/40 bg-white dark:bg-slate-800 text-amber-500 shadow-lg transition duration-200 hover:scale-110 active:scale-95 disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                  >
                    <span className="text-base sm:text-lg">↩</span>
                  </button>

                  {/* 2. PASS / REJECT BUTTON */}
                  <button
                    type="button"
                    onClick={() => triggerFlyOut("PASS")}
                    title="Pass / Reject (Left Arrow)"
                    className="flex h-13 w-13 sm:h-16 sm:w-16 items-center justify-center rounded-full border border-rose-500/40 bg-white dark:bg-slate-800 text-rose-500 shadow-xl transition duration-200 hover:scale-110 hover:bg-rose-500 hover:text-white active:scale-95 cursor-pointer"
                  >
                    <span className="text-xl sm:text-2xl font-bold">✕</span>
                  </button>

                  {/* 3. SUPER CONNECT / WAVE BUTTON */}
                  <button
                    type="button"
                    onClick={() => {
                      if (!currentProfile) return;
                      setMatchedProfile(currentProfile);
                      setToastMessage(`⚡ Super-Connected with ${currentProfile.name}!`);
                      setTimeout(() => setToastMessage(null), 3000);
                    }}
                    title="Super Connect / Direct Wave"
                    className="flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-full border border-teal-400/50 bg-teal-500 text-slate-950 shadow-xl shadow-teal-500/25 transition duration-200 hover:scale-110 active:scale-95 cursor-pointer"
                  >
                    <span className="text-lg sm:text-xl font-bold">⚡</span>
                  </button>

                  {/* 4. HEART / GAME INTEREST BUTTON */}
                  <button
                    type="button"
                    onClick={handleDoubleTap}
                    title="Express Game Interest / Like (Space or Double-Tap)"
                    className="flex h-13 w-13 sm:h-16 sm:w-16 items-center justify-center rounded-full border border-pink-500/40 bg-white dark:bg-slate-800 text-pink-500 shadow-xl transition duration-200 hover:scale-110 hover:bg-pink-500 hover:text-white active:scale-95 cursor-pointer"
                  >
                    <span className="text-xl sm:text-2xl">💖</span>
                  </button>

                  {/* 5. PLAN ACTIVITY MEETUP BUTTON */}
                  <button
                    type="button"
                    onClick={() => {
                      if (!currentProfile) return;
                      setPlanProposalTarget(currentProfile);
                      setProposalActivity(currentProfile.lookingFor);
                    }}
                    title="Propose Activity Plan"
                    className="flex h-11 w-11 sm:h-13 sm:w-13 items-center justify-center rounded-full border border-indigo-500/40 bg-white dark:bg-slate-800 text-indigo-500 shadow-lg transition duration-200 hover:scale-110 hover:bg-indigo-500 hover:text-white active:scale-95 cursor-pointer"
                  >
                    <span className="text-base sm:text-lg">🚀</span>
                  </button>
                </div>
              </>
            ) : (
              /* EMPTY DECK STATE */
              <div className="w-full max-w-md h-[460px] rounded-[2.5rem] bg-white p-8 text-center ring-1 ring-slate-200 flex flex-col items-center justify-center shadow-xl dark:bg-slate-900 dark:ring-slate-800">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-50 text-3xl dark:bg-teal-950">
                  🎉
                </div>
                <h3 className="mt-4 text-xl font-bold text-slate-900 dark:text-white">
                  You've Seen Everyone Nearby!
                </h3>
                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 max-w-xs">
                  You’ve swiped through all local recommendations for now. Check back as new members join Vynk!
                </p>
                <div className="mt-5 flex flex-wrap justify-center gap-2.5">
                  <button
                    type="button"
                    onClick={handleResetDeck}
                    className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white shadow-lg hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 transition cursor-pointer"
                  >
                    ↻ Review Matches Again
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(true)}
                    className="rounded-xl border border-teal-500 px-4 py-2 text-xs font-bold text-teal-600 hover:bg-teal-50 dark:text-teal-400 dark:hover:bg-slate-800 transition cursor-pointer"
                  >
                    + Add My Profile Card
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW MODE 2: GRID VIEW                                          */}
        {/* ============================================================== */}
        {viewMode === "GRID" && (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {deck.map((profile) => (
              <article
                key={profile.id}
                className="group overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200 transition duration-200 hover:-translate-y-1 hover:shadow-xl dark:bg-slate-900 dark:ring-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="relative h-64 overflow-hidden">
                    <img
                      src={profile.image}
                      alt={profile.name}
                      className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />

                    <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
                      <span className="rounded-full bg-slate-950/80 px-2.5 py-1 text-xs font-bold text-teal-300 backdrop-blur-md">
                        {profile.match}% Match
                      </span>
                      <span className="rounded-full bg-slate-950/80 px-2.5 py-1 text-xs text-slate-200 backdrop-blur-md">
                        📍 {profile.distance}
                      </span>
                    </div>

                    <div className="absolute bottom-3 left-4 right-4 text-white">
                      <h3 className="text-xl font-bold">
                        {profile.name}, {profile.age}
                      </h3>
                      <p className="text-xs text-teal-300 font-semibold mt-0.5">
                        🎯 {profile.lookingFor}
                      </p>
                      {/* Shared Alarm Badge in Grid */}
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        {profile.shared_availability?.[0] && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-bold text-amber-300">
                            ⏰ {profile.shared_availability[0]}
                          </span>
                        )}
                        {profile.relevant_skills?.[0] && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-bold text-teal-300">
                            ⚡ {profile.relevant_skills[0]}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 p-3.5 dark:border-slate-800 flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setMatchedProfile(profile);
                    }}
                    className="flex-1 rounded-xl bg-teal-600 py-2.5 text-xs font-bold text-white hover:bg-teal-700 transition cursor-pointer"
                  >
                    Accept / Connect
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPlanProposalTarget(profile);
                      setProposalActivity(profile.lookingFor);
                    }}
                    className="rounded-xl border border-teal-500/40 bg-teal-50/50 px-3 py-2.5 text-xs font-bold text-teal-700 hover:bg-teal-100/50 dark:bg-teal-950/30 dark:text-teal-300 text-center transition cursor-pointer"
                  >
                    🚀 Plan
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW MODE 3: AI TEMPORARY COHORTS & SQUADS                     */}
        {/* ============================================================== */}
        {viewMode === "PROPOSALS" && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* 1. HERO AI COHORT GENERATOR */}
            <div className="relative overflow-hidden rounded-3xl border border-teal-500/30 bg-gradient-to-br from-teal-500/10 via-white to-indigo-500/10 p-5 sm:p-6 shadow-md backdrop-blur-md dark:from-teal-950/30 dark:via-slate-900 dark:to-indigo-950/30 dark:border-teal-400/20">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-full bg-teal-500/20 px-3 py-1 text-xs font-bold text-teal-700 dark:text-teal-300">
                  <span>⚡</span>
                  <span>AI Temporary Cohort Engine (/groups/proposals)</span>
                </div>
                <h2 className="mt-2 text-xl sm:text-2xl font-black text-slate-900 dark:text-white">
                  Spontaneous Squads & Group Meetups
                </h2>
                <p className="mt-1 text-xs sm:text-sm text-slate-600 dark:text-slate-300">
                  Vynk AI matches 2–6 local peers with shared skills and calendar availability.
                  Once quorum accepts, convert the squad directly into a scheduled Event!
                </p>
              </div>

              {/* Natural Language Prompt Form */}
              <form
                onSubmit={handleCreateAiCohort}
                className="mt-4 flex flex-col sm:flex-row gap-2.5 items-stretch"
              >
                <div className="relative flex-1">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">✨</span>
                  <input
                    type="text"
                    id="input-ai-cohort-query"
                    value={aiCohortQuery}
                    onChange={(e) => setAiCohortQuery(e.target.value)}
                    placeholder="e.g. '4 players for badminton doubles this Saturday morning in Indiranagar'..."
                    className="w-full rounded-2xl border border-slate-200 bg-white/90 py-3.5 pl-11 pr-4 text-xs font-semibold text-slate-900 shadow-sm transition focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  />
                  {aiCohortQuery && (
                    <button
                      type="button"
                      onClick={() => setAiCohortQuery("")}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      ✕
                    </button>
                  )}
                </div>

                <button
                  type="submit"
                  id="btn-form-ai-squad"
                  disabled={isProposingAiCohort || !aiCohortQuery.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-400 px-6 py-3.5 text-xs font-extrabold text-slate-950 shadow-lg shadow-teal-500/20 hover:brightness-105 active:scale-95 transition cursor-pointer disabled:opacity-50 shrink-0"
                >
                  <span>{isProposingAiCohort ? "Forming Squad..." : "Form AI Squad"}</span>
                  <span>🚀</span>
                </button>
              </form>

              {/* One-click Prompt Chips */}
              <div className="mt-3.5 flex flex-wrap items-center gap-1.5 text-xs">
                <span className="text-[11px] font-bold text-slate-400 mr-1">Try prompts:</span>
                {[
                  "4 players for badminton doubles this Saturday",
                  "Weekend photo walk & coffee circle in Jubilee Hills",
                  "Board games night with 4 players in Madhapur",
                  "Sunday morning 20km cycling trail",
                ].map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => {
                      setAiCohortQuery(chip);
                      handleCreateAiCohort(undefined, chip);
                    }}
                    className="rounded-full border border-teal-500/30 bg-white/80 dark:bg-slate-800/80 px-2.5 py-1 text-[11px] font-semibold text-teal-700 dark:text-teal-300 hover:bg-teal-50 dark:hover:bg-slate-700 transition cursor-pointer shadow-sm"
                  >
                    ✦ {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* 2. STATS & FILTER TABS */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200/80 pb-3 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setProposalsFilter("ALL")}
                  className={`rounded-xl px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                    proposalsFilter === "ALL"
                      ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  All Cohorts ({myProposals.length})
                </button>

                <button
                  type="button"
                  onClick={() => setProposalsFilter("CONFIRMED")}
                  className={`rounded-xl px-3 py-1.5 text-xs font-bold transition cursor-pointer flex items-center gap-1 ${
                    proposalsFilter === "CONFIRMED"
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  <span>✓</span> Quorum Confirmed ({confirmedCount})
                </button>

                <button
                  type="button"
                  onClick={() => setProposalsFilter("PROPOSED")}
                  className={`rounded-xl px-3 py-1.5 text-xs font-bold transition cursor-pointer flex items-center gap-1 ${
                    proposalsFilter === "PROPOSED"
                      ? "bg-amber-500 text-slate-950"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  <span>⏳</span> Waiting RSVPs ({proposedCount})
                </button>

                <button
                  type="button"
                  onClick={() => setProposalsFilter("CONVERTED")}
                  className={`rounded-xl px-3 py-1.5 text-xs font-bold transition cursor-pointer flex items-center gap-1 ${
                    proposalsFilter === "CONVERTED"
                      ? "bg-purple-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  <span>🎉</span> Converted ({convertedCount})
                </button>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => fetchMyProposals()}
                  disabled={loadingProposals}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 shadow-sm transition cursor-pointer"
                >
                  <span>{loadingProposals ? "↻" : "⟳"}</span>
                  <span>{loadingProposals ? "Syncing..." : "Sync Proposals"}</span>
                </button>
                <Link
                  href="/events"
                  className="inline-flex items-center gap-1 rounded-xl bg-teal-50 px-3 py-1.5 font-bold text-teal-700 hover:bg-teal-100 dark:bg-teal-950/40 dark:text-teal-300 transition"
                >
                  <span>Events Hub</span>
                  <span>➔</span>
                </Link>
              </div>
            </div>

            {/* 3. PROPOSALS CARDS GRID */}
            {filteredProposals.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
                <span className="text-4xl">👥</span>
                <h3 className="mt-3 text-lg font-bold text-slate-900 dark:text-white">
                  No Cohorts in this Filter
                </h3>
                <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
                  Use the AI Cohort Formulator above or match with peers on the Deck to create spontaneous meetup proposals!
                </p>
                <button
                  type="button"
                  onClick={() => setProposalsFilter("ALL")}
                  className="mt-4 rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-teal-400 transition"
                >
                  View All Cohorts
                </button>
              </div>
            ) : (
              <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                {filteredProposals.map((proposal) => {
                  const acceptedCount = proposal.members.filter((m) => m.status === "ACCEPTED").length;
                  const isHost =
                    proposal.initiator_user_id === currentUserId ||
                    proposal.initiator_name === currentUserName ||
                    proposal.initiator_name === "You";
                  const currentUserMember = proposal.members.find(
                    (m) =>
                      m.user_id === currentUserId ||
                      m.display_name === "You" ||
                      m.display_name.toLowerCase().includes("you")
                  );
                  const isInvited = currentUserMember?.status === "INVITED";
                  const isAccepted = currentUserMember?.status === "ACCEPTED";
                  const quorumPct = Math.min(100, Math.round((acceptedCount / proposal.min_required_size) * 100));

                  return (
                    <article
                      key={proposal.proposal_id}
                      className="group flex flex-col justify-between overflow-hidden rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition duration-200 hover:-translate-y-1 hover:shadow-xl dark:bg-slate-900 dark:ring-slate-800"
                    >
                      <div className="space-y-4">
                        {/* Status & Size Top Bar */}
                        <div className="flex items-center justify-between gap-2">
                          {proposal.status === "CONFIRMED" && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                              Quorum Reached
                            </span>
                          )}
                          {proposal.status === "PROPOSED" && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 border border-amber-500/30 px-2.5 py-1 text-[11px] font-bold text-amber-600 dark:text-amber-400">
                              <span>⏳</span> Waiting for RSVPs
                            </span>
                          )}
                          {proposal.status === "CONVERTED_TO_EVENT" && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-2.5 py-1 text-[11px] font-bold text-purple-600 dark:text-purple-400">
                              <span>🎉</span> Official Event #{proposal.converted_event_id || 42}
                            </span>
                          )}
                          {proposal.status !== "CONFIRMED" &&
                            proposal.status !== "PROPOSED" &&
                            proposal.status !== "CONVERTED_TO_EVENT" && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                                {proposal.status}
                              </span>
                            )}

                          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-1 text-[11px] font-bold text-slate-700 dark:text-slate-300">
                            👥 {acceptedCount}/{proposal.target_size} Players
                          </span>
                        </div>

                        {/* Title & Description */}
                        <div>
                          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                            <span>{proposal.activity_title || "Group Activity"}</span>
                            <span>•</span>
                            <span>Host: {proposal.initiator_name || "Community"}</span>
                          </div>
                          <h3 className="mt-1 text-base font-extrabold text-slate-900 dark:text-white leading-snug">
                            {proposal.title}
                          </h3>
                          {proposal.description && (
                            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                              {proposal.description}
                            </p>
                          )}
                        </div>

                        {/* Schedule & Venue Card */}
                        <div className="rounded-2xl bg-slate-50 p-3 text-xs space-y-1.5 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <span className="text-slate-400">📅</span>
                            <span className="font-semibold">{proposal.proposed_date}</span>
                            <span className="text-slate-400">•</span>
                            <span>{proposal.proposed_start_time} - {proposal.proposed_end_time}</span>
                          </div>
                          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <span className="text-slate-400">📍</span>
                            <span className="font-semibold">{proposal.suggested_venue_name || proposal.target_locality}</span>
                            {proposal.suggested_venue_name && (
                              <span className="text-slate-400 text-[11px]">({proposal.target_locality})</span>
                            )}
                          </div>
                        </div>

                        {/* Quorum Threshold Progress Bar */}
                        <div>
                          <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                            <span className="text-slate-600 dark:text-slate-400">
                              Quorum: {acceptedCount}/{proposal.min_required_size} confirmed
                            </span>
                            <span className={acceptedCount >= proposal.min_required_size ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}>
                              {quorumPct}%
                            </span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400 transition-all duration-300"
                              style={{ width: `${quorumPct}%` }}
                            />
                          </div>
                          <p className="mt-1 text-[10px] text-slate-400">
                            {acceptedCount >= proposal.min_required_size
                              ? "✓ Minimum quorum reached! Ready to convert into scheduled event."
                              : `Needs ${proposal.min_required_size - acceptedCount} more accepted response(s).`}
                          </p>
                        </div>

                        {/* Members Roster */}
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                            Squad Roster ({proposal.members.length} members)
                          </div>
                          <div className="space-y-1.5">
                            {proposal.members.map((member) => (
                              <div
                                key={member.user_id}
                                className="flex items-center justify-between rounded-xl bg-slate-50/70 dark:bg-slate-800/40 px-2.5 py-1.5 text-xs"
                              >
                                <div className="flex items-center gap-2">
                                  {member.avatar_url ? (
                                    <img
                                      src={member.avatar_url}
                                      alt={member.display_name}
                                      className="h-6 w-6 rounded-full object-cover"
                                    />
                                  ) : (
                                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/20 text-[10px] font-bold text-teal-700 dark:text-teal-300">
                                      {member.display_name.charAt(0)}
                                    </div>
                                  )}
                                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                                    {member.display_name}
                                  </span>
                                  {member.user_id === proposal.initiator_user_id && (
                                    <span className="text-[10px] text-amber-500 font-bold">👑 Host</span>
                                  )}
                                </div>

                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] font-bold text-teal-600 dark:text-teal-400">
                                    ⚡ {Math.round(member.compatibility_score)}%
                                  </span>
                                  {member.status === "ACCEPTED" && (
                                    <span className="rounded-md bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300">
                                      ✓ Joined
                                    </span>
                                  )}
                                  {member.status === "INVITED" && (
                                    <span className="rounded-md bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300">
                                      ⏳ Invited
                                    </span>
                                  )}
                                  {member.status === "DECLINED" && (
                                    <span className="rounded-md bg-rose-500/20 px-1.5 py-0.5 text-[10px] font-bold text-rose-700 dark:text-rose-300">
                                      ✕ Declined
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Action Footer */}
                      <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800">
                        {/* Case 1: Current user is invited and hasn't responded */}
                        {isInvited && (
                          <div className="flex gap-2">
                            <button
                              type="button"
                              id={`btn-accept-proposal-${proposal.proposal_id}`}
                              onClick={() => handleRespondProposal(proposal.proposal_id, "ACCEPTED")}
                              disabled={respondingProposalId === proposal.proposal_id}
                              className="flex-1 rounded-xl bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:bg-emerald-400 transition cursor-pointer flex items-center justify-center gap-1.5"
                            >
                              <span>✓</span>
                              <span>{respondingProposalId === proposal.proposal_id ? "Joining..." : "Accept & Join Squad"}</span>
                            </button>
                            <button
                              type="button"
                              id={`btn-decline-proposal-${proposal.proposal_id}`}
                              onClick={() => handleRespondProposal(proposal.proposal_id, "DECLINED")}
                              disabled={respondingProposalId === proposal.proposal_id}
                              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 transition cursor-pointer"
                            >
                              ✕ Decline
                            </button>
                          </div>
                        )}

                        {/* Case 2: Status is CONFIRMED and current user is Host -> Convert to scheduled Event */}
                        {!isInvited && proposal.status === "CONFIRMED" && isHost && (
                          <button
                            type="button"
                            id={`btn-convert-proposal-${proposal.proposal_id}`}
                            onClick={() => handleConvertProposal(proposal.proposal_id)}
                            disabled={convertingProposalId === proposal.proposal_id}
                            className="w-full rounded-2xl bg-gradient-to-r from-teal-500 via-emerald-400 to-teal-400 py-3 text-xs font-extrabold text-slate-950 shadow-lg shadow-teal-500/25 hover:brightness-105 active:scale-95 transition cursor-pointer flex items-center justify-center gap-2"
                          >
                            <span>🚀</span>
                            <span>{convertingProposalId === proposal.proposal_id ? "Converting into Event..." : "Convert into Scheduled Event"}</span>
                          </button>
                        )}

                        {/* Case 3: Status is CONFIRMED and current user is Member (not host) */}
                        {!isInvited && proposal.status === "CONFIRMED" && !isHost && (
                          <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-500/30 p-2.5 text-center text-xs font-bold text-emerald-700 dark:text-emerald-300 flex items-center justify-center gap-1.5">
                            <span>✓</span>
                            <span>Quorum confirmed! Host will convert into scheduled event.</span>
                          </div>
                        )}

                        {/* Case 4: Status is CONVERTED_TO_EVENT */}
                        {proposal.status === "CONVERTED_TO_EVENT" && (
                          <Link
                            href="/events"
                            id={`btn-view-event-${proposal.proposal_id}`}
                            className="w-full rounded-xl bg-purple-600 py-2.5 text-xs font-bold text-white shadow-md hover:bg-purple-500 transition text-center flex items-center justify-center gap-1.5"
                          >
                            <span>📅 View in Events Hub</span>
                            <span>➔</span>
                          </Link>
                        )}

                        {/* Case 5: User already accepted and proposal is still waiting for others */}
                        {!isInvited && proposal.status === "PROPOSED" && isAccepted && (
                          <div className="rounded-xl bg-slate-50 dark:bg-slate-800/80 p-2.5 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center justify-center gap-1.5">
                            <span>✓</span>
                            <span>You've joined. Waiting for others to confirm quorum...</span>
                          </div>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* FIRST-TIME ONBOARDING / GESTURE GUIDE MODAL                    */}
        {/* ============================================================== */}
        {showTutorial && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-sm rounded-[2.5rem] bg-slate-900 border border-slate-800 p-6 text-white shadow-2xl">
              <div className="text-center">
                <span className="text-4xl">👋</span>
                <h3 className="mt-3 text-xl font-bold tracking-tight">
                  Swipe Controls
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Control everything smoothly with your hand or keyboard:
                </p>
              </div>

              <div className="mt-5 space-y-3">
                {/* Right Swipe / Right Arrow */}
                <div className="flex items-start gap-3 rounded-2xl bg-slate-800/80 p-3 border border-emerald-500/30">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 text-lg">
                    👉
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-emerald-300">
                      Right Swipe or [→ Arrow] = Accept
                    </h4>
                    <p className="mt-0.5 text-[11px] text-slate-300 leading-snug">
                      Connect with them so whatever activities or games you want to play, you can connect!
                    </p>
                  </div>
                </div>

                {/* Left Swipe / Left Arrow */}
                <div className="flex items-start gap-3 rounded-2xl bg-slate-800/80 p-3 border border-rose-500/30">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400 text-lg">
                    👈
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-rose-300">
                      Left Swipe or [← Arrow] = Reject
                    </h4>
                    <p className="mt-0.5 text-[11px] text-slate-300 leading-snug">
                      Pass on this profile and smoothly move to the next member.
                    </p>
                  </div>
                </div>

                {/* Double Click / Space */}
                <div className="flex items-start gap-3 rounded-2xl bg-slate-800/80 p-3 border border-teal-500/30">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400 text-lg">
                    💖
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-teal-300">
                      Double Click or [Space] = Like / Game Interest
                    </h4>
                    <p className="mt-0.5 text-[11px] text-slate-300 leading-snug">
                      Instagram-style like! Marks that whenever they are planning games, you are also interested!
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                id="btn-dismiss-swipe-tutorial"
                onClick={handleDismissTutorial}
                className="mt-6 w-full rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-400 py-3 text-xs font-black text-slate-950 shadow-lg hover:brightness-110 transition cursor-pointer"
              >
                Got It, Start Swiping! 🚀
              </button>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* MODAL 1: UPLOAD PHOTO & CREATE CARD MODAL                       */}
        {/* ============================================================== */}
        {showUploadModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 animate-in fade-in zoom-in-95 duration-200">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>📷</span> Upload Photo & Connection Card
                </h3>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xl font-bold cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleAddCustomCard} className="mt-4 space-y-4">
                {/* Photo Upload Box */}
                <div className="text-center">
                  <p className="text-xs font-semibold uppercase text-slate-500 mb-2">
                    Card Profile Photo
                  </p>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="mx-auto relative h-36 w-36 rounded-3xl border-2 border-dashed border-teal-400/60 bg-teal-50/50 hover:bg-teal-50 dark:bg-slate-800 flex flex-col items-center justify-center cursor-pointer overflow-hidden transition group"
                  >
                    {customImagePreview ? (
                      <>
                        <img
                          src={customImagePreview}
                          alt="Preview"
                          className="h-full w-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-xs text-white font-bold transition">
                          Change Photo
                        </div>
                      </>
                    ) : (
                      <>
                        <span className="text-4xl mb-1">📸</span>
                        <span className="text-xs font-bold text-teal-700 dark:text-teal-300">
                          Click to upload
                        </span>
                        <span className="text-[10px] text-slate-400">PNG, JPG or WebP</span>
                      </>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {/* Name & Age */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-2">
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                      Name
                    </label>
                    <input
                      type="text"
                      required
                      value={customName}
                      onChange={(e) => setCustomName(e.target.value)}
                      placeholder="Your name"
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                      Age
                    </label>
                    <input
                      type="number"
                      required
                      min={18}
                      max={99}
                      value={customAge}
                      onChange={(e) => setCustomAge(Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                </div>

                {/* Activity Interested */}
                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                    Activity Interested / Game Plan
                  </label>
                  <input
                    type="text"
                    required
                    value={customLookingFor}
                    onChange={(e) => setCustomLookingFor(e.target.value)}
                    placeholder="e.g. Weekend cycling buddy, badminton sparring"
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
                    className="flex-1 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 rounded-xl bg-teal-600 py-2.5 text-xs font-bold text-white hover:bg-teal-700 shadow-md transition"
                  >
                    Add to Deck ✦
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* MODAL 2: CELEBRATION MODAL ("IT'S A CONNECTION!")              */}
        {/* ============================================================== */}
        {matchedProfile && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4 animate-in fade-in duration-300">
            <div className="relative w-full max-w-sm rounded-[2.5rem] bg-gradient-to-b from-slate-900 to-indigo-950 p-6 text-center text-white shadow-2xl ring-1 ring-white/20">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/20 text-3xl text-emerald-400 border border-emerald-500/40 animate-bounce">
                💚
              </div>

              <p className="mt-3 text-xs font-extrabold uppercase tracking-widest text-teal-300">
                Mutual Affinity!
              </p>

              <h3 className="mt-1 text-2xl font-black">
                It's a Connection!
              </h3>

              <p className="mt-2 text-xs text-slate-300">
                You and <span className="font-bold text-white">{matchedProfile.name}</span> are now connected for{" "}
                <span className="text-teal-300 font-semibold">{matchedProfile.lookingFor}</span>.
              </p>

              <div className="mt-4 flex items-center justify-center -space-x-4">
                <img
                  src={matchedProfile.image}
                  alt={matchedProfile.name}
                  className="h-14 w-14 rounded-full border-4 border-slate-900 object-cover shadow-lg"
                />
                <div className="flex h-14 w-14 items-center justify-center rounded-full border-4 border-slate-900 bg-teal-500 text-slate-950 text-lg font-bold shadow-lg">
                  YOU
                </div>
              </div>

              <div className="mt-5 space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    const target = matchedProfile;
                    setMatchedProfile(null);
                    setPlanProposalTarget(target);
                    setProposalActivity(target.lookingFor);
                  }}
                  className="w-full rounded-2xl bg-teal-400 py-2.5 text-xs font-bold text-slate-950 shadow-lg hover:bg-teal-300 transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <span>🚀</span>
                  <span>Propose Plan / Activity Now</span>
                </button>

                <button
                  type="button"
                  onClick={() => setMatchedProfile(null)}
                  className="w-full rounded-2xl border border-white/20 py-2 text-xs font-semibold text-slate-300 hover:bg-white/10 transition cursor-pointer"
                >
                  Keep Swiping
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* MODAL 3: ACTIVITY / PLAN PROPOSAL MODAL                        */}
        {/* ============================================================== */}
        {planProposalTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-md rounded-[2.5rem] bg-white p-6 md:p-8 shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 text-slate-900 dark:text-white">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <img
                    src={planProposalTarget.image}
                    alt={planProposalTarget.name}
                    className="h-10 w-10 rounded-full object-cover ring-2 ring-teal-500"
                  />
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                      Co-Op Plan Creator
                    </span>
                    <h3 className="text-lg font-extrabold leading-tight">
                      Plan with {planProposalTarget.name}
                    </h3>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setPlanProposalTarget(null)}
                  className="h-7 w-7 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs text-slate-500 hover:text-slate-800 dark:text-slate-300 cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSendPlanProposal} className="mt-5 space-y-4">
                {/* Activity Name */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                    🎯 Activity / Plan
                  </label>
                  <select
                    value={proposalActivity}
                    onChange={(e) => setProposalActivity(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs font-semibold text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="Badminton Sparring Session">🏸 Badminton Sparring Session</option>
                    <option value="Weekend Photo Walk & Coffee">📷 Weekend Photo Walk & Coffee</option>
                    <option value="Morning Cycling Trail">🚴 Morning Cycling Trail</option>
                    <option value="Board Games & Chai Meetup">🎲 Board Games & Chai Meetup</option>
                    <option value="Live Music & Indie Gig">🎸 Live Music & Indie Gig</option>
                    <option value="Tennis / Pickleball Match">🎾 Tennis / Pickleball Match</option>
                    <option value="Casual Evening Walk & Talk">☕ Casual Evening Walk & Talk</option>
                  </select>
                </div>

                {/* Day / Date & Time Alarms */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                      📅 Day / Date
                    </label>
                    <select
                      value={proposalDate}
                      onChange={(e) => setProposalDate(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs font-semibold text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    >
                      <option value="This Saturday">Saturday</option>
                      <option value="This Sunday">Sunday</option>
                      <option value="Weekday Evening">Weekday Evening</option>
                      <option value="Tomorrow">Tomorrow</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                      ⏰ Start Time
                    </label>
                    <input
                      type="text"
                      value={proposalTime}
                      onChange={(e) => setProposalTime(e.target.value)}
                      placeholder="e.g. 07:30 AM"
                      className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs font-semibold text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                </div>

                {/* Shared Availability Helper */}
                {planProposalTarget.shared_availability?.[0] && (
                  <div className="rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 p-2.5 text-[11px] text-amber-900 dark:text-amber-300 flex items-center gap-1.5">
                    <span>💡</span>
                    <span>
                      {planProposalTarget.name} has open alarm window: <strong>{planProposalTarget.shared_availability[0]}</strong>
                    </span>
                  </div>
                )}

                {/* Note */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                    💬 Note / Message (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={proposalNotes}
                    onChange={(e) => setProposalNotes(e.target.value)}
                    placeholder="e.g. Let's book a court at Jubilee Hills or grab filter chai!"
                    className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setPlanProposalTarget(null)}
                    className="flex-1 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingProposal}
                    className="flex-1 rounded-xl bg-teal-400 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-300 shadow-md transition cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    {isSubmittingProposal ? "Sending..." : "🚀 Send Plan Invite"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
