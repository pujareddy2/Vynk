import { fetchApi } from "./api";

export interface Creator {
  id: number;
  name: string;
  role: string;
  bio: string;
  followers: number;
  rating: number;
  avatar: string;
  badge: string;
  category: string;
  activitiesCount: number;
  upcomingEvent: string;
  verified: boolean;
}

export const creatorService = {
  async getCreators(): Promise<any> {
    // Falls back gracefully or calls backend
    try {
      return await fetchApi("/creators");
    } catch {
      return null;
    }
  },

  async followCreator(creatorId: number): Promise<any> {
    return { success: true, creatorId };
  },
};

export default creatorService;