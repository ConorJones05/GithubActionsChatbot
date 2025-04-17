import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface CodeComparisonBlockProps {
  oldCode: string;
  newCode: string;
  fileName: string;
}

const CodeComparisonBlock: React.FC<CodeComparisonBlockProps> = ({ 
  oldCode, 
  newCode, 
  fileName 
}) => {
  const getLanguageFromFileName = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'jsx': return 'jsx';
      case 'tsx': return 'tsx';
      case 'py': return 'python';
      case 'html': return 'html';
      case 'css': return 'css';
      case 'scss': return 'scss';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'yml': case 'yaml': return 'yaml';
      case 'sh': return 'bash';
      case 'java': return 'java';
      case 'c': return 'c';
      case 'cpp': return 'cpp';
      case 'rb': return 'ruby';
      case 'php': return 'php';
      case 'go': return 'go';
      case 'rs': return 'rust';
      default: return 'text';
    }
  };

  const language = getLanguageFromFileName(fileName);

  return (
    <div className="code-comparison">
      <div className="code-section">
        <h4 className="code-title">Old Code:</h4>
        <div className="code-content-wrapper">
          <SyntaxHighlighter 
            language={language}
            style={vscDarkPlus}
            showLineNumbers={true}
            wrapLines={true}
            customStyle={{
              margin: 0,
              borderRadius: '0.25rem',
              maxWidth: '100%',
              height: '100%'
            }}
          >
            {oldCode}
          </SyntaxHighlighter>
        </div>
      </div>
      <div className="code-section">
        <h4 className="code-title">New Code:</h4>
        <div className="code-content-wrapper">
          <SyntaxHighlighter 
            language={language}
            style={vscDarkPlus}
            showLineNumbers={true}
            wrapLines={true}
            customStyle={{
              margin: 0,
              borderRadius: '0.25rem',
              maxWidth: '100%',
              height: '100%'
            }}
          >
            {newCode}
          </SyntaxHighlighter>
        </div>
      </div>
    </div>
  );
};

export default CodeComparisonBlock;