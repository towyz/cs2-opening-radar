import { useMemo, useState } from "react";
import { ApiError, analyzeDemo, analyzeLocalDemo } from "./api/client";
import { FilterPanel, type Filters } from "./components/FilterPanel";
import { LocalDemoPanel } from "./components/LocalDemoPanel";
import { MapViewer } from "./components/MapViewer";
import { OpponentCard } from "./components/OpponentCard";
import { UploadPanel } from "./components/UploadPanel";
import type { AnalysisResult } from "./types/analysis";

const defaultFilters: Filters = {
  side: "ALL",
  roundNumber: "ALL",
  grenadeType: "ALL",
  showPath: true,
  showGrenades: true
};

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<Filters>(defaultFilters);

  const roundOptions = useMemo(
    () => result?.rounds.map((round) => round.roundNumber) ?? [],
    [result]
  );

  async function handleAnalyze(demo: File, steam64: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeDemo({ demo, steam64 });
      setResult(response.result);
      setFilters(defaultFilters);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyzeLocal(path: string, steam64: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeLocalDemo({ path, steam64 });
      setResult(response.result);
      setFilters(defaultFilters);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="toolbar-band">
        <div className="toolbar-grid">
          <UploadPanel loading={loading} error={error} onAnalyze={handleAnalyze} />
          <LocalDemoPanel loading={loading} onAnalyze={handleAnalyzeLocal} />
        </div>
      </section>

      <section className="workspace-grid">
        <aside className="sidebar">
          <OpponentCard result={result} />
          <FilterPanel
            filters={filters}
            rounds={roundOptions}
            disabled={!result}
            onChange={setFilters}
          />
        </aside>
        <MapViewer result={result} filters={filters} />
      </section>
    </main>
  );
}

function formatError(err: unknown): string {
  if (err instanceof ApiError && typeof err.detail === "object" && err.detail) {
    const detail = err.detail as {
      code?: string;
      message?: string;
      players?: Array<{ name: string; steam64: string }>;
    };
    const prefix = detail.code ? `${detail.code}: ` : "";
    const players = detail.players?.length
      ? ` Players: ${detail.players.map((player) => `${player.name} (${player.steam64})`).join(", ")}`
      : "";
    return `${prefix}${detail.message ?? err.message}${players}`;
  }
  return err instanceof Error ? err.message : "Analysis failed";
}
