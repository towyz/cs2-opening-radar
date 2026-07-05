import { useMemo, useState } from "react";
import {
  ApiError,
  analyzeDemo,
  analyzeLocalDemo,
  importPerfectWorldRecentDust2,
  type PerfectWorldRecentResponse
} from "./api/client";
import { FilterPanel, type Filters, type ViewMode } from "./components/FilterPanel";
import { LocalDemoPanel } from "./components/LocalDemoPanel";
import { MapViewer } from "./components/MapViewer";
import { OpponentCard } from "./components/OpponentCard";
import { PerfectWorldPanel } from "./components/PerfectWorldPanel";
import { UploadPanel } from "./components/UploadPanel";
import type { AnalysisResult } from "./types/analysis";

const defaultFilters: Filters = {
  demoIndices: [],
  side: "ALL",
  roundKey: "ALL",
  playbackRoundKeys: [],
  grenadeType: "ALL",
  showPath: true,
  showGrenades: true
};

export default function App() {
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [viewMode, setViewMode] = useState<ViewMode>("overview");

  const hasResults = results.length > 0;
  const demoOptions = useMemo(
    () =>
      results.map((result, index) => ({
        index,
        label: demoLabel(result, index),
        title: result.meta.demoFile
      })),
    [results]
  );
  const roundOptions = useMemo(
    () =>
      results.flatMap((result, demoIndex) =>
        result.rounds
          .filter((round) => round.valid)
          .map((round) => ({
            key: roundKey(demoIndex, round.roundNumber),
            label: `D${demoIndex + 1} R${round.roundNumber}`,
            roundNumber: round.roundNumber,
            demoIndex
          }))
      ),
    [results]
  );

  async function handleAnalyze(demo: File, steam64: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeDemo({ demo, steam64 });
      appendResult(response.result);
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
      appendResult(response.result);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleImportPerfectWorld(uid: string, steam64?: string): Promise<PerfectWorldRecentResponse> {
    setLoading(true);
    setError(null);
    try {
      const response = await importPerfectWorldRecentDust2({ uid, steam64, limit: 5 });
      appendResults(response.results);
      if (response.imported.length === 0 && response.scanned === 0) {
        setError("No recent Perfect World dust2 demo candidates were returned for this UID.");
      } else if (response.imported.length === 0) {
        setError(`No matching dust2 demos found for this Steam64. Scanned ${response.scanned}, downloaded ${response.downloaded}.`);
      }
      return response;
    } catch (err) {
      setError(formatError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }

  function appendResult(nextResult: AnalysisResult) {
    appendResults([nextResult]);
  }

  function appendResults(nextBatch: AnalysisResult[]) {
    if (nextBatch.length === 0) {
      return;
    }
    const nextResults = [...results, ...nextBatch];
    setResults(nextResults);
    setFilters((currentFilters) => ({
      ...currentFilters,
      demoIndices: nextResults.map((_, index) => index),
      roundKey: "ALL",
      playbackRoundKeys: []
    }));
    setViewMode("overview");
  }

  function handleClearResults() {
    setResults([]);
    setFilters(defaultFilters);
    setViewMode("overview");
    setError(null);
  }

  return (
    <main className="app-shell">
      <section className="toolbar-band">
        <div className="toolbar-grid">
          <UploadPanel loading={loading} error={error} onAnalyze={handleAnalyze} />
          <LocalDemoPanel loading={loading} onAnalyze={handleAnalyzeLocal} />
          <PerfectWorldPanel loading={loading} onImport={handleImportPerfectWorld} />
        </div>
      </section>

      <section className="workspace-grid">
        <aside className="sidebar">
          <OpponentCard results={results} onClear={handleClearResults} />
          <FilterPanel
            filters={filters}
            viewMode={viewMode}
            demos={demoOptions}
            rounds={roundOptions}
            disabled={!hasResults}
            onChange={setFilters}
            onViewModeChange={setViewMode}
          />
        </aside>
        <MapViewer results={results} filters={filters} viewMode={viewMode} />
      </section>
    </main>
  );
}

function demoLabel(result: AnalysisResult, index: number): string {
  return `D${index + 1} ${shortDemoName(result.meta.demoFile)}`;
}

function roundKey(demoIndex: number, roundNumber: number): string {
  return `${demoIndex}:${roundNumber}`;
}

function shortDemoName(fileName: string): string {
  const stem = fileName.replace(/\.(dem|zip|bz2)$/i, "");
  if (stem.length <= 12) {
    return fileName;
  }
  return `${stem.slice(0, 8)}...${stem.slice(-4)}${fileName.slice(stem.length)}`;
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
