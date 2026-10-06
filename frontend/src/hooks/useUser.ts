import { useState } from "react";
import { userService } from "@/services/user.service";

export function useUser() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getProfile = async () => {
    setLoading(true);
    setError(null);

    try {
      return await userService.getProfile();
    } catch (err) {
      setError("Failed to load profile");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async () => {
    setLoading(true);
    setError(null);

    try {
      return await userService.updateProfile();
    } catch (err) {
      setError("Failed to update profile");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getProfile,
    updateProfile,
    loading,
    error,
  };
}