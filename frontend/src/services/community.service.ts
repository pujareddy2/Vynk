import { fetchApi } from "./api";

export interface Community {
  community_id: number;
  name: string;
  description?: string;
  created_by?: number;
  member_count: number;
  created_at?: string;
  locality?: string;
  category?: string;
}

export interface CommunityCreatePayload {
  name: string;
  description?: string;
  initial_member_ids?: number[];
}

export interface CommunityHealthResponse {
  community_id: number;
  member_count: number;
  active_member_count: number;
  events_created: number;
  completed_events: number;
  recent_event_count: number;
  average_event_participation: number;
  average_feedback_rating: number;
  health_score: number;
  health_status: string;
}

export interface CommunityLifecycleInsightResponse {
  community_id: number;
  health_score: number;
  health_status: string;
  trend: string;
  score_change: number;
  lifecycle_stage: string;
  insight: string;
  recommended_focus: string;
}

export interface CommunityActionRecommendationItem {
  priority: string;
  action: string;
  title: string;
  reason: string;
  suggested_next_step: string;
}

export interface CommunityActionRecommendationsResponse {
  community_id: number;
  recommendations: CommunityActionRecommendationItem[];
}

export interface CommunityProposalItem {
  community_type: string;
  theme: string;
  activity: string;
  activity_id?: number;
  interest_id?: number;
  locality: string;
  member_candidates: number;
  candidate_user_ids: number[];
  recurring_pattern: string;
  day_of_week?: string;
  time_window?: string;
  compatibility_score: number;
  community_opportunity_score: number;
  suggested_action: string;
  action_payload?: {
    name?: string;
    description?: string;
    initial_member_ids?: number[];
  };
  reasons: string[];
  existing_community_id?: number;
}

export interface CommunityIntelligenceResponse {
  total_proposals: number;
  locality_filter?: string;
  proposals: CommunityProposalItem[];
}

export const communityService = {
  async getCommunities(): Promise<Community[]> {
    return await fetchApi<Community[]>("/communities");
  },

  async createCommunity(payload: CommunityCreatePayload): Promise<Community> {
    return await fetchApi<Community>("/communities", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async joinCommunity(communityId: number): Promise<{ message: string; community_id: number }> {
    return await fetchApi(`/communities/${communityId}/join`, {
      method: "POST",
    });
  },

  async getCommunityHealth(communityId: number): Promise<CommunityHealthResponse> {
    return await fetchApi<CommunityHealthResponse>(`/communities/${communityId}/health`);
  },

  async getCommunityLifecycle(communityId: number): Promise<CommunityLifecycleInsightResponse> {
    return await fetchApi<CommunityLifecycleInsightResponse>(`/communities/${communityId}/lifecycle`);
  },

  async getCommunityRecommendations(communityId: number): Promise<CommunityActionRecommendationsResponse> {
    return await fetchApi<CommunityActionRecommendationsResponse>(`/communities/${communityId}/recommendations`);
  },

  async getCommunityIntelligence(locality?: string): Promise<CommunityIntelligenceResponse> {
    const q = locality ? `?locality=${encodeURIComponent(locality)}` : "";
    return await fetchApi<CommunityIntelligenceResponse>(`/ai/community-intelligence${q}`);
  },
};

export default communityService;