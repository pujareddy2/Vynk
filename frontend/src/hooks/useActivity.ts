import { useState } from "react";
import { activityService } from "@/services/activity.service";

export function useActivity() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getActivity = async (activityId: number) => {
    setLoading(true);
    setError(null);

    try {
      return await activityService.getActivity(activityId);
    } catch (err: any) {
      setError(err?.message || "Failed to load activity");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getActivity,
    loading,
    error,
  };
}