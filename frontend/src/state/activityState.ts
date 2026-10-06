import { Activity } from "@/types/activity";

export type ActivityState = {
  activities: Activity[];
  selectedActivity: Activity | null;
  loading: boolean;
  error: string | null;
};

export const initialActivityState: ActivityState = {
  activities: [],
  selectedActivity: null,
  loading: false,
  error: null,
};