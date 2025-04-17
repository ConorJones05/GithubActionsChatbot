import React from 'react';

interface ApiKeyDisplayProps {
  apiKey: string;
  onCopy: () => void;
  copied: boolean;
}

const ApiKeyDisplay: React.FC<ApiKeyDisplayProps> = ({ apiKey, onCopy, copied }) => {
  return (
    <div className="api-card">
      <h2 className="section-title">2. Your API Key:</h2>
      <div className="api-key-display">
        <code className="api-key-value">{apiKey}</code>
        <button 
          className={`copy-button ${copied ? 'copied' : ''}`}
          onClick={onCopy}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
    </div>
  );
};

export default ApiKeyDisplay;