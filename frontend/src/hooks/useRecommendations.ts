import { useState } from "react";
import { recommendationService } from "@/services/recommendation.service";

export function useRecommendations() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      return await recommendationService.getRecommendations();
    } catch (err) {
      setError("Failed to load recommendations");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getRecommendations,
    loading,
    error,
  };
}