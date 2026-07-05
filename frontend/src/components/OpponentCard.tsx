import type { AnalysisResult, GrenadeType } from "../types/analysis";

const grenadeLabels: GrenadeType[] = ["smoke", "flash", "he", "molotov", "incendiary", "unknown"];

export function OpponentCard({
  results,
  onClear
}: {
  results: AnalysisResult[];
  onClear: () => void;
}) {
  if (results.length === 0) {
    return (
      <section className="panel">
        <h2>Demos</h2>
        <p className="muted">No analysis loaded.</p>
      </section>
    );
  }

  const totals = results.reduce(
    (summary, result) => ({
      totalRounds: summary.totalRounds + result.summary.totalRounds,
      validRounds: summary.validRounds + result.summary.validRounds,
      tRounds: summary.tRounds + result.summary.tRounds,
      ctRounds: summary.ctRounds + result.summary.ctRounds,
      grenades: grenadeLabels.reduce(
        (grenades, type) => ({ ...grenades, [type]: grenades[type] + result.summary.grenades[type] }),
        summary.grenades
      )
    }),
    {
      totalRounds: 0,
      validRounds: 0,
      tRounds: 0,
      ctRounds: 0,
      grenades: {
        smoke: 0,
        flash: 0,
        he: 0,
        molotov: 0,
        incendiary: 0,
        unknown: 0
      } satisfies Record<GrenadeType, number>
    }
  );

  return (
    <section className="panel">
      <div className="panel-title-row">
        <h2>Demos</h2>
        <button type="button" onClick={onClear}>
          Clear
        </button>
      </div>
      <dl className="stat-list">
        <div>
          <dt>Loaded</dt>
          <dd>{results.length}</dd>
        </div>
        <div>
          <dt>Map</dt>
          <dd>{Array.from(new Set(results.map((result) => result.meta.map))).join(", ")}</dd>
        </div>
        <div>
          <dt>Window</dt>
          <dd>{Math.max(...results.map((result) => result.meta.windowSeconds))}s</dd>
        </div>
        <div>
          <dt>Rounds</dt>
          <dd>
            {totals.validRounds}/{totals.totalRounds}
          </dd>
        </div>
        <div>
          <dt>T / CT</dt>
          <dd>
            {totals.tRounds} / {totals.ctRounds}
          </dd>
        </div>
      </dl>
      <div className="demo-list">
        {results.map((result, index) => (
          <div key={`${result.meta.demoFile}-${index}`} className="demo-list-item">
            <strong>D{index + 1}</strong>
            <span>{result.meta.demoFile}</span>
          </div>
        ))}
      </div>
      <div className="grenade-stats">
        {grenadeLabels.map((type) => (
          <span key={type}>
            {type}: {totals.grenades[type]}
          </span>
        ))}
      </div>
    </section>
  );
}
