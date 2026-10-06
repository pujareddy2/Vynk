import { useState } from "react";
import { activityService } from "@/services/activity.service";

export function useActivity() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getActivity = async () => {
    setLoading(true);
    setError(null);

    try {
      return await activityService.getActivity();
    } catch (err) {
      setError("Failed to load activity");
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