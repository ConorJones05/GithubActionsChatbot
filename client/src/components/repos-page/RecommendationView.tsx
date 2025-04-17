import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';
import CodeComparisonBlock from './CodeComparisonBlock';

interface RecommendationViewProps {
  responseData: string;
  oldCode: string;
  newCode: string;
  fileName: string;
}

const RecommendationView: React.FC<RecommendationViewProps> = ({ 
  responseData, 
  oldCode, 
  newCode, 
  fileName 
}) => {
  return (
    <div className="recommendation-container">
      <div className="recommendation-header">
        <h3 className="recommendation-title">Recommendation:</h3>
      </div>
      <p className="file-name">File: {fileName}</p>
      
      <MarkdownRenderer content={responseData} />
      
      <CodeComparisonBlock 
        oldCode={oldCode}
        newCode={newCode}
        fileName={fileName}
      />
    </div>
  );
};

export default RecommendationView;