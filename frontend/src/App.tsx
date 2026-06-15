import React, { useState } from 'react';
import { AnalysisResult } from './types/analysis';
import UploadPanel from './components/UploadPanel';
import OpponentCard from './components/OpponentCard';
import MapViewer from './components/MapViewer';
import './App.css';

function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRounds, setSelectedRounds] = useState<Set<number>>(new Set());
  const [showPath, setShowPath] = useState(true);
  const [showGrenades, setShowGrenades] = useState(true);
  const [grenadeFilter, setGrenadeFilter] = useState<string | null>(null);

  const handleAnalyze = async (
    demoFile: File,
    steam64: string,
    mapName: string,
    windowSeconds: number,
  ) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const { apiClient } = await import('./api/client');
      const response = await apiClient.analyzeDemoFile(demoFile, steam64, mapName, windowSeconds);
      setResult(response.result);
      setSelectedRounds(new Set(response.result.rounds.map((r) => r.roundNumber)));
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>CS2 Opening Analyzer</h1>
        <p>Analyze opening behavior from CS2 demo files</p>
      </header>

      <div className="app-container">
        <div className="upload-section">
          <UploadPanel onAnalyze={handleAnalyze} loading={loading} />
        </div>

        {error && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="analysis-section">
            <div className="sidebar">
              <OpponentCard result={result} />
              <div className="filters">
                <h3>Filters</h3>
                <label>
                  <input
                    type="checkbox"
                    checked={showPath}
                    onChange={(e) => setShowPath(e.target.checked)}
                  />
                  Show Path
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={showGrenades}
                    onChange={(e) => setShowGrenades(e.target.checked)}
                  />
                  Show Grenades
                </label>
                <div>
                  <label>Grenade Type:</label>
                  <select
                    value={grenadeFilter || ''}
                    onChange={(e) => setGrenadeFilter(e.target.value || null)}
                  >
                    <option value="">All Types</option>
                    <option value="smoke">Smoke</option>
                    <option value="flash">Flash</option>
                    <option value="he">HE</option>
                    <option value="molotov">Molotov</option>
                    <option value="incendiary">Incendiary</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="main-content">
              <MapViewer
                result={result}
                selectedRounds={selectedRounds}
                showPath={showPath}
                showGrenades={showGrenades}
                grenadeFilter={grenadeFilter}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
