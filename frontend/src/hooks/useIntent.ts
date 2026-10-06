import { useState } from "react";
import { intentService } from "@/services/intent.service";

export function useIntent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitIntent = async () => {
    setLoading(true);
    setError(null);

    try {
      return await intentService.submitIntent();
    } catch (err) {
      setError("Failed to submit intent");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getIntent = async () => {
    setLoading(true);
    setError(null);

    try {
      return await intentService.getIntent();
    } catch (err) {
      setError("Failed to load intent");
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