import type { GrenadeType, RoundAnalysis } from "../types/analysis";

const grenadeColors: Record<GrenadeType, string> = {
  smoke: "#9aa4ad",
  flash: "#fff176",
  he: "#ef5350",
  molotov: "#ff7a1a",
  incendiary: "#ff7a1a",
  unknown: "#d6dde7"
};

export function GrenadeLayer({
  rounds,
  grenadeType
}: {
  rounds: RoundAnalysis[];
  grenadeType: GrenadeType | "ALL";
}) {
  return (
    <g>
      {rounds.flatMap((round) =>
        round.grenades
          .filter((grenade) => grenadeType === "ALL" || grenade.type === grenadeType)
          .map((grenade, index) => {
            const color = grenadeColors[grenade.type];
            const points = grenade.trajectory
              .map((point) => `${point.map.x},${point.map.y}`)
              .join(" ");
            return (
              <g key={`grenade-${round.roundNumber}-${index}`}>
                {points ? (
                  <polyline
                    points={points}
                    fill="none"
                    stroke={color}
                    strokeWidth="3"
                    strokeDasharray={grenade.trajectorySource === "estimated" ? "10 8" : undefined}
                    opacity="0.92"
                  />
                ) : null}
                <circle
                  cx={grenade.throwPosition.map.x}
                  cy={grenade.throwPosition.map.y}
                  r="6"
                  fill={color}
                  stroke="#10151d"
                  strokeWidth="2"
                >
                  <title>{`${grenade.type} R${round.roundNumber} ${grenade.throwTimeFromFreezeEnd.toFixed(1)}s`}</title>
                </circle>
                {grenade.detonatePosition ? (
                  <rect
                    x={grenade.detonatePosition.map.x - 6}
                    y={grenade.detonatePosition.map.y - 6}
                    width="12"
                    height="12"
                    fill="none"
                    stroke={color}
                    strokeWidth="3"
                  />
                ) : null}
              </g>
            );
          })
      )}
    </g>
  );
}

