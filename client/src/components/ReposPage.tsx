import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import RepoItem from "./RepoItem";

import "./ReposPage.css";

interface RepoRecommendation {
  responseData: string;
  oldCode: string;
  newCode: string;
  fileName: string;
}

function ReposPage() {
  const [repos, setRepos] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<Record<string, RepoRecommendation>>({});
  const [openRecommendations, setOpenRecommendations] = useState<Record<string, boolean>>({});
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [loadingRecommendation, setLoadingRecommendation] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const fetchRepos = async () => {
      try {
        console.log("Fetching repos from recommendations for user:", user?.id);
        setLoadingRepos(true);
    
        if (!user) {
          setError("User not authenticated");
          return;
        }
    
        const { data, error: recError } = await supabase
          .from("recommendations")
          .select("repository")
          .eq("user_id", user.id);
    
        if (recError) {
          console.error("Error fetching recommendations:", recError);
          setError("Failed to load repositories from recommendations");
          return;
        }
    
        if (data && Array.isArray(data)) {
          const uniqueRepos = Array.from(new Set(data.map(rec => rec.repository)));
          setRepos(uniqueRepos);
        } else {
          setRepos([]);
        }
    
        setError(null);
      } catch (error) {
        console.error("Error fetching repositories from recommendations:", error);
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
    if (recommendations[repo] && openRecommendations[repo]) {
      setOpenRecommendations(prev => ({
        ...prev,
        [repo]: false
      }));
      return;
    }
    
    try {
      setLoadingRecommendation((prev) => ({ ...prev, [repo]: true }));
      
      if (!user) {
        console.error("User not authenticated");
        return;
      }

      if (recommendations[repo]) {
        setOpenRecommendations(prev => ({
          ...prev,
          [repo]: true
        }));
        setLoadingRecommendation((prev) => ({ ...prev, [repo]: false }));
        return;
      }

      const { data, error: recError } = await supabase
        .from("recommendations")
        .select("response_data, old_code, new_code, file_name")
        .eq("repository", repo)
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .single();
      
      console.log(`Response for ${repo}:`, data);
      
      if (recError) {
        console.error(`Error fetching recommendation for ${repo}:`, recError);
        return;
      }
      
      if (data) {
        setRecommendations((prev) => ({
          ...prev,
          [repo]: {
            responseData: data.response_data,
            oldCode: data.old_code,
            newCode: data.new_code,
            fileName: data.file_name || "unknown",
          },
        }));
        setOpenRecommendations(prev => ({
          ...prev,
          [repo]: true
        }));
      }
    } catch (error) {
      console.error(`Error fetching recommendation for repo: ${repo}`, error);

      setOpenRecommendations(prev => ({
        ...prev,
        [repo]: true
      }));
    } finally {
      setLoadingRecommendation((prev) => ({ ...prev, [repo]: false }));
    }
  };

  return (
    <div className="repos-container">
      <div className="repos-header">
        <h1 className="repos-title">Your Repositories</h1>
      </div>
      
      {error && (
        <div className="error-alert">
          <p>{error}</p>
        </div>
      )}
      
      {loadingRepos ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
        </div>
      ) : repos.length > 0 ? (
        <ul className="repos-list">
          {repos.map((repo) => (
            <RepoItem
              key={repo}
              repo={repo}
              recommendation={recommendations[repo]}
              isOpen={!!openRecommendations[repo]}
              isLoading={!!loadingRecommendation[repo]}
              onToggle={() => fetchRecommendation(repo)}
            />
          ))}
        </ul>
      ) : (
        <p className="no-repos-message">No repositories found. Try using the GitHub Actions Chatbot with your workflows first.</p>
      )}
      
      <button
        className="back-button"
        onClick={() => navigate("/api-key")}
      >
        Back to API Key
      </button>
    </div>
  );
}

export default ReposPage;