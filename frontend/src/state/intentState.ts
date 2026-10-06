import { Intent } from "@/types/intent";

export type IntentState = {
  intents: Intent[];
  currentIntent: Intent | null;
  loading: boolean;
  error: string | null;
};

export const initialIntentState: IntentState = {
  intents: [],
  currentIntent: null,
  loading: false,
  error: null,
};