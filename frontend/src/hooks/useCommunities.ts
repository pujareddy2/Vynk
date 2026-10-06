import { useState } from "react";
import { communityService } from "@/services/community.service";

export function useCommunities() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCommunities = async () => {
    setLoading(true);
    setError(null);

    try {
      return await communityService.getCommunities();
    } catch (err) {
      setError("Failed to load communities");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getCommunity = async () => {
    setLoading(true);
    setError(null);

    try {
      return await communityService.getCommunity();
    } catch (err) {
      setError("Failed to load community");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getCommunities,
    getCommunity,
    loading,
    error,
  };
}