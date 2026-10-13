export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiError {
  message: string;
  status: number;
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Inject JWT auth token if stored
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("vynk_token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const res = await fetch(url, config);

    if (!res.ok) {
      let errorMessage = `Request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === "string" 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {}

      if (res.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("vynk_token");
      }

      const error: ApiError = { message: errorMessage, status: res.status };
      throw error;
    }

    if (res.status === 204) {
      return {} as T;
    }

    return await res.json();
  } catch (err: any) {
    if (err.status) {
      throw err;
    }
    throw { message: err.message || "Network connection error", status: 503 };
  }
}

export default API_URL;