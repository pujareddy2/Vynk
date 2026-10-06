import { useState } from "react";
import { matchingService } from "@/services/matching.service";

export function useMatches() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getMatches = async () => {
    setLoading(true);
    setError(null);

    try {
      return await matchingService.getMatches();
    } catch (err) {
      setError("Failed to load matches");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getMatch = async () => {
    setLoading(true);
    setError(null);

    try {
      return await matchingService.getMatch();
    } catch (err) {
      setError("Failed to load match");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getMatches,
    getMatch,
    loading,
    error,
  };
}