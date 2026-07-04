import type { GrenadeType, Side } from "../types/analysis";

export interface Filters {
  side: Side | "ALL";
  roundNumber: number | "ALL";
  playbackRoundNumbers: number[];
  grenadeType: GrenadeType | "ALL";
  showPath: boolean;
  showGrenades: boolean;
}

export type ViewMode = "overview" | "playback";

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
  rounds,
  disabled,
  onChange,
  onViewModeChange
}: {
  filters: Filters;
  viewMode: ViewMode;
  rounds: number[];
  disabled: boolean;
  onChange: (filters: Filters) => void;
  onViewModeChange: (mode: ViewMode) => void;
}) {
  const selectedPlaybackRounds = new Set(filters.playbackRoundNumbers);
  const allVisibleRoundsSelected =
    rounds.length > 0 && rounds.every((round) => selectedPlaybackRounds.has(round));

  function togglePlaybackRound(round: number, checked: boolean) {
    const next = new Set(filters.playbackRoundNumbers);
    if (checked) {
      next.add(round);
    } else {
      next.delete(round);
    }
    onChange({ ...filters, playbackRoundNumbers: Array.from(next).sort((left, right) => left - right) });
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
      {viewMode === "overview" ? (
        <label>
          Round
          <select
            disabled={disabled}
            value={filters.roundNumber}
            onChange={(event) =>
              onChange({
                ...filters,
                roundNumber: event.target.value === "ALL" ? "ALL" : Number(event.target.value)
              })
            }
          >
            <option value="ALL">All</option>
            {rounds.map((round) => (
              <option key={round} value={round}>
                {round}
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
                  playbackRoundNumbers: allVisibleRoundsSelected ? [] : rounds
                })
              }
            >
              {allVisibleRoundsSelected ? "Clear" : "All"}
            </button>
          </div>
          <div className="round-check-grid">
            {rounds.map((round) => (
              <label key={round} className="round-check">
                <input
                  type="checkbox"
                  disabled={disabled}
                  checked={selectedPlaybackRounds.has(round)}
                  onChange={(event) => togglePlaybackRound(round, event.target.checked)}
                />
                R{round}
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
