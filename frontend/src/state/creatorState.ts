import { Creator } from "@/types/creator";

export type CreatorState = {
  creators: Creator[];
  selectedCreator: Creator | null;
  loading: boolean;
  error: string | null;
};

export const initialCreatorState: CreatorState = {
  creators: [],
  selectedCreator: null,
  loading: false,
  error: null,
};