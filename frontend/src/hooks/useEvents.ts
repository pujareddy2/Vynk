import { useState } from "react";
import { eventService, EventCreatePayload } from "@/services/event.service";

export function useEvents() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getEvents = async () => {
    setLoading(true);
    setError(null);

    try {
      return await eventService.getEvents();
    } catch (err: any) {
      setError(err?.message || "Failed to load events");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createEvent = async (payload: EventCreatePayload) => {
    setLoading(true);
    setError(null);

    try {
      return await eventService.createEvent(payload);
    } catch (err: any) {
      setError(err?.message || "Failed to create event");
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