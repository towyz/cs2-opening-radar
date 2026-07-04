import type {
  GrenadeEvent,
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
  const playerPosition = interpolatedPlayerPosition(round.path, currentTime);

  return (
    <g>
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
  const detonateTime = grenadeDetonateTime(grenade);
  const currentPosition = interpolatedGrenadePosition(grenade, currentTime);
  const effectDuration = grenadeEffectDuration(grenade.type);
  const effectProgress = progress(detonateTime, detonateTime + effectDuration, currentTime);
  const showEffect =
    Boolean(grenade.detonatePosition) &&
    currentTime >= detonateTime &&
    currentTime <= detonateTime + effectDuration;
  const isInFlight = currentPosition && currentTime < detonateTime;

  return (
    <g>
      {isInFlight ? (
        <GrenadeIcon
          type={grenade.type}
          position={currentPosition}
          color={color}
          roundColor={roundColor}
          label={`${grenade.type} ${currentTime.toFixed(1)}s`}
        />
      ) : null}
      {showEffect && grenade.detonatePosition ? (
        <GrenadeEffect
          type={grenade.type}
          position={grenade.detonatePosition.map}
          color={color}
          progress={effectProgress}
          label={`${grenade.type} effect ${detonateTime.toFixed(1)}s`}
        />
      ) : null}
    </g>
  );
}

function GrenadeIcon({
  type,
  position,
  color,
  roundColor,
  label
}: {
  type: GrenadeType;
  position: MapPoint;
  color: string;
  roundColor: string;
  label: string;
}) {
  const icon = grenadeIconType(type);

  return (
    <g transform={`translate(${position.x} ${position.y})`}>
      <circle r="15" fill="#0c1118" opacity="0.82" />
      <circle r="13" fill={color} stroke={roundColor} strokeWidth="3" />
      {icon === "flash" ? (
        <g stroke="#111820" strokeWidth="3" strokeLinecap="round">
          <path d="M -2 -9 L -7 1 H -1 L -4 9 L 8 -4 H 2 L 6 -9 Z" fill="#fffde7" strokeLinejoin="round" />
        </g>
      ) : null}
      {icon === "fire" ? (
        <path
          d="M 0 -10 C 7 -3 8 4 3 9 C 8 7 10 1 7 -5 C 13 1 12 12 0 12 C -10 12 -13 3 -6 -5 C -6 1 -2 1 0 -10 Z"
          fill="#fff3bf"
          stroke="#111820"
          strokeLinejoin="round"
          strokeWidth="2.5"
        />
      ) : null}
      {icon === "smoke" ? (
        <g fill="#edf2f7" stroke="#111820" strokeWidth="2">
          <circle cx="-4" cy="1" r="5" />
          <circle cx="2" cy="-3" r="6" />
          <circle cx="6" cy="3" r="4" />
        </g>
      ) : null}
      {icon === "he" ? (
        <g fill="#ffebee" stroke="#111820" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5">
          <path d="M -6 -5 H 5 L 8 -1 V 7 L 3 10 H -5 L -9 5 V -1 Z" />
          <path d="M 2 -7 L 6 -11" />
          <path d="M 7 -10 L 10 -7" />
        </g>
      ) : null}
      <title>{label}</title>
    </g>
  );
}

function GrenadeEffect({
  type,
  position,
  color,
  progress,
  label
}: {
  type: GrenadeType;
  position: MapPoint;
  color: string;
  progress: number;
  label: string;
}) {
  const icon = grenadeIconType(type);
  const opacity = Math.max(0, 1 - progress);

  if (icon === "smoke") {
    return (
      <g transform={`translate(${position.x} ${position.y})`} opacity={Math.max(0.16, opacity)}>
        {[0, 1, 2, 3].map((index) => {
          const spread = 10 + progress * 38 + index * 5;
          const angle = index * 1.7;
          return (
            <circle
              key={`smoke-puff-${index}`}
              cx={Math.cos(angle) * progress * 16}
              cy={Math.sin(angle) * progress * 13}
              r={spread}
              fill="#cfd8dc"
              opacity={0.28 + (1 - progress) * 0.24}
              stroke="#eceff1"
              strokeWidth="2"
            />
          );
        })}
        <title>{label}</title>
      </g>
    );
  }

  if (icon === "fire") {
    return (
      <g transform={`translate(${position.x} ${position.y})`} opacity={opacity}>
        <circle r={18 + progress * 22} fill="#ff7a1a" opacity="0.28" />
        <path
          d="M 0 -22 C 14 -8 16 9 4 20 C 18 14 22 0 12 -13 C 27 1 23 28 0 29 C -21 29 -27 6 -12 -14 C -12 2 -3 1 0 -22 Z"
          fill="#ffb000"
          stroke="#fff3bf"
          strokeWidth="3"
          strokeLinejoin="round"
          transform={`scale(${0.78 + progress * 0.25})`}
        />
        <title>{label}</title>
      </g>
    );
  }

  if (icon === "flash") {
    return (
      <g transform={`translate(${position.x} ${position.y})`} opacity={opacity}>
        <circle r={20 + progress * 34} fill="#fff176" opacity="0.34" />
        <g stroke="#fffde7" strokeLinecap="round" strokeWidth="5">
          <path d="M 0 -34 V -18" />
          <path d="M 0 18 V 34" />
          <path d="M -34 0 H -18" />
          <path d="M 18 0 H 34" />
          <path d="M -24 -24 L -13 -13" />
          <path d="M 13 13 L 24 24" />
          <path d="M 24 -24 L 13 -13" />
          <path d="M -13 13 L -24 24" />
        </g>
        <title>{label}</title>
      </g>
    );
  }

  return (
    <g transform={`translate(${position.x} ${position.y})`} opacity={opacity}>
      <circle r={18 + progress * 36} fill="none" stroke={color} strokeWidth="5" />
      <circle r={8 + progress * 14} fill={color} opacity="0.3" />
      <path d="M -13 -13 L 13 13 M 13 -13 L -13 13" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" />
      <title>{label}</title>
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

function interpolatedGrenadePosition(grenade: GrenadeEvent, currentTime: number): MapPoint | null {
  if (grenade.trajectory.length === 0) {
    return grenade.throwPosition.map;
  }
  const first = grenade.trajectory[0];
  const firstTime = grenade.throwTimeFromFreezeEnd + first.timeFromThrow;
  if (currentTime <= firstTime) {
    return interpolateMap(grenade.throwPosition.map, first.map, progress(grenade.throwTimeFromFreezeEnd, firstTime, currentTime));
  }
  for (let index = 1; index < grenade.trajectory.length; index++) {
    const previous = grenade.trajectory[index - 1];
    const next = grenade.trajectory[index];
    const previousTime = grenade.throwTimeFromFreezeEnd + previous.timeFromThrow;
    const nextTime = grenade.throwTimeFromFreezeEnd + next.timeFromThrow;
    if (currentTime <= nextTime) {
      return interpolateMap(previous.map, next.map, progress(previousTime, nextTime, currentTime));
    }
  }
  return grenade.trajectory[grenade.trajectory.length - 1].map;
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

function grenadeIconType(type: GrenadeType): "he" | "flash" | "fire" | "smoke" {
  if (type === "flash") return "flash";
  if (type === "molotov" || type === "incendiary") return "fire";
  if (type === "smoke") return "smoke";
  return "he";
}

function grenadeEffectDuration(type: GrenadeType): number {
  if (type === "smoke") return 7;
  if (type === "molotov" || type === "incendiary") return 4;
  if (type === "flash") return 0.9;
  return 1.2;
}

function roundColor(round: RoundAnalysis, index: number): string {
  const base = sideColors[round.side] ?? sideColors.UNKNOWN;
  if (index === 0) return base;
  const palette = ["#ff6b6b", "#8ce99a", "#74c0fc", "#ffd43b", "#da77f2", "#63e6be", "#ffa94d"];
  return palette[(index - 1) % palette.length];
}
