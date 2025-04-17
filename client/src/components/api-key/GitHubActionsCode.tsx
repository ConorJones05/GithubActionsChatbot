import React from 'react';

interface GitHubActionsCodeProps {
  apiKey: string;
  onCopy: () => void;
  copied: boolean;
}

const GitHubActionsCode: React.FC<GitHubActionsCodeProps> = ({ apiKey, onCopy, copied }) => {
  const getGitHubActionCode = () => {
    return `name: Debug with SaaS Debugging
if: \${{ failure() || steps.build.outcome == 'failure' }}
uses: ConorJones05/githubactionschatbot@main
with:
  api_key: ${apiKey}`;
  };

  return (
    <div className="api-card">
      <h2 className="section-title">1. Copy this code into your workflow file:</h2>
      <div className="code-block">
        <pre>
          {getGitHubActionCode()}
        </pre>
        <button 
          className={`copy-button ${copied ? 'copied' : ''}`}
          onClick={onCopy}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <p className="note">Add this step to your GitHub workflow file (.github/workflows/your-workflow.yml)</p>
    </div>
  );
};

export default GitHubActionsCode;