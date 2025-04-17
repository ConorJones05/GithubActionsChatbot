import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface CodeComparisonBlockProps {
  oldCode: string;
  newCode: string;
  fileName: string;
}

const CodeComparisonBlock = ({ oldCode, newCode, fileName }: CodeComparisonBlockProps) => {
  const getLanguageFromFileName = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'jsx': return 'jsx';
      case 'tsx': return 'tsx';
      case 'py': return 'python';
      default: return 'javascript';
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