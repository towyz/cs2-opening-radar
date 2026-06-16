import type { GrenadeType, Side } from "../types/analysis";

export interface Filters {
  side: Side | "ALL";
  roundNumber: number | "ALL";
  grenadeType: GrenadeType | "ALL";
  showPath: boolean;
  showGrenades: boolean;
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
  rounds,
  disabled,
  onChange
}: {
  filters: Filters;
  rounds: number[];
  disabled: boolean;
  onChange: (filters: Filters) => void;
}) {
  return (
    <section className="panel filter-panel" aria-disabled={disabled}>
      <h2>Filters</h2>
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

