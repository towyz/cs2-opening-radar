import type { AnalysisResult, GrenadeType } from "../types/analysis";

const grenadeLabels: GrenadeType[] = ["smoke", "flash", "he", "molotov", "incendiary", "unknown"];

export function OpponentCard({ result }: { result: AnalysisResult | null }) {
  if (!result) {
    return (
      <section className="panel">
        <h2>Opponent</h2>
        <p className="muted">No analysis loaded.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>{result.meta.targetName ?? "Unknown player"}</h2>
      <dl className="stat-list">
        <div>
          <dt>Steam64</dt>
          <dd>{result.meta.targetSteam64}</dd>
        </div>
        <div>
          <dt>Map</dt>
          <dd>{result.meta.map}</dd>
        </div>
        <div>
          <dt>Window</dt>
          <dd>{result.meta.windowSeconds}s</dd>
        </div>
        <div>
          <dt>Rounds</dt>
          <dd>
            {result.summary.validRounds}/{result.summary.totalRounds}
          </dd>
        </div>
        <div>
          <dt>T / CT</dt>
          <dd>
            {result.summary.tRounds} / {result.summary.ctRounds}
          </dd>
        </div>
      </dl>
      <div className="grenade-stats">
        {grenadeLabels.map((type) => (
          <span key={type}>
            {type}: {result.summary.grenades[type]}
          </span>
        ))}
      </div>
    </section>
  );
}

