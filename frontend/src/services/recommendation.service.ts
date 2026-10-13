import { fetchApi } from "./api";

export interface RecommendationItem {
  id: number;
  type: "EVENT" | "ACTIVITY" | "PEOPLE" | string;
  title: string;
  score: number;
  reasons: string[];
  locality?: string | null;
  event_id?: number | null;
  activity_id?: number | null;
  user_id?: number | null;
  event_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  remaining_spots?: number | null;
  per_person_cost?: number | null;
  trust_score?: number | null;
  reputation?: {
    average_rating?: number;
    total_reviews?: number;
    completed_events?: number;
  } | null;
}

export interface RecommendationResponse {
  total_recommendations: number;
  user_locality?: string | null;
  recommendations: RecommendationItem[];
}

export interface DoSomethingNowOption {
  type: "EVENT" | "ACTIVITY" | string;
  action: "JOIN" | "CREATE" | "FULL" | string;
  title: string;
  score: number;
  feasible: boolean;
  reason: string;
  reasons: string[];
  event_id?: number | null;
  activity_id?: number | null;
  interest_id?: number | null;
  interest_name?: string | null;
  locality?: string | null;
  event_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  remaining_spots?: number | null;
  cost_per_person?: number | null;
  available_peers_count?: number;
  available_venues_count?: number;
  suggested_slot_id?: number | null;
  suggested_venue_name?: string | null;
}

export interface DoSomethingNowResponse {
  target_date: string;
  target_time: string;
  day_name?: string;
  day_of_week?: string;
  user_locality?: string | null;
  user_available_now: boolean;
  total_options: number;
  feasible_count?: number;
  options: DoSomethingNowOption[];
}

export interface DemandRadarItem {
  activity: string;
  activity_id?: number | null;
  interest_id?: number | null;
  category?: string | null;
  locality: string;
  preferred_day: string;
  preferred_time: string;
  interested_users: number;
  active_events: number;
  available_spots: number;
  estimated_unmet_demand: number;
  demand_score: number;
  status: "HIGH_DEMAND" | "MODERATE_DEMAND" | "BALANCED" | "EMERGING_DEMAND" | "LOW_DEMAND" | string;
  suggested_action?: string | null;
}

export interface DemandRadarResponse {
  total_clusters: number;
  locality_filter?: string | null;
  clusters: DemandRadarItem[];
}

export interface OpportunityItem {
  opportunity_id?: number;
  activity_name: string;
  activity_id?: number;
  category?: string;
  locality: string;
  day: string;
  time: string;
  demand_score: number;
  feasibility_score: number;
  expected_participants: string;
  recommended_capacity: number;
  venue_available: boolean;
  suggested_venue_id?: number | null;
  suggested_venue_name?: string | null;
  suggested_price_per_person: number;
  opportunity_score: number;
  action: string;
  action_payload?: any;
  reasons: string[];
}

export interface OpportunitiesResponse {
  total_opportunities: number;
  locality_filter?: string | null;
  opportunities: OpportunityItem[];
}

export const recommendationService = {
  async getRecommendations(params?: {
    type?: string;
    locality?: string;
    min_score?: number;
    limit?: number;
  }): Promise<RecommendationResponse> {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.locality) q.set("locality", params.locality);
    if (params?.min_score !== undefined) q.set("min_score", String(params.min_score));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    const qs = q.toString();
    return await fetchApi(qs ? `/recommendations?${qs}` : "/recommendations");
  },

  async getDoSomethingNow(params?: {
    target_date?: string;
    target_time?: string;
    locality?: string;
    interest_id?: number;
    limit?: number;
  }): Promise<DoSomethingNowResponse> {
    const q = new URLSearchParams();
    if (params?.target_date) q.set("target_date", params.target_date);
    if (params?.target_time) q.set("target_time", params.target_time);
    if (params?.locality) q.set("locality", params.locality);
    if (params?.interest_id) q.set("interest_id", String(params.interest_id));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    const qs = q.toString();
    return await fetchApi(qs ? `/do-something-now?${qs}` : "/do-something-now");
  },

  async getDemandRadar(params?: {
    locality?: string;
    activity?: string;
    day_of_week?: string;
    min_demand_score?: number;
    limit?: number;
  }): Promise<DemandRadarResponse> {
    const q = new URLSearchParams();
    if (params?.locality) q.set("locality", params.locality);
    if (params?.activity) q.set("activity", params.activity);
    if (params?.day_of_week) q.set("day_of_week", params.day_of_week);
    if (params?.min_demand_score !== undefined) q.set("min_demand_score", String(params.min_demand_score));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    const qs = q.toString();
    return await fetchApi(qs ? `/ai/demand-radar?${qs}` : "/ai/demand-radar");
  },

  async getOpportunities(params?: {
    locality?: string;
    activity?: string;
    day?: string;
    min_opportunity_score?: number;
    limit?: number;
  }): Promise<OpportunitiesResponse> {
    const q = new URLSearchParams();
    if (params?.locality) q.set("locality", params.locality);
    if (params?.activity) q.set("activity", params.activity);
    if (params?.day) q.set("day", params.day);
    if (params?.min_opportunity_score !== undefined) q.set("min_opportunity_score", String(params.min_opportunity_score));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    const qs = q.toString();
    return await fetchApi(qs ? `/ai/opportunities?${qs}` : "/ai/opportunities");
  },
};

export default recommendationService;