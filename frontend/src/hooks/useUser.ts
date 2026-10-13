import { useState } from "react";
import { userService, ProfileUpdatePayload } from "@/services/user.service";

export function useUser() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getProfile = async () => {
    setLoading(true);
    setError(null);

    try {
      return await userService.getProfileMe();
    } catch (err: any) {
      setError(err?.message || "Failed to load profile");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (payload: ProfileUpdatePayload) => {
    setLoading(true);
    setError(null);

    try {
      return await userService.updateProfile(payload);
    } catch (err: any) {
      setError(err?.message || "Failed to update profile");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getProfile,
    getProfileMe: getProfile,
    updateProfile,
    loading,
    error,
  };
}