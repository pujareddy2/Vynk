export type Match = {
  id: string;
  userId: string;
  matchedUserId: string;
  score?: number;
  status: "pending" | "accepted" | "rejected";
};