import { useState } from "react";
import { activityService } from "@/services/activity.service";

export function useActivities() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getActivities = async () => {
    setLoading(true);
    setError(null);

    try {
      return await activityService.getActivities();
    } catch (err: any) {
      setError(err?.message || "Failed to load activities");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createActivity = async (payload: { interest_id: number; title: string; description?: string }) => {
    setLoading(true);
    setError(null);

    try {
      return await activityService.createActivity(payload);
    } catch (err: any) {
      setError(err?.message || "Failed to create activity");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getActivities,
    createActivity,
    loading,
    error,
  };
}