import { fetchApi } from "./api";

export const intentService = {
  async understandIntent(prompt: string): Promise<any> {
    return await fetchApi("/ai/intent", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    });
  },

  async searchByIntent(query: string): Promise<any> {
    return await fetchApi("/ai/intent/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
  },
};

export default intentService;