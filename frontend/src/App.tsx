import { useState } from 'react';
import InputPanel from './components/InputPanel';
import FlowChart from './components/FlowChart';
import type { SearchResponse, StepData } from './types';
import './App.css';

function App() {
  const [steps, setSteps] = useState<StepData[]>([]);
  const [loading, setLoading] = useState(false);
  const [resultTitle, setResultTitle] = useState<string>('');

  // 处理搜索结果
  const handleSearchResult = (result: SearchResponse) => {
    if (result.results.length > 0) {
      // 展示第一个教程的步骤
      const firstResult = result.results[0];
      setResultTitle(firstResult.title);
      setSteps(firstResult.steps);
    } else {
      setResultTitle('');
      setSteps([]);
    }
  };

  return (
    <div className="app">
      <header className="app__input-section">
        <InputPanel
          onSearchResult={handleSearchResult}
          onLoadingChange={setLoading}
        />
      </header>
      <main className="app__flow-section">
        {loading && (
          <div className="app__loading-overlay">
            <div className="app__loading-spinner" />
            <p>正在分解折纸步骤...</p>
          </div>
        )}
        {resultTitle && !loading && (
          <div className="app__result-header">
            <h3>📄 {resultTitle}</h3>
          </div>
        )}
        <FlowChart steps={steps} />
      </main>
    </div>
  );
}

export default App;
