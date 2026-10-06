import { Recommendation } from "@/types/recommendation";

export type RecommendationState = {
  recommendations: Recommendation[];
  loading: boolean;
  error: string | null;
};

export const initialRecommendationState: RecommendationState = {
  recommendations: [],
  loading: false,
  error: null,
};