import { Database, Play, RefreshCcw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { listLocalDemos, type LocalDemoItem } from "../api/client";

interface LocalDemoPanelProps {
  loading: boolean;
  onImport: (path: string) => void;
}

export function LocalDemoPanel({ loading, onImport }: LocalDemoPanelProps) {
  const [demos, setDemos] = useState<LocalDemoItem[]>([]);
  const [configPath, setConfigPath] = useState("");
  const [selectedPath, setSelectedPath] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    setError(null);
    try {
      const response = await listLocalDemos();
      setDemos(response.demos);
      setConfigPath(response.configPath);
      setSelectedPath((current) => current || response.demos[0]?.path || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load local demos");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedPath) {
      onImport(selectedPath);
    }
  }

  return (
    <form className="local-demo-panel" onSubmit={handleSubmit}>
      <div className="local-demo-header">
        <Database size={18} />
        <span>Local demos</span>
        <button className="icon-button" type="button" disabled={refreshing || loading} onClick={refresh}>
          <RefreshCcw size={16} />
        </button>
      </div>
      <select
        className="local-demo-select"
        value={selectedPath}
        disabled={loading || refreshing || demos.length === 0}
        onChange={(event) => setSelectedPath(event.target.value)}
      >
        {demos.length === 0 ? (
          <option value="">No configured demos</option>
        ) : (
          demos.map((demo) => (
            <option key={demo.path} value={demo.path}>
              {demo.name} - {formatBytes(demo.size)} - {demo.modifiedTime}
            </option>
          ))
        )}
      </select>
      <button className="primary-button" disabled={!selectedPath || loading}>
        <Play size={18} />
        <span>{loading ? "Reading" : "Add local"}</span>
      </button>
      {error ? <p className="inline-error">{error}</p> : null}
      {!error && demos.length === 0 ? (
        <p className="config-hint">Configure demo directories in {configPath || "backend/local_demo_config.json"}.</p>
      ) : null}
    </form>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
