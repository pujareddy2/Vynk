import { useState } from "react";
import { eventService } from "@/services/event.service";

export function useEvent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getEvent = async () => {
    setLoading(true);
    setError(null);

    try {
      return await eventService.getEvent();
    } catch (err) {
      setError("Failed to load event");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getEvent,
    loading,
    error,
  };
}