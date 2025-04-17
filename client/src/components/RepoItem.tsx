import RecommendationView from "./RecommendationView";

interface RepoRecommendation {
  responseData: string;
  oldCode: string;
  newCode: string;
  fileName: string;
}

interface RepoItemProps {
  repo: string;
  recommendation?: RepoRecommendation;
  isOpen: boolean;
  isLoading: boolean;
  onToggle: () => void;
}

const RepoItem = ({ 
  repo, 
  recommendation, 
  isOpen, 
  isLoading, 
  onToggle 
}: RepoItemProps) => {
  return (
    <li className="repo-item">
      <div className="repo-header">
        <span className="repo-name">{repo}</span>
        <button
          className="show-recommendation-button"
          onClick={onToggle}
          disabled={isLoading}
        >
          {isLoading 
            ? "Loading..." 
            : recommendation && isOpen 
              ? "Hide Recommendation" 
              : "Show Recommendation"}
        </button>
      </div>
      
      {recommendation && isOpen && (
        <RecommendationView
          responseData={recommendation.responseData}
          oldCode={recommendation.oldCode}
          newCode={recommendation.newCode}
          fileName={recommendation.fileName}
        />
      )}
    </li>
  );
};

export default RepoItem;