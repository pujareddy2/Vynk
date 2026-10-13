import { useState } from "react";
import { intentService } from "@/services/intent.service";

export function useIntent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitIntent = async (prompt: string) => {
    setLoading(true);
    setError(null);

    try {
      return await intentService.understandIntent(prompt);
    } catch (err: any) {
      setError(err?.message || "Failed to submit intent");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getIntent = async (query: string) => {
    setLoading(true);
    setError(null);

    try {
      return await intentService.searchByIntent(query);
    } catch (err: any) {
      setError(err?.message || "Failed to load intent");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    submitIntent,
    getIntent,
    loading,
    error,
  };
}