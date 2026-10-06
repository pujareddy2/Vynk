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
    } catch (err) {
      setError("Failed to load creators");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getCreator = async () => {
    setLoading(true);
    setError(null);

    try {
      return await creatorService.getCreator();
    } catch (err) {
      setError("Failed to load creator");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getCreators,
    getCreator,
    loading,
    error,
  };
}