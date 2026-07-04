import type {
  GrenadeEvent,
  GrenadeTrajectoryPoint,
  GrenadeType,
  MapPoint,
  RoundAnalysis,
  TrajectoryPoint
} from "../types/analysis";

const sideColors: Record<string, string> = {
  T: "#ffb000",
  CT: "#31b7ff",
  UNKNOWN: "#d6dde7"
};

const grenadeColors: Record<GrenadeType, string> = {
  smoke: "#9aa4ad",
  flash: "#fff176",
  he: "#ef5350",
  molotov: "#ff7a1a",
  incendiary: "#ff7a1a",
  unknown: "#d6dde7"
};

export function PlaybackLayer({
  rounds,
  currentTime,
  grenadeType,
  showPath,
  showGrenades
}: {
  rounds: RoundAnalysis[];
  currentTime: number;
  grenadeType: GrenadeType | "ALL";
  showPath: boolean;
  showGrenades: boolean;
}) {
  return (
    <g>
      {rounds.map((round, index) => (
        <PlaybackRound
          key={`playback-round-${round.roundNumber}`}
          round={round}
          currentTime={currentTime}
          grenadeType={grenadeType}
          showPath={showPath}
          showGrenades={showGrenades}
          color={roundColor(round, index)}
        />
      ))}
    </g>
  );
}

function PlaybackRound({
  round,
  currentTime,
  grenadeType,
  showPath,
  showGrenades,
  color
}: {
  round: RoundAnalysis;
  currentTime: number;
  grenadeType: GrenadeType | "ALL";
  showPath: boolean;
  showGrenades: boolean;
  color: string;
}) {
  const elapsedPath = round.path.filter((point) => point.timeFromFreezeEnd <= currentTime);
  const playerPosition = interpolatedPlayerPosition(round.path, currentTime);
  const pathPoints = elapsedPath.map((point) => `${point.map.x},${point.map.y}`).join(" ");

  return (
    <g>
      {showPath && pathPoints ? (
        <polyline
          points={pathPoints}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinejoin="round"
          strokeLinecap="round"
          opacity="0.88"
        />
      ) : null}
      {showGrenades
        ? round.grenades
            .filter((grenade) => grenadeType === "ALL" || grenade.type === grenadeType)
            .map((grenade, index) => (
              <PlaybackGrenade
                key={`playback-grenade-${round.roundNumber}-${index}`}
                grenade={grenade}
                currentTime={currentTime}
                roundColor={color}
              />
            ))
        : null}
      {showPath && playerPosition ? (
        <g>
          <circle
            cx={playerPosition.x}
            cy={playerPosition.y}
            r="13"
            fill={color}
            stroke="#0c1118"
            strokeWidth="4"
          />
          <circle cx={playerPosition.x} cy={playerPosition.y} r="4" fill="#ffffff" opacity="0.95" />
          <text
            x={playerPosition.x}
            y={playerPosition.y - 18}
            textAnchor="middle"
            fill="#ffffff"
            stroke="#0c1118"
            strokeWidth="4"
            paintOrder="stroke"
            fontSize="18"
            fontWeight="700"
          >
            R{round.roundNumber}
          </text>
          <title>{`R${round.roundNumber} ${currentTime.toFixed(1)}s`}</title>
        </g>
      ) : null}
    </g>
  );
}

function PlaybackGrenade({
  grenade,
  currentTime,
  roundColor
}: {
  grenade: GrenadeEvent;
  currentTime: number;
  roundColor: string;
}) {
  if (currentTime < grenade.throwTimeFromFreezeEnd) {
    return null;
  }

  const color = grenadeColors[grenade.type];
  const elapsedTrajectory = grenade.trajectory.filter(
    (point) => grenade.throwTimeFromFreezeEnd + point.timeFromThrow <= currentTime
  );
  const trajectoryPoints = elapsedTrajectory.map((point) => `${point.map.x},${point.map.y}`).join(" ");
  const currentPosition = grenadePosition(grenade, elapsedTrajectory);
  const detonateTime = grenadeDetonateTime(grenade);
  const hasDetonated = grenade.detonatePosition && currentTime >= detonateTime;

  return (
    <g>
      {trajectoryPoints ? (
        <polyline
          points={trajectoryPoints}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={grenade.trajectorySource === "estimated" ? "10 8" : undefined}
          opacity="0.95"
        />
      ) : null}
      {currentPosition && !hasDetonated ? (
        <circle cx={currentPosition.x} cy={currentPosition.y} r="7" fill={color} stroke={roundColor} strokeWidth="3">
          <title>{`${grenade.type} ${currentTime.toFixed(1)}s`}</title>
        </circle>
      ) : null}
      {hasDetonated && grenade.detonatePosition ? (
        <g>
          <circle
            cx={grenade.detonatePosition.map.x}
            cy={grenade.detonatePosition.map.y}
            r="12"
            fill="none"
            stroke={color}
            strokeWidth="4"
          />
          <path
            d={`M ${grenade.detonatePosition.map.x - 8} ${grenade.detonatePosition.map.y - 8} L ${
              grenade.detonatePosition.map.x + 8
            } ${grenade.detonatePosition.map.y + 8} M ${grenade.detonatePosition.map.x + 8} ${
              grenade.detonatePosition.map.y - 8
            } L ${grenade.detonatePosition.map.x - 8} ${grenade.detonatePosition.map.y + 8}`}
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
          >
            <title>{`${grenade.type} detonate ${detonateTime.toFixed(1)}s`}</title>
          </path>
        </g>
      ) : null}
    </g>
  );
}

function interpolatedPlayerPosition(path: TrajectoryPoint[], currentTime: number): MapPoint | null {
  if (path.length === 0) return null;
  if (currentTime <= path[0].timeFromFreezeEnd) return path[0].map;
  for (let index = 1; index < path.length; index++) {
    const previous = path[index - 1];
    const next = path[index];
    if (currentTime <= next.timeFromFreezeEnd) {
      return interpolateMap(previous.map, next.map, progress(previous.timeFromFreezeEnd, next.timeFromFreezeEnd, currentTime));
    }
  }
  return path[path.length - 1].map;
}

function grenadePosition(grenade: GrenadeEvent, elapsedTrajectory: GrenadeTrajectoryPoint[]): MapPoint | null {
  if (elapsedTrajectory.length > 0) {
    return elapsedTrajectory[elapsedTrajectory.length - 1].map;
  }
  return grenade.throwPosition.map;
}

function grenadeDetonateTime(grenade: GrenadeEvent): number {
  const last = grenade.trajectory[grenade.trajectory.length - 1];
  if (last) {
    return grenade.throwTimeFromFreezeEnd + last.timeFromThrow;
  }
  return grenade.throwTimeFromFreezeEnd;
}

function interpolateMap(start: MapPoint, end: MapPoint, amount: number): MapPoint {
  return {
    x: start.x + (end.x - start.x) * amount,
    y: start.y + (end.y - start.y) * amount,
    layer: start.layer
  };
}

function progress(start: number, end: number, current: number): number {
  if (end <= start) return 1;
  return Math.min(1, Math.max(0, (current - start) / (end - start)));
}

function roundColor(round: RoundAnalysis, index: number): string {
  const base = sideColors[round.side] ?? sideColors.UNKNOWN;
  if (index === 0) return base;
  const palette = ["#ff6b6b", "#8ce99a", "#74c0fc", "#ffd43b", "#da77f2", "#63e6be", "#ffa94d"];
  return palette[(index - 1) % palette.length];
}
