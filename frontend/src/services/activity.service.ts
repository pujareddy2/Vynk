import { fetchApi } from "./api";

export interface Activity {
  activity_id: number;
  interest_id: number;
  interest_name?: string;
  interest_category?: string;
  title: string;
  description?: string;
  created_by?: number;
  creator_name?: string;
  created_at?: string;
}

export interface ActivityCreatePayload {
  interest_id: number;
  title: string;
  description?: string;
}

export const activityService = {
  async getActivities(): Promise<Activity[]> {
    return await fetchApi<Activity[]>("/activities");
  },

  async getActivity(activityId: number): Promise<Activity> {
    return await fetchApi<Activity>(`/activities/${activityId}`);
  },

  async createActivity(payload: ActivityCreatePayload): Promise<Activity> {
    return await fetchApi<Activity>("/activities", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async deleteActivity(activityId: number): Promise<any> {
    return await fetchApi(`/activities/${activityId}`, {
      method: "DELETE",
    });
  },
};

export default activityService;