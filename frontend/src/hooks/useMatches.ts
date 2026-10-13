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
    } catch (err: any) {
      setError(err?.message || "Failed to load matches");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getPeopleMatches = async () => {
    setLoading(true);
    setError(null);

    try {
      return await matchingService.getPeopleMatches();
    } catch (err: any) {
      setError(err?.message || "Failed to load people matches");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getMatches,
    getPeopleMatches,
    getMatch: getMatches,
    loading,
    error,
  };
}