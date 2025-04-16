import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { apiKeyService } from "../services/apiKeyService";
import ApiKeyDisplay from "./api-key/ApiKeyDisplay";
import GitHubActionsCode from "./api-key/GitHubActionsCode";
import NavigationButtons from "./api-key/NavigationButtons";
import LoadingSpinner from "./api-key/LoadingSpinner";
import './ApiKeyPage.css'; 

function ApiKeyPage() {
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [snippetCopied, setSnippetCopied] = useState(false);
  const [apiKeyCopied, setApiKeyCopied] = useState(false);
  const { user, signOut } = useAuth();

  useEffect(() => {
    const fetchApiKey = async () => {
      if (!user) return;
      
      try {
        setLoading(true);
        
        const existingKey = await apiKeyService.fetchApiKey(user.id);
        
        if (existingKey) {
          setApiKey(existingKey);
        } else {
          const newKey = await apiKeyService.generateApiKey();
          setApiKey(newKey);
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

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(`- name: Debug with SaaS Debugging
\t\t\t\tif: \${{ failure() || steps.build.outcome == 'failure' }}
\t\t\t\tuses: ConorJones05/githubactionschatbot@main
\t\t\t\twith:
\t\t\t\t  api_key: ${apiKey}`);
    
    setSnippetCopied(true);
    
    setTimeout(() => {
      setSnippetCopied(false);
    }, 2000);
  };

  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    
    setApiKeyCopied(true);
    
    setTimeout(() => {
      setApiKeyCopied(false);
    }, 2000);
  };

  return (
    <div className="api-container">
      <div className="api-content">
        <div className="api-header">
          <h1 className="api-title">GitHub Actions Integration</h1>
        </div>
        
        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            <GitHubActionsCode 
              apiKey={apiKey} 
              onCopy={handleCopySnippet}
              copied={snippetCopied}
            />
            
            <ApiKeyDisplay 
              apiKey={apiKey} 
              onCopy={handleCopyApiKey}
              copied={apiKeyCopied}
            />
          </>
        )}
        
        <NavigationButtons onSignOut={signOut} />
      </div>
    </div>
  );
}

export default ApiKeyPage;