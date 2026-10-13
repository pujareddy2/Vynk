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
    } catch (err: any) {
      setError(err?.message || "Failed to load communities");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getCommunity = async (id: number) => {
    setLoading(true);
    setError(null);

    try {
      return await communityService.getCommunityHealth(id);
    } catch (err: any) {
      setError(err?.message || "Failed to load community");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const joinCommunity = async (id: number) => {
    setLoading(true);
    setError(null);

    try {
      return await communityService.joinCommunity(id);
    } catch (err: any) {
      setError(err?.message || "Failed to join community");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getCommunities,
    getCommunity,
    joinCommunity,
    loading,
    error,
  };
}