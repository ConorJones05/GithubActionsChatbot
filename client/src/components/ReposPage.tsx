import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

interface RepoRecommendation {
  responseData: string;
  oldCode: string;
  newCode: string;
  fileName: string;
}

function ReposPage() {
  const [repos, setRepos] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<Record<string, RepoRecommendation>>({});
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [loadingRecommendation, setLoadingRecommendation] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const fetchRepos = async () => {
      try {
        console.log("Fetching repos for user:", user?.id);
        setLoadingRepos(true);
        
        if (!user) {
          setError("User not authenticated");
          return;
        }
        
        const { data: userData, error: userError } = await supabase
          .from("users")
          .select("repo_used")
          .eq("user_id", user.id)
          .single();
        
        if (userError) {
          console.error("Error fetching repos from Supabase:", userError);
          setError("Failed to load repositories from database");
          return;
        }
        
        console.log("Supabase response:", userData);
        
        if (userData && userData.repo_used && Array.isArray(userData.repo_used)) {
          setRepos(userData.repo_used);
        } else {
          setRepos([]);
        }
        
        setError(null);
      } catch (error) {
        console.error("Error fetching repositories:", error);
        setError("Error fetching repository data");
      } finally {
        setLoadingRepos(false);
      }
    };

    if (user) {
      fetchRepos();
    }
  }, [user]);

  const fetchRecommendation = async (repo: string) => {
    try {
      setLoadingRecommendation((prev) => ({ ...prev, [repo]: true }));
      
      if (!user) {
        console.error("User not authenticated");
        return;
      }

      const { data, error: recError } = await supabase
        .from("recommendations")
        .select("response_data, old_code, new_code, file_name")
        .eq("repository", repo)
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(1);
      
      console.log(`Response for ${repo}:`, data);
      
      if (recError) {
        console.error(`Error fetching recommendation for ${repo}:`, recError);
        setRecommendations((prev) => ({
          ...prev,
        }));
        return;
      }
      
      if (data && data.length > 0) {
        setRecommendations((prev) => ({
          ...prev,
          [repo]: {
            responseData: data[0].response_data,
            oldCode: data[0].old_code,
            newCode: data[0].new_code,
            fileName: data[0].file_name,
          },
        }));
      } else {
        setRecommendations((prev) => ({
          ...prev,
        }));
      }
    } catch (error) {
      console.error(`Error fetching recommendation for repo: ${repo}`, error);
      setRecommendations((prev) => ({
        ...prev,
      }));
    } finally {
      setLoadingRecommendation((prev) => ({ ...prev, [repo]: false }));
    }
  };

  return (
    <div>
      <h1>Your Repositories</h1>
      
      {error && (
        <div>
          <p>{error}</p>
        </div>
      )}
      
      {loadingRepos ? (
        <div>
          <div></div>
        </div>
      ) : repos.length > 0 ? (
        <ul>
          {repos.map((repo) => (
            <li key={repo}>
              <div>
                <span>{repo}</span>
                <button
                  onClick={() => fetchRecommendation(repo)}
                  disabled={loadingRecommendation[repo]}
                >
                  {loadingRecommendation[repo] ? "Loading..." : "Show Recommendation"}
                </button>
              </div>
              {recommendations[repo] && (
                <div>
                  <h3>Recommendation:</h3>
                  <p>{recommendations[repo].fileName}</p>
                  <p>{recommendations[repo].responseData}</p>
                  <div>
                    <div>
                      <h4>Old Code:</h4>
                      <pre>
                        {recommendations[repo].oldCode}
                      </pre>
                    </div>
                    <div>
                      <h4>New Code:</h4>
                      <pre>
                        {recommendations[repo].newCode}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p>No repositories found. Try using the GitHub Actions Chatbot with your workflows first.</p>
      )}
      <button
        onClick={() => navigate("/api-key")}
      >
        Back to API Key
      </button>
    </div>
  );
}

export default ReposPage;