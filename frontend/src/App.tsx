import { useMemo, useState } from "react";
import { ApiError, analyzePlayer, importDemo, importLocalDemo, type ImportedDemo, type PlayerOption } from "./api/client";
import { FilterPanel, type Filters, type ViewMode } from "./components/FilterPanel";
import { LocalDemoPanel } from "./components/LocalDemoPanel";
import { MapViewer } from "./components/MapViewer";
import { OpponentCard } from "./components/OpponentCard";
import { UploadPanel } from "./components/UploadPanel";
import type { AnalysisResult } from "./types/analysis";

interface ImportedDemoState extends ImportedDemo {
  players: PlayerOption[];
}

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
  const [importedDemos, setImportedDemos] = useState<ImportedDemoState[]>([]);
  const [selectedSteam64, setSelectedSteam64] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [viewMode, setViewMode] = useState<ViewMode>("overview");

  const hasResults = results.length > 0;
  const playerOptions = useMemo(() => {
    const players = new Map<string, PlayerOption & { demoCount: number }>();
    for (const demo of importedDemos) {
      for (const player of demo.players) {
        const current = players.get(player.steam64);
        if (current) {
          current.demoCount += 1;
        } else {
          players.set(player.steam64, { ...player, demoCount: 1 });
        }
      }
    }
    return Array.from(players.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [importedDemos]);
  const selectedDemoIds = useMemo(
    () =>
      selectedSteam64
        ? importedDemos
            .filter((demo) => demo.players.some((player) => player.steam64 === selectedSteam64))
            .map((demo) => demo.id)
        : [],
    [importedDemos, selectedSteam64]
  );
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

  async function handleImportDemo(demo: File) {
    setLoading(true);
    setError(null);
    try {
      const response = await importDemo({ demo });
      appendImportedDemo({ ...response.demo, players: response.players });
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleImportLocalDemo(path: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await importLocalDemo({ path });
      appendImportedDemo({ ...response.demo, players: response.players });
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyzeSelectedPlayer() {
    if (!selectedSteam64 || selectedDemoIds.length === 0) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await analyzePlayer({ demoIds: selectedDemoIds, steam64: selectedSteam64 });
      replaceResults(response.results);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  function appendImportedDemo(nextDemo: ImportedDemoState) {
    setImportedDemos((current) => [...current, nextDemo]);
    if (!selectedSteam64 && nextDemo.players[0]) {
      setSelectedSteam64(nextDemo.players[0].steam64);
    }
  }

  function replaceResults(nextResults: AnalysisResult[]) {
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
    setImportedDemos([]);
    setSelectedSteam64("");
    setFilters(defaultFilters);
    setViewMode("overview");
    setError(null);
  }

  return (
    <main className="app-shell">
      <section className="toolbar-band">
        <div className="toolbar-grid">
          <UploadPanel loading={loading} error={error} onImport={handleImportDemo} />
          <LocalDemoPanel loading={loading} onImport={handleImportLocalDemo} />
        </div>
      </section>

      <section className="workspace-grid">
        <aside className="sidebar">
          <PlayerSelectionPanel
            demos={importedDemos}
            players={playerOptions}
            selectedSteam64={selectedSteam64}
            selectedDemoCount={selectedDemoIds.length}
            loading={loading}
            onSelect={setSelectedSteam64}
            onAnalyze={handleAnalyzeSelectedPlayer}
          />
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

function PlayerSelectionPanel({
  demos,
  players,
  selectedSteam64,
  selectedDemoCount,
  loading,
  onSelect,
  onAnalyze
}: {
  demos: ImportedDemoState[];
  players: Array<PlayerOption & { demoCount: number }>;
  selectedSteam64: string;
  selectedDemoCount: number;
  loading: boolean;
  onSelect: (steam64: string) => void;
  onAnalyze: () => void;
}) {
  return (
    <section className="player-panel">
      <div className="player-panel-header">
        <span>Players</span>
        <span>{demos.length} demos</span>
      </div>
      {demos.length > 0 ? (
        <div className="imported-demo-list">
          {demos.map((demo, index) => (
            <div className="imported-demo-item" key={demo.id} title={demo.name}>
              D{index + 1} {demo.name}
            </div>
          ))}
        </div>
      ) : (
        <p className="config-hint">Add demos to read Perfect World player names.</p>
      )}
      <select
        className="local-demo-select"
        value={selectedSteam64}
        disabled={loading || players.length === 0}
        onChange={(event) => onSelect(event.target.value)}
      >
        {players.length === 0 ? (
          <option value="">No players loaded</option>
        ) : (
          players.map((player) => (
            <option key={player.steam64} value={player.steam64}>
              {player.name} - {player.demoCount} demo{player.demoCount > 1 ? "s" : ""}
            </option>
          ))
        )}
      </select>
      <button className="primary-button" disabled={!selectedSteam64 || selectedDemoCount === 0 || loading} onClick={onAnalyze}>
        <span>{loading ? "Parsing" : `Analyze ${selectedDemoCount} demo${selectedDemoCount > 1 ? "s" : ""}`}</span>
      </button>
    </section>
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
