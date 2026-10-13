import { fetchApi } from "./api";

export interface User {
  user_id: number;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at?: string;
  name?: string;
  city?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  email: string;
}

export const authService = {
  async register(email: string, password: string, confirmPassword?: string, approxLocality?: string): Promise<User> {
    const payload = {
      email,
      password,
      confirm_password: confirmPassword || password,
      approx_locality: approxLocality || undefined,
    };
    return await fetchApi<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const res = await fetchApi<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (res.access_token && typeof window !== "undefined") {
      localStorage.setItem("vynk_token", res.access_token);
      localStorage.setItem(
        "vynk_user",
        JSON.stringify({
          user_id: res.user_id,
          email: res.email,
          name: res.email.split("@")[0].charAt(0).toUpperCase() + res.email.split("@")[0].slice(1),
        })
      );
    }

    return res;
  },

  async getMe(): Promise<User> {
    return await fetchApi<User>("/auth/me");
  },

  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("vynk_token");
      localStorage.removeItem("vynk_user");
    }
  },

  isAuthenticated(): boolean {
    if (typeof window !== "undefined") {
      return !!localStorage.getItem("vynk_token");
    }
    return false;
  },

  async ensureAuthenticated(): Promise<string | null> {
    if (typeof window !== "undefined") {
      const existing = localStorage.getItem("vynk_token");
      if (existing) return existing;
      try {
        const res = await this.login("demo@vynk.com", "password123");
        return res.access_token;
      } catch {
        return null;
      }
    }
    return null;
  },
};

export default authService;