import { useState } from "react";
import { eventService } from "@/services/event.service";

export function useEvents() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getEvents = async () => {
    setLoading(true);
    setError(null);

    try {
      return await eventService.getEvents();
    } catch (err) {
      setError("Failed to load events");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createEvent = async () => {
    setLoading(true);
    setError(null);

    try {
      return await eventService.createEvent();
    } catch (err) {
      setError("Failed to create event");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getEvents,
    createEvent,
    loading,
    error,
  };
}