import { Match } from "@/types/match";

export type MatchingState = {
  matches: Match[];
  selectedMatch: Match | null;
  loading: boolean;
  error: string | null;
};

export const initialMatchingState: MatchingState = {
  matches: [],
  selectedMatch: null,
  loading: false,
  error: null,
};