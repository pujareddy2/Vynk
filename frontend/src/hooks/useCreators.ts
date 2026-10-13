import { useState } from "react";
import { creatorService } from "@/services/creator.service";

export function useCreators() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCreators = async () => {
    setLoading(true);
    setError(null);

    try {
      return await creatorService.getCreators();
    } catch (err: any) {
      setError(err?.message || "Failed to load creators");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const followCreator = async (creatorId: number) => {
    setLoading(true);
    setError(null);

    try {
      return await creatorService.followCreator(creatorId);
    } catch (err: any) {
      setError(err?.message || "Failed to follow creator");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getCreators,
    followCreator,
    loading,
    error,
  };
}