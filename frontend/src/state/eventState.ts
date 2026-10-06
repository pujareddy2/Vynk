import { Event } from "@/types/event";

export type EventState = {
  events: Event[];
  selectedEvent: Event | null;
  loading: boolean;
  error: string | null;
};

export const initialEventState: EventState = {
  events: [],
  selectedEvent: null,
  loading: false,
  error: null,
};