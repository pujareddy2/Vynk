export type Participant = {
  id: string;
  userId: string;
  activityId?: string;
  eventId?: string;
  status: "pending" | "confirmed" | "cancelled";
};