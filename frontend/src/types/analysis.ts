/**
 * Frontend type definitions for analysis data structures.
 */

export interface WorldCoordinates {
  x: number;
  y: number;
  z: number;
}

export interface MapCoordinates {
  x: number;
  y: number;
  layer: string;
}

export interface Position {
  world: WorldCoordinates;
  map: MapCoordinates;
}

export interface PathPoint {
  tick: number;
  timeFromFreezeEnd: number;
  world: WorldCoordinates;
  map: MapCoordinates;
  alive: boolean;
  velocity?: number | null;
}

export interface TrajectoryPoint {
  timeFromThrow: number;
  world: WorldCoordinates;
  map: MapCoordinates;
}

export interface Grenade {
  roundNumber: number;
  side: string;
  type: string;
  throwTick: number;
  throwTimeFromFreezeEnd: number;
  throwPosition: Position;
  detonatePosition: Position;
  trajectory: TrajectoryPoint[];
}

export interface Round {
  roundNumber: number;
  side: string;
  valid: boolean;
  freezeEndTick: number;
  equipmentValue?: number | null;
  roundType?: string | null;
  path: PathPoint[];
  grenades: Grenade[];
}

export interface GrenadeStats {
  smoke: number;
  flash: number;
  he: number;
  molotov: number;
  incendiary: number;
  unknown: number;
}

export interface Summary {
  totalRounds: number;
  validRounds: number;
  tRounds: number;
  ctRounds: number;
  grenades: GrenadeStats;
}

export interface Meta {
  demoFile: string;
  game: string;
  map: string;
  targetSteam64: string;
  targetName: string;
  windowSeconds: number;
  tickRate: number;
}

export interface AnalysisResult {
  meta: Meta;
  summary: Summary;
  rounds: Round[];
}

export interface AnalyzeResponse {
  taskId: string;
  result: AnalysisResult;
}

export interface MapConfig {
  map: string;
  radarImage: string;
  width: number;
  height: number;
  posX: number;
  posY: number;
  scale: number;
  layers: Array<{
    name: string;
    zMin: number;
    zMax: number;
  }>;
}

export interface Player {
  name: string;
  steam64: string;
}

export interface ErrorDetail {
  detail: string;
  players?: Player[];
}
