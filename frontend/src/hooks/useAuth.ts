import { useState } from "react";
import { authService } from "@/services/auth.service";

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async () => {
    setLoading(true);
    setError(null);

    try {
      await authService.login();
    } catch (err) {
      setError("Login failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signup = async () => {
    setLoading(true);
    setError(null);

    try {
      await authService.signup();
    } catch (err) {
      setError("Signup failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    setError(null);

    try {
      await authService.logout();
    } catch (err) {
      setError("Logout failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    login,
    signup,
    logout,
    loading,
    error,
  };
}