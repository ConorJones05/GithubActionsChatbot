import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import './LoginPage.css'

function ApiKeyPage() {
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  useEffect(() => {
    const fetchApiKey = async () => {
      if (!user) return;
      
      try {
        setLoading(true);
        const { data, error } = await supabase
          .from("users")
          .select("api_key")
          .eq("user_id", user.id)
          .single();

        if (error && error.code !== "PGRST116") {
          throw error;
        }
        
        if (data?.api_key) {
          setApiKey(data.api_key);
        } else {
          const response = await fetch("/api/generate-key", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
            }
          });
          
          if (!response.ok) {
            throw new Error("Failed to generate API key");
          }
          
          const newKeyData = await response.json();
          setApiKey(newKeyData.api_key);
        }
      } catch (error) {
        console.error("Error fetching API key:", error);
        alert("Failed to retrieve API key. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchApiKey();
  }, [user]);

  const getGitHubActionCode = () => {
    return `name: Debug with SaaS Debugging
if: \${{ failure() || steps.build.outcome == 'failure' }}
uses: ConorJones05/githubactionschatbot@main
with:
  api_key: ${apiKey}`;
  };

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(getGitHubActionCode());
    alert("GitHub Action code copied to clipboard!");
  };

  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    alert("API key copied to clipboard!");
  };

  return (
    <div>
      <div>
        <h1>GitHub Actions Integration</h1>
        
        {loading ? (
          <div>
            <div></div>
          </div>
        ) : (
          <div>
            <div>
              <h2>1. Copy this code into your workflow file:</h2>
              <div>
                <pre>
                  {getGitHubActionCode()}
                </pre>
                <button 
                  onClick={handleCopySnippet}
                >
                  Copy
                </button>
              </div>
              <p>Add this step to your GitHub workflow file (.github/workflows/your-workflow.yml)</p>
            </div>
            
            <div>
              <h2>2. Your API Key:</h2>
              <div>
                <code>{apiKey}</code>
                <button 
                  onClick={handleCopyApiKey}
                >
                  Copy
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div>
          <button 
            onClick={() => navigate("/repos")}
          >
            View My Repositories
          </button>
          
          <button 
            onClick={signOut}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

export default ApiKeyPage;