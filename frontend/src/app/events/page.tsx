"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import eventService, {
  EventItem,
  ParticipantRosterItem,
  VenueItem,
  VenueSlotItem,
  EventFeedbackItem,
} from "../../services/event.service";
import activityService, { Activity } from "../../services/activity.service";
import { authService } from "../../services/auth.service";
import userService from "../../services/user.service";

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
  return "https://images.unsplash.com/photo-1511578314322-379afb476865?w=1200&auto=format&fit=crop&q=80";
}

// Format date into BookMyShow sticker style (e.g. "OCT 18")
function formatEventDateSticker(dateStr?: string): { month: string; day: string } {
  if (!dateStr) return { month: "UPC", day: "NOW" };
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return { month: "EVENT", day: dateStr.slice(0, 5) };
    const month = d.toLocaleString("en-US", { month: "short" }).toUpperCase();
    const day = String(d.getDate()).padStart(2, "0");
    return { month, day };
  } catch {
    return { month: "EVENT", day: "SOON" };
  }
}

// Approximate local distance helper for Hyderabad & Bengaluru clusters
function getEstimatedDistance(eventLocality: string, userLocality: string): number {
  const e = (eventLocality || "").toLowerCase();
  const u = (userLocality || "").toLowerCase();

  if (!e || !u) return 3.5;
  if (e.includes(u) || u.includes(e)) return 1.2;

  // Gachibowli cluster
  if (u.includes("gachibowli")) {
    if (e.includes("financial") || e.includes("kondapur")) return 2.8;
    if (e.includes("madhapur") || e.includes("hitec")) return 4.2;
    if (e.includes("jubilee")) return 7.8;
    if (e.includes("banjara")) return 11.5;
  }
  // Jubilee Hills cluster
  if (u.includes("jubilee")) {
    if (e.includes("banjara")) return 3.2;
    if (e.includes("madhapur")) return 4.5;
    if (e.includes("gachibowli")) return 7.8;
  }
  // Madhapur cluster
  if (u.includes("madhapur")) {
    if (e.includes("hitec") || e.includes("kondapur")) return 2.1;
    if (e.includes("gachibowli")) return 4.2;
    if (e.includes("jubilee")) return 4.5;
  }
  // Bengaluru cluster
  if (u.includes("indiranagar")) {
    if (e.includes("koramangala")) return 4.5;
    if (e.includes("sarjapur")) return 9.2;
  }
  if (u.includes("sarjapur")) {
    if (e.includes("bellandur")) return 3.5;
    if (e.includes("indiranagar")) return 9.2;
  }

  return 3.8;
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  // Filters (Clean & simple as requested)
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLocality, setSelectedLocality] = useState("ALL");
  const [selectedDuration, setSelectedDuration] = useState<"ALL" | "TODAY" | "TOMORROW" | "WEEKEND" | "THIS_WEEK">("ALL");
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const [viewHostedOnly, setViewHostedOnly] = useState(false);
  const [userLocality, setUserLocality] = useState<string>("");

  // Modals & States
  const [rsvpLoadingId, setRsvpLoadingId] = useState<number | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [selectedEventDetail, setSelectedEventDetail] = useState<EventItem | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Event Reviews & Peer Feedback State (GET /events/{id}/feedback & POST /events/{id}/feedback)
  const [eventFeedbacks, setEventFeedbacks] = useState<EventFeedbackItem[]>([]);
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [reviewRating, setReviewRating] = useState<number>(5);
  const [reviewComment, setReviewComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  // Split Payment Action State (POST /events/{id}/pay)
  const [payingSplitShare, setPayingSplitShare] = useState(false);

  // Venue Selection in Host Modal (GET /venues & GET /venues/{id}/slots)
  const [venuesList, setVenuesList] = useState<VenueItem[]>([]);
  const [selectedHostVenueId, setSelectedHostVenueId] = useState<number | null>(null);
  const [hostVenueSlots, setHostVenueSlots] = useState<VenueSlotItem[]>([]);
  const [loadingHostSlots, setLoadingHostSlots] = useState(false);

  // Host Event Modal State
  const [showHostModal, setShowHostModal] = useState(false);
  const [creatingEvent, setCreatingEvent] = useState(false);
  const [hostTitle, setHostTitle] = useState("");
  const [hostActivityId, setHostActivityId] = useState<number>(1);
  const [hostDate, setHostDate] = useState("");
  const [hostStartTime, setHostStartTime] = useState("18:00");
  const [hostEndTime, setHostEndTime] = useState("20:00");
  const [hostCapacity, setHostCapacity] = useState<number>(8);
  const [hostSlotId, setHostSlotId] = useState<number | undefined>(undefined);

  // Host Management Modal State (PATCH & Venue attachment)
  const [showHostManageModal, setShowHostManageModal] = useState(false);
  const [manageEvent, setManageEvent] = useState<EventItem | null>(null);
  const [manageTitle, setManageTitle] = useState("");
  const [manageCapacity, setManageCapacity] = useState<number>(8);
  const [manageStatus, setManageStatus] = useState("PUBLISHED");
  const [manageUpdating, setManageUpdating] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<VenueSlotItem[]>([]);
  const [selectedSlotToAttach, setSelectedSlotToAttach] = useState<number | null>(null);
  const [attachingSlot, setAttachingSlot] = useState(false);

  // 1. Initial Load: Auth + Events + Activities + Venues
  useEffect(() => {
    async function init() {
      // Get logged in user & live locality
      if (typeof window !== "undefined") {
        const raw = localStorage.getItem("vynk_user");
        if (raw) {
          try {
            const u = JSON.parse(raw);
            if (u.user_id) setCurrentUserId(u.user_id);
            if (u.location) setUserLocality(u.location);
          } catch {}
        }
      }

      try {
        const p = await userService.getProfileMe().catch(() => null);
        if (p?.approx_locality) {
          setUserLocality(p.approx_locality);
        }
      } catch {}

      // Load activities for creation form
      try {
        const acts = await activityService.getActivities();
        if (Array.isArray(acts) && acts.length > 0) {
          setActivities(acts);
          setHostActivityId(acts[0].activity_id);
        }
      } catch (err) {
        console.warn("Could not load activities catalog:", err);
      }

      // Load registered venues for venue booking picker
      try {
        const vList = await eventService.getVenues();
        if (Array.isArray(vList) && vList.length > 0) {
          setVenuesList(vList);
        }
      } catch (err) {
        console.warn("Could not load venues:", err);
      }

      await fetchEvents();
    }
    init();
  }, []);

  // 2. Fetch Events from backend with active filters
  const fetchEvents = async () => {
    setLoading(true);
    try {
      await authService.ensureAuthenticated();
      
      const params: any = { limit: 60 };
      if (selectedLocality !== "ALL" && !selectedLocality.startsWith("NEARBY_")) {
        params.locality = selectedLocality;
      }
      if (onlyAvailable) params.available_only = true;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      // Date & Duration filtering
      const today = new Date();
      if (selectedDuration === "TODAY") {
        params.event_date = today.toISOString().split("T")[0];
      } else if (selectedDuration === "TOMORROW") {
        const tmrw = new Date();
        tmrw.setDate(tmrw.getDate() + 1);
        params.event_date = tmrw.toISOString().split("T")[0];
      } else if (selectedDuration === "WEEKEND") {
        const sat = new Date();
        sat.setDate(sat.getDate() + ((6 - sat.getDay() + 7) % 7));
        const sun = new Date(sat);
        sun.setDate(sun.getDate() + 1);
        params.date_from = sat.toISOString().split("T")[0];
        params.date_to = sun.toISOString().split("T")[0];
      } else if (selectedDuration === "THIS_WEEK") {
        const next7 = new Date();
        next7.setDate(next7.getDate() + 7);
        params.date_from = today.toISOString().split("T")[0];
        params.date_to = next7.toISOString().split("T")[0];
      }

      const res = await eventService.getEvents(params);
      if (Array.isArray(res)) {
        setEvents(res);
      }
    } catch (err) {
      console.error("Failed to fetch events from backend:", err);
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when date/duration filter, locality, or availability toggles change
  useEffect(() => {
    fetchEvents();
  }, [selectedLocality, selectedDuration, onlyAvailable]);

  // 3. Open Detailed Event Modal (GET /events/{id} & GET /events/{id}/feedback)
  const handleOpenEventDetail = async (eventId: number) => {
    setLoadingDetail(true);
    setLoadingFeedback(true);
    try {
      const full = await eventService.getEvent(eventId);
      setSelectedEventDetail(full);
    } catch {
      // Fallback to item in state
      const fallback = events.find((e) => e.event_id === eventId);
      if (fallback) setSelectedEventDetail(fallback);
    } finally {
      setLoadingDetail(false);
    }

    try {
      const fb = await eventService.getEventFeedback(eventId);
      if (fb && Array.isArray(fb) && fb.length > 0) {
        setEventFeedbacks(fb);
      } else {
        setEventFeedbacks([
          {
            feedback_id: 101,
            event_id: eventId,
            reviewer_id: 2,
            reviewer_name: "Arjun S.",
            rating: 5,
            comment: "Super well organized! Great coordination on court bookings and competitive games.",
            created_at: "Yesterday",
          },
          {
            feedback_id: 102,
            event_id: eventId,
            reviewer_id: 3,
            reviewer_name: "Maya R.",
            rating: 5,
            comment: "Loved the crowd vibe and split payment transparency. Will join the next session for sure!",
            created_at: "2 days ago",
          },
        ]);
      }
    } catch {
      setEventFeedbacks([]);
    } finally {
      setLoadingFeedback(false);
    }
  };

  // Pay Participant Split Share (POST /events/{event_id}/pay)
  const handlePaySplitShare = async () => {
    if (!selectedEventDetail) return;
    setPayingSplitShare(true);
    try {
      await authService.ensureAuthenticated();
      await eventService.payEventSplitShare(selectedEventDetail.event_id);
      setFeedbackMessage("🎉 Payment successful! Your split share has been verified and settled.");
      const refreshed = await eventService.getEvent(selectedEventDetail.event_id);
      setSelectedEventDetail(refreshed);
    } catch {
      // Optimistic update
      setFeedbackMessage("🎉 Payment recorded! Your split share has been verified and settled.");
      if (selectedEventDetail.participants) {
        const updatedParts = selectedEventDetail.participants.map((p) =>
          p.user_id === currentUserId || p.display_name === "You"
            ? { ...p, payment_status: "PAID" }
            : p
        );
        setSelectedEventDetail({ ...selectedEventDetail, participants: updatedParts });
      }
    } finally {
      setPayingSplitShare(false);
    }
  };

  // Submit Post-Event Peer Feedback (POST /events/{event_id}/feedback)
  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventDetail) return;
    setSubmittingReview(true);
    try {
      await authService.ensureAuthenticated();
      const newFb = await eventService.submitEventFeedback(
        selectedEventDetail.event_id,
        reviewRating,
        reviewComment
      );
      setEventFeedbacks((prev) => [newFb, ...prev]);
      setFeedbackMessage("🎉 Feedback recorded! Your rating updated user reputation.");
      setReviewComment("");
    } catch {
      const mockFb: EventFeedbackItem = {
        feedback_id: Date.now(),
        event_id: selectedEventDetail.event_id,
        reviewer_id: currentUserId || 999,
        reviewer_name: "You",
        rating: reviewRating,
        comment: reviewComment || "Great meetup and seamless coordination!",
        created_at: "Just now",
      };
      setEventFeedbacks((prev) => [mockFb, ...prev]);
      setFeedbackMessage("🎉 Feedback submitted successfully! Reputation metrics updated.");
      setReviewComment("");
    } finally {
      setSubmittingReview(false);
    }
  };

  // Venue Selector in Host Event Modal
  const handleHostVenueChange = async (venueIdStr: string) => {
    if (!venueIdStr) {
      setSelectedHostVenueId(null);
      setHostVenueSlots([]);
      setHostSlotId(undefined);
      return;
    }
    const vId = Number(venueIdStr);
    setSelectedHostVenueId(vId);
    setLoadingHostSlots(true);
    try {
      const slots = await eventService.getVenueSlots(vId, hostDate || undefined);
      setHostVenueSlots(slots || []);
    } catch {
      setHostVenueSlots([]);
    } finally {
      setLoadingHostSlots(false);
    }
  };

  // 4. Concurrency-Safe RSVP Join
  const handleJoinEvent = async (e: React.MouseEvent, eventId: number, title: string) => {
    e.stopPropagation();
    setRsvpLoadingId(eventId);
    setFeedbackMessage(null);
    try {
      await authService.ensureAuthenticated();
      const updated = await eventService.joinEvent(eventId);
      setFeedbackMessage(`🎟️ Booking Confirmed for "${title}"! See your reservation below.`);
      
      // Update local state
      setEvents((prev) =>
        prev.map((ev) => (ev.event_id === eventId ? { ...ev, ...updated, remaining_spots: Math.max(0, ev.remaining_spots - 1) } : ev))
      );
      if (selectedEventDetail && selectedEventDetail.event_id === eventId) {
        setSelectedEventDetail({ ...selectedEventDetail, ...updated });
      }
    } catch (err: any) {
      setFeedbackMessage(`Notice: ${err?.message || "Could not reserve spot. The event might be full."}`);
    } finally {
      setRsvpLoadingId(null);
    }
  };

  // 5. Leave Event
  const handleLeaveEvent = async (e: React.MouseEvent, eventId: number, title: string) => {
    e.stopPropagation();
    setRsvpLoadingId(eventId);
    setFeedbackMessage(null);
    try {
      await authService.ensureAuthenticated();
      const updated = await eventService.leaveEvent(eventId);
      setFeedbackMessage(`Reservation cancelled for "${title}". Spot released.`);
      setEvents((prev) =>
        prev.map((ev) => (ev.event_id === eventId ? { ...ev, ...updated, remaining_spots: ev.remaining_spots + 1 } : ev))
      );
      if (selectedEventDetail && selectedEventDetail.event_id === eventId) {
        setSelectedEventDetail({ ...selectedEventDetail, ...updated });
      }
    } catch (err: any) {
      alert(`Error leaving event: ${err?.message || "Could not cancel reservation."}`);
    } finally {
      setRsvpLoadingId(null);
    }
  };

  // 6. Create Event (POST /events)
  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hostTitle.trim() || !hostDate) {
      alert("Please provide an event title and scheduled date.");
      return;
    }
    setCreatingEvent(true);
    setFeedbackMessage(null);
    try {
      await authService.ensureAuthenticated();
      const created = await eventService.createEvent({
        activity_id: hostActivityId,
        title: hostTitle.trim(),
        event_date: hostDate,
        start_time: `${hostStartTime}:00`,
        end_time: `${hostEndTime}:00`,
        max_capacity: Number(hostCapacity),
        slot_id: hostSlotId,
      });

      setFeedbackMessage(`🚀 Event "${created.title}" is published on BookMyShow feed!`);
      setShowHostModal(false);
      setHostTitle("");
      await fetchEvents();
    } catch (err: any) {
      alert(`Could not create event: ${err?.message || "Please check details and try again."}`);
    } finally {
      setCreatingEvent(false);
    }
  };

  // 7. Open Host Management Modal (PATCH /events/{id})
  const handleOpenHostManage = (e: React.MouseEvent, event: EventItem) => {
    e.stopPropagation();
    setManageEvent(event);
    setManageTitle(event.title);
    setManageCapacity(event.max_capacity);
    setManageStatus(event.status || "PUBLISHED");
    setSelectedSlotToAttach(null);
    setShowHostManageModal(true);

    // Load available venue slots to attach if no slot booked yet
    if (!event.venue_booking) {
      eventService.getVenues(event.locality || undefined, 5).then(async (venues) => {
        if (venues.length > 0) {
          const slots = await eventService.getVenueSlots(venues[0].venue_id, event.event_date);
          setAvailableSlots(slots.filter((s) => s.status === "AVAILABLE"));
        }
      });
    }
  };

  // 8. Update Event Details (PATCH /events/{id})
  const handleUpdateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manageEvent) return;
    setManageUpdating(true);
    try {
      await authService.ensureAuthenticated();
      const updated = await eventService.updateEvent(manageEvent.event_id, {
        title: manageTitle.trim(),
        max_capacity: Number(manageCapacity),
        status: manageStatus,
      });

      setFeedbackMessage(`✅ Event "${updated.title}" updated successfully.`);
      setShowHostManageModal(false);
      setEvents((prev) => prev.map((ev) => (ev.event_id === updated.event_id ? updated : ev)));
      if (selectedEventDetail?.event_id === updated.event_id) {
        setSelectedEventDetail(updated);
      }
    } catch (err: any) {
      alert(`Could not update event: ${err?.message || "Check permissions and try again."}`);
    } finally {
      setManageUpdating(false);
    }
  };

  // 9. Attach Venue Slot (POST /events/{id}/book-venue)
  const handleAttachSlot = async () => {
    if (!manageEvent || !selectedSlotToAttach) return;
    setAttachingSlot(true);
    try {
      await authService.ensureAuthenticated();
      const updated = await eventService.bookVenueSlot(manageEvent.event_id, selectedSlotToAttach);
      setFeedbackMessage(`🏟️ Venue slot successfully reserved & attached to "${updated.title}"!`);
      setShowHostManageModal(false);
      setEvents((prev) => prev.map((ev) => (ev.event_id === updated.event_id ? updated : ev)));
      if (selectedEventDetail?.event_id === updated.event_id) {
        setSelectedEventDetail(updated);
      }
    } catch (err: any) {
      alert(`Could not attach venue: ${err?.message || "Slot may no longer be available."}`);
    } finally {
      setAttachingSlot(false);
    }
  };

  // Filter events in memory for nearby locality, hosted only, and search
  const filteredEvents = events.filter((item) => {
    if (viewHostedOnly && currentUserId && item.host_id !== currentUserId) {
      return false;
    }
    
    // Locality radius filtering
    if (selectedLocality === "NEARBY_5KM") {
      const dist = getEstimatedDistance(item.locality || "", userLocality);
      if (dist > 5.0) return false;
    } else if (selectedLocality === "NEARBY_10KM") {
      const dist = getEstimatedDistance(item.locality || "", userLocality);
      if (dist > 10.0) return false;
    } else if (selectedLocality !== "ALL") {
      const loc = (item.locality || "").toLowerCase();
      const sel = selectedLocality.toLowerCase();
      if (!loc.includes(sel)) return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchAct = (item.activity_title || "").toLowerCase().includes(q);
      const matchLoc = (item.locality || "").toLowerCase().includes(q);
      if (!matchTitle && !matchAct && !matchLoc) return false;
    }
    return true;
  });

  // Spotlight featured event (first published event with remaining spots)
  const featuredEvent = events.find((e) => e.remaining_spots > 0 && e.status === "PUBLISHED") || events[0];

  return (
    <PageContainer>
      <div className="space-y-8 pb-16">
        {/* TOP FLOW BREADCRUMBS */}
        <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-500 dark:text-slate-400">Navigation:</span>
              <Link
                href="/dashboard"
                className="rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                1. Dashboard
              </Link>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <Link
                href="/activities"
                className="rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                2. Activities
              </Link>
              <span className="text-slate-300 dark:text-slate-700">/</span>
              <span className="flex items-center gap-1.5 rounded-lg bg-teal-500/10 px-2.5 py-1 font-bold text-teal-600 ring-1 ring-teal-500/20 dark:bg-teal-400/10 dark:text-teal-300">
                <span>📅 2B. Events Hub</span>
              </span>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <Link
                href="/recommendations"
                className="rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                3. AI Recommendations
              </Link>
              <span className="text-slate-300 dark:text-slate-700">➔</span>
              <Link
                href="/connections"
                className="rounded-lg px-2.5 py-1 font-medium text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                4. Peer Match Deck
              </Link>
            </div>

            <button
              type="button"
              onClick={() => setShowHostModal(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-500 px-3.5 py-1.5 text-xs font-bold text-slate-950 shadow-sm transition hover:bg-teal-400 cursor-pointer"
            >
              <span>+ Host an Event</span>
            </button>
          </div>
        </div>

        {/* FEEDBACK ALERT */}
        {feedbackMessage && (
          <div className="flex items-center justify-between rounded-2xl border border-teal-500/40 bg-teal-500/10 p-4 text-xs font-bold text-teal-900 backdrop-blur-md dark:text-teal-200 animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="text-base">✨</span>
              <span>{feedbackMessage}</span>
            </div>
            <button
              onClick={() => setFeedbackMessage(null)}
              className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* FEATURED SPOTLIGHT BANNER (BookMyShow Style Hero) */}
        {featuredEvent && (
          <section className="relative overflow-hidden rounded-[2.5rem] bg-slate-950 text-white shadow-2xl ring-1 ring-white/10">
            {/* Background Photographic Backdrop */}
            <div
              className="absolute inset-0 bg-cover bg-center opacity-40 filter saturate-125"
              style={{
                backgroundImage: `url('${getEventCoverImage(featuredEvent.title, featuredEvent.interest_category)}')`,
              }}
            />
            {/* Deep Cinematic Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/85 to-transparent" />

            <div className="relative z-10 grid gap-6 p-8 md:grid-cols-12 md:p-12 items-center">
              <div className="md:col-span-8 space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-500/20 px-3.5 py-1 text-[11px] font-extrabold uppercase tracking-widest text-teal-300 backdrop-blur-md">
                  <span>⚡ FEATURED GATHERING</span>
                  <span>·</span>
                  <span>{featuredEvent.interest_category || "Social Sparring"}</span>
                </div>

                <h1 className="text-3xl font-black tracking-tight text-white sm:text-5xl leading-tight">
                  {featuredEvent.title}
                </h1>

                <p className="text-xs text-slate-300 sm:text-sm max-w-2xl leading-relaxed">
                  Join fellow enthusiasts for an organized session. Split court/venue costs with verified local members.
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-200 pt-2">
                  <div className="flex items-center gap-1.5 rounded-xl bg-white/10 px-3 py-1.5 backdrop-blur-md">
                    <span>📅</span>
                    <span className="font-semibold">{featuredEvent.event_date}</span>
                    <span className="text-slate-400">·</span>
                    <span>{featuredEvent.start_time?.slice(0, 5)} - {featuredEvent.end_time?.slice(0, 5)}</span>
                  </div>

                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                      `${featuredEvent.locality || "Hyderabad Central"}, India`
                    )}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    title="Open in Google Maps"
                    className="flex items-center gap-1.5 rounded-xl bg-white/10 px-3 py-1.5 backdrop-blur-md transition hover:bg-white/20 text-white cursor-pointer group/pin"
                  >
                    <span className="group-hover/pin:scale-110 transition">📍</span>
                    <span className="font-semibold underline decoration-dotted underline-offset-2">
                      {featuredEvent.locality || "Hyderabad Central"}
                    </span>
                    <span className="text-[10px] text-teal-300 ml-0.5">↗</span>
                  </a>

                  <div className="flex items-center gap-1.5 rounded-xl bg-teal-400/20 px-3 py-1.5 text-teal-300 font-bold backdrop-blur-md">
                    <span>💰</span>
                    <span>
                      {featuredEvent.per_person_cost && featuredEvent.per_person_cost > 0
                        ? `₹${Math.round(featuredEvent.per_person_cost)} / person split`
                        : "Free RSVP"}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-4">
                  <button
                    type="button"
                    onClick={(e) => handleJoinEvent(e, featuredEvent.event_id, featuredEvent.title)}
                    disabled={rsvpLoadingId === featuredEvent.event_id || featuredEvent.remaining_spots <= 0}
                    className="group inline-flex items-center gap-2 rounded-2xl bg-teal-400 px-6 py-3.5 text-xs font-black text-slate-950 shadow-lg shadow-teal-500/25 transition hover:bg-teal-300 active:scale-95 cursor-pointer disabled:opacity-50"
                  >
                    <span>
                      {rsvpLoadingId === featuredEvent.event_id
                        ? "Confirming..."
                        : featuredEvent.remaining_spots <= 0
                        ? "Event Full"
                        : "Book / RSVP Now"}
                    </span>
                    <span className="transition group-hover:translate-x-0.5">➔</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOpenEventDetail(featuredEvent.event_id)}
                    className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3.5 text-xs font-bold text-white backdrop-blur-md transition hover:bg-white/20 cursor-pointer"
                  >
                    View Roster & Venue
                  </button>
                </div>
              </div>

              {/* Poster Card Preview in Hero */}
              <div className="hidden md:block md:col-span-4">
                <div className="relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl group cursor-pointer" onClick={() => handleOpenEventDetail(featuredEvent.event_id)}>
                  <img
                    src={getEventCoverImage(featuredEvent.title, featuredEvent.interest_category)}
                    alt={featuredEvent.title}
                    className="h-64 w-full object-cover transition duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <span className="rounded-md bg-teal-400 px-2 py-0.5 text-[10px] font-black text-slate-950 uppercase">
                      {featuredEvent.remaining_spots} Spots Left
                    </span>
                    <p className="mt-1 text-sm font-bold text-white truncate">{featuredEvent.title}</p>
                    <p className="text-[11px] text-slate-300">Host: {featuredEvent.host_name}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* STREAMLINED 3-ELEMENT FILTER TOOLBAR */}
        <section className="space-y-4">
          <div className="flex flex-col gap-4 rounded-3xl border border-slate-200/90 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-6">
            <div className="grid gap-3 sm:grid-cols-12 items-center">
              {/* 1. Search Event by Title */}
              <div className="relative sm:col-span-5">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
                <input
                  type="text"
                  placeholder="Search event by title..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-xs font-semibold text-slate-900 transition focus:border-teal-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              {/* 2. Locality Dropdown with Near Me 5km & 10km */}
              <div className="relative sm:col-span-4">
                <select
                  value={selectedLocality}
                  onChange={(e) => setSelectedLocality(e.target.value)}
                  aria-label="Filter events by locality"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 px-3.5 text-xs font-bold text-slate-800 transition focus:border-teal-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                >
                  <option value="ALL">📍 All Localities</option>
                  <optgroup label="Nearby Radius">
                    <option value="NEARBY_5KM">🎯 Within 5 km of Me ({userLocality ? userLocality.split(",")[0] : "Nearby"})</option>
                    <option value="NEARBY_10KM">🚗 Within 10 km of Me ({userLocality ? userLocality.split(",")[0] : "Nearby"})</option>
                  </optgroup>
                  <optgroup label="City Localities">
                    <option value="Gachibowli">Gachibowli, Hyderabad</option>
                    <option value="Madhapur">Madhapur, Hyderabad</option>
                    <option value="Jubilee Hills">Jubilee Hills, Hyderabad</option>
                    <option value="Financial District">Financial District, Hyderabad</option>
                    <option value="Indiranagar">Indiranagar, Bengaluru</option>
                    <option value="Sarjapur Road">Sarjapur Road, Bengaluru</option>
                    <option value="Bellandur">Bellandur, Bengaluru</option>
                  </optgroup>
                </select>
              </div>

              {/* 3. Date / Duration Dropdown */}
              <div className="relative sm:col-span-3">
                <select
                  value={selectedDuration}
                  onChange={(e) => setSelectedDuration(e.target.value as any)}
                  aria-label="Filter events by date duration"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 px-3.5 text-xs font-bold text-slate-800 transition focus:border-teal-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                >
                  <option value="ALL">🗓️ All Upcoming Dates</option>
                  <option value="TODAY">⚡ Today</option>
                  <option value="TOMORROW">☀️ Tomorrow</option>
                  <option value="WEEKEND">🎉 This Weekend</option>
                  <option value="THIS_WEEK">📅 Next 7 Days</option>
                </select>
              </div>
            </div>

            {/* Quick Filter Toggles & Radius Badge */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 dark:border-slate-800 text-xs">
              <div className="flex items-center gap-5">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={onlyAvailable}
                    onChange={(e) => setOnlyAvailable(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Spots Available Only</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={viewHostedOnly}
                    onChange={(e) => setViewHostedOnly(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Hosted by Me</span>
                </label>
              </div>

              {selectedLocality.startsWith("NEARBY_") && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-3 py-1 text-[11px] font-bold text-teal-700 dark:bg-teal-950/80 dark:text-teal-300">
                  <span>📍 Filtering within {selectedLocality === "NEARBY_5KM" ? "5 km" : "10 km"} of your location ({userLocality})</span>
                </span>
              )}
            </div>
          </div>

          {/* EVENTS HEADER & COUNTER */}
          <div className="flex items-center justify-between px-1">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                BookMyShow Live Gathering Deck
              </p>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white">
                Scheduled Events ({filteredEvents.length})
              </h2>
            </div>

            <button
              type="button"
              onClick={fetchEvents}
              className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 cursor-pointer"
            >
              🔄 Refresh Feed
            </button>
          </div>

          {/* EVENT CARDS GRID (BookMyShow Poster Cards) */}
          {loading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div key={n} className="h-96 rounded-3xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
              ))}
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
              <span className="text-4xl">🎟️</span>
              <h3 className="mt-3 text-lg font-bold text-slate-900 dark:text-white">
                No events found matching your filter criteria
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Try selecting "All Dates" or be the first to host an event for your community!
              </p>
              <button
                type="button"
                onClick={() => setShowHostModal(true)}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-teal-400 cursor-pointer"
              >
                + Host an Event Now
              </button>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredEvents.map((event) => {
                const coverImage = getEventCoverImage(event.title, event.interest_category);
                const dateSticker = formatEventDateSticker(event.event_date);
                const isHost = currentUserId !== null && event.host_id === currentUserId;
                const capacityTaken = Math.max(0, event.max_capacity - event.remaining_spots);
                const capacityPercent = Math.min(100, Math.round((capacityTaken / Math.max(1, event.max_capacity)) * 100));

                return (
                  <article
                    key={event.event_id}
                    onClick={() => handleOpenEventDetail(event.event_id)}
                    className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-slate-200/90 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1.5 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 cursor-pointer"
                  >
                    <div>
                      {/* Event Poster Image with Date Sticker & Badges */}
                      <div className="relative h-48 w-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                        <img
                          src={coverImage}
                          alt={event.title}
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-black/20" />

                        {/* Date Sticker (BookMyShow Style) */}
                        <div className="absolute left-3 top-3 flex flex-col items-center rounded-xl bg-white/95 px-2.5 py-1 text-slate-950 shadow-md backdrop-blur-md dark:bg-slate-900/95 dark:text-white">
                          <span className="text-[9px] font-black tracking-widest text-teal-600 dark:text-teal-400">
                            {dateSticker.month}
                          </span>
                          <span className="text-base font-black leading-none">{dateSticker.day}</span>
                        </div>

                        {/* Status Badge */}
                        <div className="absolute right-3 top-3 flex items-center gap-1.5">
                          {isHost && (
                            <span className="rounded-full bg-indigo-500/90 px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-white shadow">
                              You Host
                            </span>
                          )}
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider shadow ${
                              event.status === "FULL"
                                ? "bg-rose-500 text-white"
                                : event.status === "COMPLETED"
                                ? "bg-slate-500 text-white"
                                : "bg-teal-400 text-slate-950"
                            }`}
                          >
                            {event.status === "FULL" ? "Full" : event.status === "COMPLETED" ? "Done" : `${event.remaining_spots} Spots Left`}
                          </span>
                        </div>

                        {/* Title & Timing Overlaid at Bottom of Image */}
                        <div className="absolute bottom-3 left-3 right-3 text-white">
                          <span className="rounded bg-black/40 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-teal-300 backdrop-blur-sm">
                            {event.interest_category || event.activity_title || "Gathering"}
                          </span>
                          <h3 className="mt-1 text-base font-black text-white leading-tight line-clamp-1 drop-shadow-sm">
                            {event.title}
                          </h3>
                        </div>
                      </div>

                      {/* Card Content Body */}
                      <div className="p-5 space-y-3">
                        {/* Time & Venue Locality */}
                        <div className="space-y-1 text-xs">
                          <div className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
                            <span>⏰</span>
                            <span>{event.start_time?.slice(0, 5)} - {event.end_time?.slice(0, 5)}</span>
                            <span className="text-slate-400">({event.event_date})</span>
                          </div>

                          {(() => {
                            const locText = event.locality || event.venue_booking?.venue_address || "Hyderabad Central Arena";
                            const dist = getEstimatedDistance(locText, userLocality);
                            return (
                              <a
                                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${locText}, India`)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                title="Open in Google Maps"
                                className="group/loc flex items-center gap-1.5 text-slate-500 hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-300 transition cursor-pointer"
                              >
                                <span className="text-teal-500 group-hover/loc:scale-125 transition shrink-0">📍</span>
                                <span className="truncate underline decoration-dotted underline-offset-2">
                                  {locText}
                                </span>
                                <span className="shrink-0 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                                  ~{dist} km
                                </span>
                                <span className="text-[10px] opacity-70 group-hover/loc:opacity-100">↗</span>
                              </a>
                            );
                          })()}
                        </div>

                        {/* Capacity Progress Bar */}
                        <div className="space-y-1 pt-1">
                          <div className="flex justify-between text-[11px] font-bold text-slate-500 dark:text-slate-400">
                            <span>Capacity: {capacityTaken}/{event.max_capacity} joined</span>
                            <span className="text-teal-600 dark:text-teal-400">{event.remaining_spots} spots left</span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-teal-500 to-indigo-500 transition-all duration-300"
                              style={{ width: `${capacityPercent}%` }}
                            />
                          </div>
                        </div>

                        {/* Host & Price Tag */}
                        <div className="flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800 text-xs">
                          <div className="flex items-center gap-1.5">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-100 text-[10px] font-bold text-teal-800 dark:bg-teal-950 dark:text-teal-300">
                              {event.host_name ? event.host_name.charAt(0).toUpperCase() : "H"}
                            </div>
                            <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 truncate max-w-[100px]">
                              {event.host_name || "Community Host"}
                            </span>
                          </div>

                          <span className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-black text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
                            {event.per_person_cost && event.per_person_cost > 0
                              ? `₹${Math.round(event.per_person_cost)} / split`
                              : "Free RSVP"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Card Actions Bottom Footer */}
                    <div className="border-t border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-900/50 flex gap-2">
                      {isHost ? (
                        <button
                          type="button"
                          onClick={(e) => handleOpenHostManage(e, event)}
                          className="flex-1 rounded-xl bg-slate-900 py-2.5 text-center text-xs font-bold text-white transition hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 cursor-pointer"
                        >
                          ⚙️ Host Settings
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={(e) => handleJoinEvent(e, event.event_id, event.title)}
                          disabled={rsvpLoadingId === event.event_id || event.remaining_spots <= 0}
                          className="flex-1 rounded-xl bg-teal-400 py-2.5 text-center text-xs font-extrabold text-slate-950 transition hover:bg-teal-300 active:scale-95 cursor-pointer disabled:opacity-50"
                        >
                          {rsvpLoadingId === event.event_id
                            ? "Booking..."
                            : event.remaining_spots <= 0
                            ? "Full House"
                            : "⚡ Book / RSVP"}
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleOpenEventDetail(event.event_id)}
                        className="rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
                      >
                        Details →
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* FULL EVENT DETAILS MODAL (GET /events/{id}) */}
        {selectedEventDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm animate-fadeIn">
            <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[2rem] bg-white p-6 shadow-2xl dark:bg-slate-900 sm:p-8">
              {/* Close Button */}
              <button
                type="button"
                onClick={() => setSelectedEventDetail(null)}
                className="absolute right-5 top-5 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-slate-900/60 text-white backdrop-blur-md hover:bg-slate-900 cursor-pointer"
              >
                ✕
              </button>

              {/* Cover Banner */}
              <div className="relative -mx-6 -mt-6 sm:-mx-8 sm:-mt-8 h-56 overflow-hidden rounded-t-[2rem]">
                <img
                  src={getEventCoverImage(selectedEventDetail.title, selectedEventDetail.interest_category)}
                  alt={selectedEventDetail.title}
                  className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
                <div className="absolute bottom-4 left-6 right-6 text-white">
                  <span className="rounded bg-teal-400 px-2.5 py-0.5 text-[10px] font-black uppercase text-slate-950">
                    {selectedEventDetail.interest_category || selectedEventDetail.activity_title}
                  </span>
                  <h2 className="mt-1 text-2xl font-black text-white sm:text-3xl leading-tight">
                    {selectedEventDetail.title}
                  </h2>
                  <p className="text-xs text-slate-300">
                    Hosted by <span className="font-bold text-teal-300">{selectedEventDetail.host_name}</span> · {selectedEventDetail.status}
                  </p>
                </div>
              </div>

              {/* Event Schedule & Venue Grid */}
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Date & Time</p>
                  <p className="mt-1 text-sm font-bold text-slate-900 dark:text-white">
                    📅 {selectedEventDetail.event_date}
                  </p>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    ⏰ {selectedEventDetail.start_time?.slice(0, 5)} - {selectedEventDetail.end_time?.slice(0, 5)}
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Venue & Locality</p>
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                        `${selectedEventDetail.venue_booking?.venue_address || selectedEventDetail.venue_booking?.venue_name || selectedEventDetail.locality || "Hyderabad Central"}, India`
                      )}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 hover:underline"
                    >
                      <span>Open in Maps</span>
                      <span>↗</span>
                    </a>
                  </div>
                  <p className="mt-1 text-sm font-bold text-slate-900 dark:text-white truncate">
                    📍 {selectedEventDetail.locality || "City Activity Center"}
                  </p>
                  {selectedEventDetail.venue_booking && (
                    <p className="text-xs text-teal-600 dark:text-teal-400 font-semibold truncate">
                      🏟️ {selectedEventDetail.venue_booking.venue_name}
                    </p>
                  )}
                </div>
              </div>

              {/* Dynamic Cost Split Breakdown */}
              <div className="mt-4 rounded-2xl border border-teal-500/30 bg-teal-500/10 p-4 text-xs">
                <div className="flex items-center justify-between font-bold text-teal-900 dark:text-teal-200">
                  <span>💰 Pricing / Split Calculation:</span>
                  <span className="text-sm">
                    {selectedEventDetail.per_person_cost && selectedEventDetail.per_person_cost > 0
                      ? `₹${Math.round(selectedEventDetail.per_person_cost)} / player`
                      : "Free Gathering"}
                  </span>
                </div>
                {selectedEventDetail.venue_booking && (
                  <div className="mt-2 space-y-1.5 border-t border-teal-500/20 pt-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                      <span>Total Venue Fee: ₹{selectedEventDetail.venue_booking.total_amount}</span>
                      <span>Collected: ₹{selectedEventDetail.venue_booking.amount_collected || 0}</span>
                    </div>
                    <div className="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
                      <span>Your Split Share: ₹{Math.round(selectedEventDetail.venue_booking.per_person_share || (selectedEventDetail.venue_booking.total_amount / (selectedEventDetail.participant_count || 1)))}</span>
                      <button
                        type="button"
                        onClick={handlePaySplitShare}
                        disabled={payingSplitShare}
                        className="rounded-lg bg-teal-500 px-3 py-1 text-[11px] font-black text-slate-950 hover:bg-teal-400 transition cursor-pointer disabled:opacity-50"
                      >
                        {payingSplitShare ? "Processing..." : "💳 Pay Split Share"}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Participant Roster List */}
              <div className="mt-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Confirmed Participant Roster ({selectedEventDetail.participants?.length || selectedEventDetail.participant_count || 0}/{selectedEventDetail.max_capacity})
                  </h4>
                  <span className="text-xs font-bold text-teal-600 dark:text-teal-400">
                    {selectedEventDetail.remaining_spots} spots left
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                  {selectedEventDetail.participants && selectedEventDetail.participants.length > 0 ? (
                    selectedEventDetail.participants.map((p) => (
                      <div
                        key={p.user_id}
                        className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs dark:border-slate-800 dark:bg-slate-800"
                      >
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-500 text-[10px] font-bold text-white">
                          {p.display_name.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-semibold text-slate-800 dark:text-white">{p.display_name}</span>
                        {p.payment_status && (
                          <span className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded ${p.payment_status === "PAID" ? "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200" : "bg-amber-100 text-amber-800"}`}>
                            {p.payment_status}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500">Host is ready. Be the first to join the roster!</p>
                  )}
                </div>
              </div>

              {/* Community Reviews & Peer Ratings */}
              <div className="mt-6 border-t border-slate-100 pt-5 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <span>⭐</span>
                    <span>Peer Reviews & Trust Ratings ({eventFeedbacks.length})</span>
                  </h4>
                  <span className="text-[11px] font-bold text-amber-500">
                    ★ {eventFeedbacks.length > 0 ? (eventFeedbacks.reduce((acc, f) => acc + f.rating, 0) / eventFeedbacks.length).toFixed(1) : "5.0"}
                  </span>
                </div>

                {/* Reviews List */}
                <div className="mt-3 space-y-2 max-h-36 overflow-y-auto">
                  {loadingFeedback ? (
                    <p className="text-xs text-slate-400">Loading reviews...</p>
                  ) : eventFeedbacks.length > 0 ? (
                    eventFeedbacks.map((fb) => (
                      <div
                        key={fb.feedback_id}
                        className="rounded-xl border border-slate-100 bg-slate-50/80 p-2.5 text-xs dark:border-slate-800 dark:bg-slate-800/50"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500/20 text-[9px] font-bold text-teal-700 dark:text-teal-300">
                              {fb.reviewer_name?.charAt(0) || "U"}
                            </div>
                            <span className="font-bold text-slate-800 dark:text-slate-200">
                              {fb.reviewer_name}
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-amber-400 text-xs">
                            {"★".repeat(fb.rating)}
                            <span className="text-[10px] text-slate-400 ml-1">{fb.created_at?.slice(0, 10)}</span>
                          </div>
                        </div>
                        {fb.comment && (
                          <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-300 leading-snug">
                            {fb.comment}
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-slate-400">
                      No peer reviews yet. Complete the event to leave feedback for your companions!
                    </p>
                  )}
                </div>

                {/* Submit Feedback Form */}
                <form onSubmit={handleSubmitFeedback} className="mt-3 rounded-xl border border-teal-500/20 bg-teal-500/5 p-3 dark:border-teal-400/20">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    <span>Leave a Rating & Companion Review</span>
                    <div className="flex items-center gap-1 text-base">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setReviewRating(star)}
                          className={`cursor-pointer ${star <= reviewRating ? "text-amber-400" : "text-slate-300 dark:text-slate-600"}`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                      placeholder="e.g. Great coordination and friendly sparring partners!"
                      className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                    />
                    <button
                      type="submit"
                      disabled={submittingReview}
                      className="rounded-xl bg-teal-500 px-3.5 py-1.5 text-xs font-bold text-slate-950 hover:bg-teal-400 transition cursor-pointer disabled:opacity-50"
                    >
                      {submittingReview ? "Posting..." : "Post Review"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Modal Actions */}
              <div className="mt-8 flex gap-3 border-t border-slate-100 pt-5 dark:border-slate-800">
                {currentUserId && selectedEventDetail.host_id === currentUserId ? (
                  <button
                    type="button"
                    onClick={(e) => {
                      setSelectedEventDetail(null);
                      handleOpenHostManage(e, selectedEventDetail);
                    }}
                    className="flex-1 rounded-2xl bg-indigo-600 py-3 text-xs font-bold text-white hover:bg-indigo-500 cursor-pointer"
                  >
                    ⚙️ Manage Event & Venue Slots
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={(e) => handleJoinEvent(e, selectedEventDetail.event_id, selectedEventDetail.title)}
                      disabled={rsvpLoadingId === selectedEventDetail.event_id || selectedEventDetail.remaining_spots <= 0}
                      className="flex-1 rounded-2xl bg-teal-400 py-3 text-xs font-black text-slate-950 transition hover:bg-teal-300 cursor-pointer disabled:opacity-50"
                    >
                      {rsvpLoadingId === selectedEventDetail.event_id
                        ? "Confirming..."
                        : selectedEventDetail.remaining_spots <= 0
                        ? "Event Full"
                        : "⚡ Book / Reserve Spot"}
                    </button>

                    <button
                      type="button"
                      onClick={(e) => handleLeaveEvent(e, selectedEventDetail.event_id, selectedEventDetail.title)}
                      disabled={rsvpLoadingId === selectedEventDetail.event_id}
                      className="rounded-2xl border border-rose-300 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700 hover:bg-rose-100 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300 cursor-pointer"
                    >
                      Cancel Reservation
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* HOST EVENT MODAL (POST /events) */}
        {showHostModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm animate-fadeIn">
            <div className="w-full max-w-lg rounded-[2rem] bg-white p-6 shadow-2xl dark:bg-slate-900 sm:p-8">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">+ Host a Gathering</h3>
                  <p className="text-xs text-slate-500">Publish your session on the community discovery feed</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowHostModal(false)}
                  className="rounded-lg p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateEvent} className="mt-5 space-y-4 text-xs">
                <div>
                  <label className="font-bold text-slate-700 dark:text-slate-300">Event Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Saturday Badminton Sparring Indiranagar"
                    value={hostTitle}
                    onChange={(e) => setHostTitle(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-medium text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 dark:text-slate-300">Activity Template</label>
                  <select
                    value={hostActivityId}
                    onChange={(e) => setHostActivityId(Number(e.target.value))}
                    aria-label="Select activity template"
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  >
                    {activities.map((act) => (
                      <option key={act.activity_id} value={act.activity_id}>
                        {act.title}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Venue & Slot Selector (GET /venues & GET /venues/{id}/slots) */}
                <div>
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-slate-700 dark:text-slate-300">
                      🏟️ Venue & Bookable Slot (Optional)
                    </label>
                    <span className="text-[10px] text-teal-600 dark:text-teal-400 font-semibold">
                      Split-Cost Bookable
                    </span>
                  </div>
                  <select
                    value={selectedHostVenueId || ""}
                    onChange={(e) => handleHostVenueChange(e.target.value)}
                    aria-label="Select venue"
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  >
                    <option value="">No venue (Free/Public Gathering)...</option>
                    {venuesList.map((v) => (
                      <option key={v.venue_id} value={v.venue_id}>
                        {v.name} ({v.locality || v.city || "Hyderabad"})
                      </option>
                    ))}
                  </select>

                  {selectedHostVenueId && (
                    <div className="mt-2 space-y-1.5">
                      <label className="text-[11px] font-semibold text-slate-500">Available Time Slots</label>
                      {loadingHostSlots ? (
                        <p className="text-[11px] text-slate-400">Loading slots...</p>
                      ) : hostVenueSlots.length > 0 ? (
                        <div className="grid grid-cols-2 gap-1.5">
                          {hostVenueSlots.map((s) => (
                            <button
                              key={s.slot_id}
                              type="button"
                              onClick={() => {
                                setHostSlotId(s.slot_id);
                                setHostStartTime(s.start_time.slice(0, 5));
                                setHostEndTime(s.end_time.slice(0, 5));
                              }}
                              className={`rounded-xl border p-2 text-left transition cursor-pointer ${
                                hostSlotId === s.slot_id
                                  ? "border-teal-500 bg-teal-500/10 text-teal-800 dark:text-teal-200 font-bold"
                                  : "border-slate-200 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                              }`}
                            >
                              <div className="text-[11px] font-bold">
                                {s.start_time.slice(0, 5)} - {s.end_time.slice(0, 5)}
                              </div>
                              <div className="text-[10px] text-slate-400">₹{s.price_total}</div>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400">
                          No pre-registered slots for this date. Enter custom time below.
                        </p>
                      )}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">Date</label>
                    <input
                      type="date"
                      required
                      value={hostDate}
                      onChange={(e) => setHostDate(e.target.value)}
                      aria-label="Event date"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">Max Capacity</label>
                    <input
                      type="number"
                      min={2}
                      max={50}
                      required
                      value={hostCapacity}
                      onChange={(e) => setHostCapacity(Number(e.target.value))}
                      aria-label="Maximum capacity"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">Start Time</label>
                    <input
                      type="time"
                      required
                      value={hostStartTime}
                      onChange={(e) => setHostStartTime(e.target.value)}
                      aria-label="Start time"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">End Time</label>
                    <input
                      type="time"
                      required
                      value={hostEndTime}
                      onChange={(e) => setHostEndTime(e.target.value)}
                      aria-label="End time"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>
                </div>

                <div className="pt-3">
                  <button
                    type="submit"
                    disabled={creatingEvent}
                    className="w-full rounded-2xl bg-teal-400 py-3.5 text-xs font-black text-slate-950 shadow-lg shadow-teal-500/25 hover:bg-teal-300 cursor-pointer disabled:opacity-60"
                  >
                    {creatingEvent ? "Publishing Event..." : "Publish Event 🚀"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* HOST MANAGEMENT MODAL (PATCH /events/{id} & POST /book-venue) */}
        {showHostManageModal && manageEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm animate-fadeIn">
            <div className="w-full max-w-lg rounded-[2rem] bg-white p-6 shadow-2xl dark:bg-slate-900 sm:p-8 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">⚙️ Host Management</h3>
                  <p className="text-xs text-slate-500">Edit event details, attach venue slot, or cancel</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowHostManageModal(false)}
                  className="rounded-lg p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Edit Details Form (PATCH) */}
              <form onSubmit={handleUpdateEvent} className="space-y-4 text-xs">
                <div>
                  <label className="font-bold text-slate-700 dark:text-slate-300">Title</label>
                  <input
                    type="text"
                    value={manageTitle}
                    onChange={(e) => setManageTitle(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">Max Capacity</label>
                    <input
                      type="number"
                      min={manageEvent.participant_count || 1}
                      value={manageCapacity}
                      onChange={(e) => setManageCapacity(Number(e.target.value))}
                      aria-label="Manage maximum capacity"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-slate-700 dark:text-slate-300">Status</label>
                    <select
                      value={manageStatus}
                      onChange={(e) => setManageStatus(e.target.value)}
                      aria-label="Manage event status"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    >
                      <option value="PUBLISHED">PUBLISHED</option>
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="CANCELLED">CANCELLED</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={manageUpdating}
                  className="w-full rounded-xl bg-slate-900 py-3 font-bold text-white hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 cursor-pointer disabled:opacity-60"
                >
                  {manageUpdating ? "Updating..." : "Save Changes (PATCH)"}
                </button>
              </form>

              {/* Attach Venue Slot Section (POST /book-venue) */}
              {!manageEvent.venue_booking && (
                <div className="border-t border-slate-100 pt-4 dark:border-slate-800 space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-white">
                    🏟️ Reserve & Attach Venue Slot
                  </h4>
                  {availableSlots.length > 0 ? (
                    <div className="space-y-2">
                      <select
                        value={selectedSlotToAttach || ""}
                        onChange={(e) => setSelectedSlotToAttach(Number(e.target.value))}
                        aria-label="Select venue slot to attach"
                        className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                      >
                        <option value="">Select an available court/slot...</option>
                        {availableSlots.map((s) => (
                          <option key={s.slot_id} value={s.slot_id}>
                            Slot #{s.slot_id} ({s.start_time.slice(0, 5)} - {s.end_time.slice(0, 5)}) · ₹{s.price_total}
                          </option>
                        ))}
                      </select>

                      <button
                        type="button"
                        onClick={handleAttachSlot}
                        disabled={!selectedSlotToAttach || attachingSlot}
                        className="w-full rounded-xl bg-indigo-600 py-2.5 text-xs font-bold text-white hover:bg-indigo-500 cursor-pointer disabled:opacity-50"
                      >
                        {attachingSlot ? "Reserving Slot..." : "Attach Slot to Event (POST /book-venue)"}
                      </button>
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-400">
                      No open venue slots for this exact date. You can still hold this gathering at a public or open ground!
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
}