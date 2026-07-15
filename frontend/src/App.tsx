import { useState } from 'react';
import InputPanel from './components/InputPanel';
import FlowChart from './components/FlowChart';
import type { SearchResponse, StepData } from './types';
import './App.css';

function App() {
  const [steps, setSteps] = useState<StepData[]>([]);
  const [loading, setLoading] = useState(false);
  const [resultTitle, setResultTitle] = useState('');
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  const handleSearchResult = (result: SearchResponse) => {
    if (result.results.length > 0) {
      const firstResult = result.results[0];
      setResultTitle(firstResult.title);
      setSourceUrl(firstResult.source_url);
      setSteps(firstResult.steps);
      setIsDemo(result.is_demo);
    } else {
      setResultTitle('');
      setSourceUrl('');
      setSteps([]);
      setIsDemo(false);
    }
    setError(result.error || '');
  };

  const handleError = (msg: string) => {
    setError(msg);
  };

  return (
    <div className="app">
      <header className="app__input-section">
        <InputPanel
          onSearchResult={handleSearchResult}
          onLoadingChange={setLoading}
          onError={handleError}
        />
      </header>
      <main className="app__flow-section">
        {/* 错误提示 */}
        {error && !loading && (
          <div className="app__error-bar">
            <span className="app__error-icon">!</span>
            <span>{error}</span>
          </div>
        )}

        {/* 加载遮罩 */}
        {loading && (
          <div className="app__loading-overlay">
            <div className="app__loading-spinner" />
            <p>正在分解折纸步骤...</p>
          </div>
        )}

        {/* 结果标题 */}
        {resultTitle && !loading && (
          <div className="app__result-header">
            <h3>{resultTitle}</h3>
            {isDemo && <span className="app__demo-badge">演示数据</span>}
            {sourceUrl && (
              <a className="app__source-link" href={sourceUrl} target="_blank" rel="noopener noreferrer">
                查看来源
              </a>
            )}
          </div>
        )}

        <FlowChart steps={steps} />
      </main>
    </div>
  );
}

export default App;
