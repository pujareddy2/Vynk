import { fetchApi } from "./api";

export interface PeopleMatchCandidate {
  user_id: number;
  display_name: string;
  avatar_url?: string;
  approx_locality?: string;
  match_score: number;
  deterministic_score?: number;
  semantic_similarity?: number;
  trust_score?: number;
  match_breakdown?: Record<string, any>;
  match_reasons?: string[];
  shared_interests?: string[];
  relevant_skills?: string[];
  shared_availability?: string[];
}

export interface PeopleMatchResponse {
  total_candidates: number;
  activity_id?: number;
  activity_title?: string;
  target_interest?: string;
  matches: PeopleMatchCandidate[];
}

export interface GroupProposalMember {
  user_id: number;
  display_name: string;
  avatar_url?: string;
  approx_locality?: string;
  compatibility_score: number;
  status: "ACCEPTED" | "INVITED" | "PENDING" | "DECLINED" | string;
  invited_at?: string;
  responded_at?: string | null;
}

export interface GroupProposal {
  proposal_id: number;
  title: string;
  description?: string;
  activity_id?: number;
  activity_title?: string;
  initiator_user_id: number;
  initiator_name?: string;
  status: "PROPOSED" | "CONFIRMED" | "CANCELLED" | "CONVERTED_TO_EVENT" | "EXPIRED" | string;
  target_size: number;
  min_required_size: number;
  proposed_date: string;
  proposed_start_time: string;
  proposed_end_time: string;
  target_locality: string;
  suggested_venue_id?: number;
  suggested_venue_name?: string;
  estimated_cost_per_person?: number;
  members: GroupProposalMember[];
  converted_event_id?: number | null;
  expires_at?: string;
  created_at?: string;
}

export const matchingService = {
  async getMatches(params?: {
    min_score?: number;
    locality?: string;
    day_of_week?: string;
    search?: string;
    query?: string;
  }): Promise<PeopleMatchResponse> {
    const query = new URLSearchParams();
    if (params?.min_score !== undefined) query.set("min_score", params.min_score.toString());
    if (params?.locality) query.set("locality", params.locality);
    if (params?.day_of_week) query.set("day_of_week", params.day_of_week);
    if (params?.search) query.set("search", params.search);
    if (params?.query) query.set("query", params.query);

    const queryString = query.toString();
    const endpoint = queryString ? `/matches?${queryString}` : "/matches";
    return await fetchApi<PeopleMatchResponse>(endpoint);
  },

  async getPeopleMatches(): Promise<PeopleMatchResponse> {
    return await fetchApi<PeopleMatchResponse>("/matches/people");
  },

  async proposeAiGroup(query: string): Promise<GroupProposal> {
    return await fetchApi<GroupProposal>("/ai/groups/propose", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
  },

  async getMyProposals(): Promise<GroupProposal[]> {
    return await fetchApi<GroupProposal[]>("/groups/proposals/me");
  },

  async respondToProposal(
    proposalId: number,
    response: "ACCEPTED" | "DECLINED"
  ): Promise<{ status: string; message: string }> {
    return await fetchApi<{ status: string; message: string }>(
      `/groups/proposals/${proposalId}/respond`,
      {
        method: "POST",
        body: JSON.stringify({ response }),
      }
    );
  },

  async convertProposalToEvent(proposalId: number): Promise<any> {
    return await fetchApi<any>(`/groups/proposals/${proposalId}/convert`, {
      method: "POST",
    });
  },
};

export default matchingService;