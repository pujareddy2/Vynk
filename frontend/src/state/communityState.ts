import { Community } from "@/types/community";

export type CommunityState = {
  communities: Community[];
  selectedCommunity: Community | null;
  loading: boolean;
  error: string | null;
};

export const initialCommunityState: CommunityState = {
  communities: [],
  selectedCommunity: null,
  loading: false,
  error: null,
};