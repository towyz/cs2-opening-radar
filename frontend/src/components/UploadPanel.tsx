import React, { useRef, useState } from 'react';
import './UploadPanel.css';

interface UploadPanelProps {
  onAnalyze: (
    demoFile: File,
    steam64: string,
    mapName: string,
    windowSeconds: number,
  ) => void;
  loading: boolean;
}

export default function UploadPanel({ onAnalyze, loading }: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [steam64, setSteam64] = useState('');
  const [mapName, setMapName] = useState('de_dust2');
  const [windowSeconds, setWindowSeconds] = useState(30);
  const [fileName, setFileName] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!fileInputRef.current?.files?.[0]) {
      alert('Please select a demo file');
      return;
    }

    if (!steam64.trim()) {
      alert('Please enter Steam64 ID');
      return;
    }

    const demoFile = fileInputRef.current.files[0];
    onAnalyze(demoFile, steam64.trim(), mapName, windowSeconds);
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <form className="upload-panel" onSubmit={handleSubmit}>
      <h2>Analyze Demo</h2>

      <div className="form-group">
        <label htmlFor="demo-file">Demo File (.dem)</label>
        <div className="file-input-wrapper">
          <button
            type="button"
            className="file-button"
            onClick={handleFileClick}
            disabled={loading}
          >
            {fileName ? '✓ ' + fileName : 'Choose File'}
          </button>
          <input
            ref={fileInputRef}
            id="demo-file"
            type="file"
            accept=".dem"
            onChange={handleFileChange}
            disabled={loading}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="steam64">Steam64 ID</label>
        <input
          id="steam64"
          type="text"
          placeholder="e.g., 76561198123456789"
          value={steam64}
          onChange={(e) => setSteam64(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="map-name">Map</label>
          <select
            id="map-name"
            value={mapName}
            onChange={(e) => setMapName(e.target.value)}
            disabled={loading}
          >
            <option value="de_dust2">de_dust2</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="window-seconds">Window (seconds)</label>
          <input
            id="window-seconds"
            type="number"
            min="10"
            max="60"
            value={windowSeconds}
            onChange={(e) => setWindowSeconds(parseInt(e.target.value))}
            disabled={loading}
          />
        </div>
      </div>

      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
    </form>
  );
}
