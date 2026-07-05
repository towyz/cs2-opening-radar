import type { GrenadeType, Side } from "../types/analysis";

export interface Filters {
  demoIndices: number[];
  side: Side | "ALL";
  roundKey: string | "ALL";
  playbackRoundKeys: string[];
  grenadeType: GrenadeType | "ALL";
  showPath: boolean;
  showGrenades: boolean;
}

export type ViewMode = "overview" | "playback";

export interface DemoOption {
  index: number;
  label: string;
  title: string;
}

export interface RoundOption {
  key: string;
  label: string;
  roundNumber: number;
  demoIndex: number;
}

const grenadeTypes: Array<GrenadeType | "ALL"> = [
  "ALL",
  "smoke",
  "flash",
  "he",
  "molotov",
  "incendiary",
  "unknown"
];

export function FilterPanel({
  filters,
  viewMode,
  demos,
  rounds,
  disabled,
  onChange,
  onViewModeChange
}: {
  filters: Filters;
  viewMode: ViewMode;
  demos: DemoOption[];
  rounds: RoundOption[];
  disabled: boolean;
  onChange: (filters: Filters) => void;
  onViewModeChange: (mode: ViewMode) => void;
}) {
  const selectedDemos = new Set(filters.demoIndices);
  const visibleRounds = rounds.filter(
    (round) => selectedDemos.has(round.demoIndex)
  );
  const selectedPlaybackRounds = new Set(filters.playbackRoundKeys);
  const allDemosSelected = demos.length > 0 && demos.every((demo) => selectedDemos.has(demo.index));
  const allVisibleRoundsSelected =
    visibleRounds.length > 0 && visibleRounds.every((round) => selectedPlaybackRounds.has(round.key));

  function toggleDemo(demoIndex: number, checked: boolean) {
    const next = new Set(filters.demoIndices);
    if (checked) {
      next.add(demoIndex);
    } else {
      next.delete(demoIndex);
    }
    const nextDemoIndices = Array.from(next).sort((left, right) => left - right);
    const validRoundKeys = new Set(
      rounds.filter((round) => nextDemoIndices.includes(round.demoIndex)).map((round) => round.key)
    );
    onChange({
      ...filters,
      demoIndices: nextDemoIndices,
      roundKey: filters.roundKey === "ALL" || validRoundKeys.has(filters.roundKey) ? filters.roundKey : "ALL",
      playbackRoundKeys: filters.playbackRoundKeys.filter((key) => validRoundKeys.has(key))
    });
  }

  function togglePlaybackRound(roundKey: string, checked: boolean) {
    const next = new Set(filters.playbackRoundKeys);
    if (checked) {
      next.add(roundKey);
    } else {
      next.delete(roundKey);
    }
    onChange({ ...filters, playbackRoundKeys: Array.from(next).sort() });
  }

  return (
    <section className="panel filter-panel" aria-disabled={disabled}>
      <h2>Filters</h2>
      <div className="mode-switch" role="group" aria-label="Map mode">
        <button
          type="button"
          disabled={disabled}
          className={viewMode === "overview" ? "active" : ""}
          onClick={() => onViewModeChange("overview")}
        >
          Overview
        </button>
        <button
          type="button"
          disabled={disabled}
          className={viewMode === "playback" ? "active" : ""}
          onClick={() => onViewModeChange("playback")}
        >
          Playback
        </button>
      </div>
      <label>
        Side
        <select
          disabled={disabled}
          value={filters.side}
          onChange={(event) => onChange({ ...filters, side: event.target.value as Filters["side"] })}
        >
          <option value="ALL">All</option>
          <option value="T">T</option>
          <option value="CT">CT</option>
        </select>
      </label>
      <div className="round-picker">
        <div className="round-picker-header">
          <span>Demos</span>
          <button
            type="button"
            disabled={disabled || demos.length === 0}
            onClick={() =>
              onChange({
                ...filters,
                demoIndices: allDemosSelected ? [] : demos.map((demo) => demo.index),
                roundKey: "ALL",
                playbackRoundKeys: []
              })
            }
          >
            {allDemosSelected ? "Clear" : "All"}
          </button>
        </div>
        <div className="demo-check-grid">
          {demos.map((demo) => (
            <label key={demo.index} className="demo-check">
              <input
                type="checkbox"
                disabled={disabled}
                checked={selectedDemos.has(demo.index)}
                onChange={(event) => toggleDemo(demo.index, event.target.checked)}
              />
              <span title={demo.title}>{demo.label}</span>
            </label>
          ))}
        </div>
      </div>
      {viewMode === "overview" ? (
        <label>
          Round
          <select
            disabled={disabled}
            value={filters.roundKey}
            onChange={(event) =>
              onChange({
                ...filters,
                roundKey: event.target.value
              })
            }
          >
            <option value="ALL">All</option>
            {visibleRounds.map((round) => (
              <option key={round.key} value={round.key}>
                {round.label}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <div className="round-picker">
          <div className="round-picker-header">
            <span>Rounds</span>
            <button
              type="button"
              disabled={disabled || rounds.length === 0}
              onClick={() =>
                onChange({
                  ...filters,
                  playbackRoundKeys: allVisibleRoundsSelected ? [] : visibleRounds.map((round) => round.key)
                })
              }
            >
              {allVisibleRoundsSelected ? "Clear" : "All"}
            </button>
          </div>
          <div className="round-check-grid">
            {visibleRounds.map((round) => (
              <label key={round.key} className="round-check">
                <input
                  type="checkbox"
                  disabled={disabled}
                  checked={selectedPlaybackRounds.has(round.key)}
                  onChange={(event) => togglePlaybackRound(round.key, event.target.checked)}
                />
                {round.label}
              </label>
            ))}
          </div>
        </div>
      )}
      <label>
        Grenade
        <select
          disabled={disabled}
          value={filters.grenadeType}
          onChange={(event) =>
            onChange({ ...filters, grenadeType: event.target.value as Filters["grenadeType"] })
          }
        >
          {grenadeTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>
      <label className="check-row">
        <input
          type="checkbox"
          disabled={disabled}
          checked={filters.showPath}
          onChange={(event) => onChange({ ...filters, showPath: event.target.checked })}
        />
        Player path
      </label>
      <label className="check-row">
        <input
          type="checkbox"
          disabled={disabled}
          checked={filters.showGrenades}
          onChange={(event) => onChange({ ...filters, showGrenades: event.target.checked })}
        />
        Grenades
      </label>
    </section>
  );
}
