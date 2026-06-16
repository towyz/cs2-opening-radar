import type { Filters } from "./FilterPanel";
import { GrenadeLayer } from "./GrenadeLayer";
import { TrajectoryLayer } from "./TrajectoryLayer";
import type { AnalysisResult } from "../types/analysis";

export function MapViewer({
  result,
  filters
}: {
  result: AnalysisResult | null;
  filters: Filters;
}) {
  const rounds = (result?.rounds ?? []).filter((round) => {
    if (!round.valid) return false;
    if (filters.side !== "ALL" && round.side !== filters.side) return false;
    if (filters.roundNumber !== "ALL" && round.roundNumber !== filters.roundNumber) return false;
    return true;
  });

  return (
    <section className="map-stage">
      <div className="radar-frame">
        <img
          className="radar-image"
          src="/maps/de_dust2/radar.png"
          alt="de_dust2 radar"
          onError={(event) => {
            event.currentTarget.classList.add("missing");
          }}
        />
        <svg className="radar-overlay" viewBox="0 0 1024 1024" role="img">
          {filters.showPath ? <TrajectoryLayer rounds={rounds} /> : null}
          {filters.showGrenades ? (
            <GrenadeLayer rounds={rounds} grenadeType={filters.grenadeType} />
          ) : null}
        </svg>
        {!result ? <div className="empty-state">Upload a Dust2 demo to render opening paths.</div> : null}
      </div>
    </section>
  );
}

