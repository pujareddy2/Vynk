import { useState } from "react";
import { authService } from "@/services/auth.service";

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, pass: string) => {
    setLoading(true);
    setError(null);

    try {
      return await authService.login(email, pass);
    } catch (err: any) {
      setError(err?.message || "Login failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email: string, pass: string, confirm?: string) => {
    setLoading(true);
    setError(null);

    try {
      return await authService.register(email, pass, confirm);
    } catch (err: any) {
      setError(err?.message || "Signup failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
  };

  return {
    login,
    signup,
    logout,
    loading,
    error,
    isAuthenticated: authService.isAuthenticated,
  };
}