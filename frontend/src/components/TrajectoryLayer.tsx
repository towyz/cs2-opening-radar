import type { RoundAnalysis } from "../types/analysis";

const sideColors: Record<string, string> = {
  T: "#ffb000",
  CT: "#31b7ff",
  UNKNOWN: "#d6dde7"
};

export function TrajectoryLayer({ rounds }: { rounds: RoundAnalysis[] }) {
  return (
    <g>
      {rounds.map((round) => {
        const points = round.path.map((point) => `${point.map.x},${point.map.y}`).join(" ");
        if (!points) return null;
        const start = round.path[0];
        const end = round.path[round.path.length - 1];
        const color = sideColors[round.side] ?? sideColors.UNKNOWN;
        return (
          <g key={`path-${round.roundNumber}`}>
            <polyline
              points={points}
              fill="none"
              stroke={color}
              strokeWidth="4"
              strokeLinejoin="round"
              strokeLinecap="round"
              opacity="0.84"
            />
            <circle cx={start.map.x} cy={start.map.y} r="7" fill={color}>
              <title>{`R${round.roundNumber} start ${round.side}`}</title>
            </circle>
            <circle cx={end.map.x} cy={end.map.y} r="7" fill="#ffffff" stroke={color} strokeWidth="3">
              <title>{`R${round.roundNumber} end ${end.timeFromFreezeEnd.toFixed(1)}s`}</title>
            </circle>
          </g>
        );
      })}
    </g>
  );
}

