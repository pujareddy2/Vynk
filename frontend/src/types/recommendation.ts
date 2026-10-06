export type Recommendation = {
  id: string;
  title: string;
  description?: string;
  type: "activity" | "event" | "person" | "group";
  score?: number;
};