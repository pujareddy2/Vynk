import { fetchApi } from "./api";

export interface MasterInterest {
  interest_id: number;
  name: string;
  category: string;
}

export interface MasterSkill {
  skill_id: number;
  name: string;
  category: string;
}

export interface UserSkillItem {
  skill_id: number;
  skill_level: string;
  is_offering: boolean;
  name?: string;
  category?: string;
}

export interface UserAvailabilityItem {
  day_of_week: string;
  start_time?: string;
  end_time?: string;
}

export interface FullProfile {
  user_id: number;
  email: string;
  display_name: string;
  bio?: string;
  avatar_url?: string;
  approx_locality?: string;
  budget_preference?: string;
  interests?: MasterInterest[];
  skills?: UserSkillItem[];
  availability?: UserAvailabilityItem[];
  created_at?: string;
  updated_at?: string;
}

export interface ProfileUpdatePayload {
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  approx_locality?: string;
  budget_preference?: string;
}

export const userService = {
  async getProfileMe(): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me");
  },

  async updateProfile(payload: ProfileUpdatePayload): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async updateInterests(interestIds: number[]): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me/interests", {
      method: "PUT",
      body: JSON.stringify(interestIds),
    });
  },

  async getInterestsCatalog(): Promise<MasterInterest[]> {
    return await fetchApi<MasterInterest[]>("/interests");
  },

  async getSkillsCatalog(): Promise<MasterSkill[]> {
    return await fetchApi<MasterSkill[]>("/skills");
  },

  async updateSkills(skills: UserSkillItem[]): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me/skills", {
      method: "PUT",
      body: JSON.stringify(skills),
    });
  },

  async updateAvailability(availability: UserAvailabilityItem[]): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me/availability", {
      method: "PUT",
      body: JSON.stringify(availability),
    });
  },

  async completeOnboarding(payload: {
    display_name: string;
    bio?: string;
    avatar_url?: string;
    approx_locality?: string;
    budget_preference?: string;
    interest_ids: number[];
    skills?: UserSkillItem[];
    availability?: UserAvailabilityItem[];
  }): Promise<FullProfile> {
    return await fetchApi<FullProfile>("/profile/me/onboarding", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getUserReputation(): Promise<any> {
    return await fetchApi("/users/me/reputation");
  },
};

export default userService;