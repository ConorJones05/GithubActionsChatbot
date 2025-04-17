import { supabase } from "../utils/supabaseClient";

export const apiKeyService = {
  async fetchApiKey(userId: string) {
    const { data, error } = await supabase
      .from("users")
      .select("api_key")
      .eq("user_id", userId)
      .single();

    if (error && error.code !== "PGRST116") {
      throw error;
    }
    
    return data?.api_key;
  },
  
  async generateApiKey() {
    const session = await supabase.auth.getSession();
    const accessToken = session.data.session?.access_token;
    
    const response = await fetch("/api/generate-key", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error("Failed to generate API key");
    }
    
    const data = await response.json();
    return data.api_key;
  }
};