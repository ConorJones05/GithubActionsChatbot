import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
const GITHUB_API_BASE_URL = "https://api.github.com";

const getGitHubToken = () => {
    return localStorage.getItem("github_token");
};

const fetchGitHubRepositories = async () => {
    const token = getGitHubToken();
    if (!token) {
        throw new Error("GitHub token not found");
    }
    
    try {
        const response = await axios.get(`${GITHUB_API_BASE_URL}/user/repos`, {
            headers: {
                Authorization: `token ${token}`,
                Accept: "application/vnd.github.v3+json"
            },
            params: {
                sort: "updated",
                per_page: 100
            }
        });
        return response.data;
    } catch (error) {
        console.error("Error fetching GitHub repositories:", error);
        throw error;
    }
};
function ReposPage() {
  const [repos, setRepos] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRepos = async () => {
      const response = await fetch("/api/repos");
      if (response.ok) {
        const data = await response.json();
        setRepos(data.repos);
      } else {
        navigate("/");
      }
    };

    fetchRepos();
  }, [navigate]);

  return (
    <div>
      <h1>Your Repositories</h1>
      {repos.length > 0 ? (
        <ul>
          {repos.map((repo, index) => (
            <li key={index}>{repo}</li>
          ))}
        </ul>
      ) : (
        <p>Loading...</p>
      )}
      <button onClick={() => navigate("/api-key")}>Back to API Key</button>
    </div>
  );
}

export default ReposPage;