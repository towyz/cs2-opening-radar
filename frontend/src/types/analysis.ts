export type Side = "T" | "CT" | "UNKNOWN";
export type GrenadeType = "smoke" | "flash" | "he" | "molotov" | "incendiary" | "unknown";

export interface WorldPoint {
  x: number;
  y: number;
  z: number;
}

export interface MapPoint {
  x: number;
  y: number;
  layer: string;
}

export interface TrajectoryPoint {
  tick: number;
  timeFromFreezeEnd: number;
  world: WorldPoint;
  map: MapPoint;
  alive: boolean;
  velocity: number | null;
}

export interface GrenadeTrajectoryPoint {
  tick: number;
  timeFromThrow: number;
  world: WorldPoint;
  map: MapPoint;
}

export interface GrenadeEvent {
  roundNumber: number;
  side: Side;
  type: GrenadeType;
  throwTick: number;
  throwTimeFromFreezeEnd: number;
  throwPosition: {
    world: WorldPoint;
    map: MapPoint;
  };
  detonatePosition: {
    world: WorldPoint;
    map: MapPoint;
  } | null;
  trajectorySource: "parsed" | "estimated" | "missing";
  trajectory: GrenadeTrajectoryPoint[];
}

export interface RoundAnalysis {
  roundNumber: number;
  side: Side;
  valid: boolean;
  invalidReason: string | null;
  freezeEndTick: number | null;
  windowEndTick: number | null;
  timeWindowSource:
    | "freeze_end_event"
    | "round_officially_started_event"
    | "round_start_plus_freeze_time"
    | "unknown";
  equipmentValue: number | null;
  roundType: string | null;
  path: TrajectoryPoint[];
  grenades: GrenadeEvent[];
}

export interface AnalysisResult {
  meta: {
    demoFile: string;
    game: "CS2";
    map: string;
    targetSteam64: string;
    targetName: string | null;
    windowSeconds: number;
    tickRate: number | null;
    parser: {
      name: string;
      version: string;
    };
  };
  summary: {
    totalRounds: number;
    validRounds: number;
    tRounds: number;
    ctRounds: number;
    grenades: Record<GrenadeType, number>;
  };
  players: Array<{
    name: string;
    steam64: string;
  }>;
  rounds: RoundAnalysis[];
}

