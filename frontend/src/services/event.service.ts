import { fetchApi } from "./api";

export interface ParticipantRosterItem {
  user_id: number;
  display_name: string;
  avatar_url?: string | null;
  status: string;
  payment_status?: string | null;
  paid_amount?: number | null;
  joined_at: string;
}

export interface VenueBookingDetail {
  booking_id: number;
  event_id: number;
  slot_id: number;
  venue_id: number;
  venue_name: string;
  venue_address: string;
  slot_date: string;
  start_time: string;
  end_time: string;
  booked_by: number;
  total_amount: number;
  currency: string;
  status: string;
  amount_collected: number;
  per_person_share: number;
  created_at: string;
}

export interface EventItem {
  event_id: number;
  activity_id: number;
  activity_title: string;
  interest_name?: string | null;
  interest_category?: string | null;
  host_id: number;
  host_name: string;
  title: string;
  event_date: string;
  start_time: string;
  end_time: string;
  max_capacity: number;
  participant_count: number;
  remaining_spots: number;
  per_person_cost?: number | null;
  cost_per_person?: number | null;
  locality?: string | null;
  status: "PUBLISHED" | "FULL" | "COMPLETED" | "CANCELLED" | string;
  venue_booking?: VenueBookingDetail | null;
  participants?: ParticipantRosterItem[];
  created_at?: string;
}

export interface EventCreatePayload {
  activity_id: number;
  title: string;
  event_date: string;
  start_time: string;
  end_time: string;
  max_capacity: number;
  slot_id?: number | null;
}

export interface EventUpdatePayload {
  title?: string;
  event_date?: string;
  start_time?: string;
  end_time?: string;
  max_capacity?: number;
  status?: string;
}

export interface EventFilterParams {
  activity_id?: number;
  interest_id?: number;
  locality?: string;
  event_date?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  available_only?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface VenueSlotItem {
  slot_id: number;
  venue_id: number;
  slot_date: string;
  start_time: string;
  end_time: string;
  price_total: number;
  currency: string;
  status: string;
}

export interface EventFeedbackItem {
  feedback_id: number;
  event_id: number;
  reviewer_id: number;
  reviewer_name: string;
  reviewer_avatar?: string | null;
  rating: number;
  comment?: string | null;
  created_at: string;
}

export interface SplitPaymentResponse {
  payment_id: number;
  booking_id: number;
  user_id: number;
  amount: number;
  currency: string;
  status: string;
  paid_at?: string;
}

export interface VenueItem {
  venue_id: number;
  name: string;
  description?: string;
  address?: string;
  locality?: string;
  city?: string;
  contact_phone?: string;
  rating?: number;
  price_per_hour?: number;
}

export const eventService = {
  async getEvents(params?: EventFilterParams): Promise<EventItem[]> {
    const q = new URLSearchParams();
    if (params?.activity_id) q.set("activity_id", String(params.activity_id));
    if (params?.interest_id) q.set("interest_id", String(params.interest_id));
    if (params?.locality) q.set("locality", params.locality);
    if (params?.event_date) q.set("event_date", params.event_date);
    if (params?.date_from) q.set("date_from", params.date_from);
    if (params?.date_to) q.set("date_to", params.date_to);
    if (params?.status) q.set("status", params.status);
    if (params?.available_only) q.set("available_only", "true");
    if (params?.search) q.set("search", params.search);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    
    const qs = q.toString();
    return await fetchApi<EventItem[]>(qs ? `/events?${qs}` : "/events");
  },

  async getEvent(eventId: number): Promise<EventItem> {
    return await fetchApi<EventItem>(`/events/${eventId}`);
  },

  async createEvent(payload: EventCreatePayload): Promise<EventItem> {
    return await fetchApi<EventItem>("/events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateEvent(eventId: number, payload: EventUpdatePayload): Promise<EventItem> {
    return await fetchApi<EventItem>(`/events/${eventId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async joinEvent(eventId: number): Promise<EventItem> {
    return await fetchApi<EventItem>(`/events/${eventId}/join`, {
      method: "POST",
    });
  },

  async leaveEvent(eventId: number): Promise<EventItem> {
    return await fetchApi<EventItem>(`/events/${eventId}/leave`, {
      method: "POST",
    });
  },

  async bookVenueSlot(eventId: number, slotId: number): Promise<EventItem> {
    return await fetchApi<EventItem>(`/events/${eventId}/book-venue`, {
      method: "POST",
      body: JSON.stringify({ slot_id: slotId }),
    });
  },

  async payEventSplitShare(eventId: number, amount?: number): Promise<SplitPaymentResponse> {
    return await fetchApi<SplitPaymentResponse>(`/events/${eventId}/pay`, {
      method: "POST",
      body: JSON.stringify(amount ? { amount } : {}),
    });
  },

  async getVenues(locality?: string, limit = 50): Promise<VenueItem[]> {
    const q = new URLSearchParams();
    if (locality) q.set("locality", locality);
    q.set("limit", String(limit));
    return await fetchApi<VenueItem[]>(`/venues?${q.toString()}`);
  },

  async getVenueSlots(venueId: number, dateStr?: string): Promise<VenueSlotItem[]> {
    const q = new URLSearchParams();
    if (dateStr) q.set("slot_date", dateStr);
    const qs = q.toString();
    return await fetchApi<VenueSlotItem[]>(qs ? `/venues/${venueId}/slots?${qs}` : `/venues/${venueId}/slots`);
  },

  async getEventFeedback(eventId: number): Promise<EventFeedbackItem[]> {
    try {
      return await fetchApi<EventFeedbackItem[]>(`/events/${eventId}/feedback`);
    } catch {
      return [];
    }
  },

  async submitEventFeedback(eventId: number, rating: number, comment?: string): Promise<EventFeedbackItem> {
    return await fetchApi<EventFeedbackItem>(`/events/${eventId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ rating, comment }),
    });
  },
};

export default eventService;