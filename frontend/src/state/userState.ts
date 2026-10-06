import { Profile } from "@/types/profile";
import { User } from "@/types/user";

export type UserState = {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  error: string | null;
};

export const initialUserState: UserState = {
  user: null,
  profile: null,
  loading: false,
  error: null,
};