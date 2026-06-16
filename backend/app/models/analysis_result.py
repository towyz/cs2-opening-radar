from typing import Literal

from pydantic import BaseModel

Side = Literal["T", "CT", "UNKNOWN"]
GrenadeType = Literal["smoke", "flash", "he", "molotov", "incendiary", "unknown"]
TimeWindowSource = Literal[
    "freeze_end_event",
    "round_officially_started_event",
    "round_start_plus_freeze_time",
    "unknown",
]
TrajectorySource = Literal["parsed", "estimated", "missing"]


class WorldPoint(BaseModel):
    x: float
    y: float
    z: float


class MapPoint(BaseModel):
    x: float
    y: float
    layer: str


class PathPoint(BaseModel):
    tick: int
    timeFromFreezeEnd: float
    world: WorldPoint
    map: MapPoint
    alive: bool
    velocity: float | None = None


class GrenadeTrajectoryPoint(BaseModel):
    tick: int
    timeFromThrow: float
    world: WorldPoint
    map: MapPoint


class PositionedPoint(BaseModel):
    world: WorldPoint
    map: MapPoint


class GrenadeEvent(BaseModel):
    roundNumber: int
    side: Side
    type: GrenadeType
    throwTick: int
    throwTimeFromFreezeEnd: float
    throwPosition: PositionedPoint
    detonatePosition: PositionedPoint | None
    trajectorySource: TrajectorySource
    trajectory: list[GrenadeTrajectoryPoint]


class RoundAnalysis(BaseModel):
    roundNumber: int
    side: Side
    valid: bool
    invalidReason: str | None
    freezeEndTick: int | None
    windowEndTick: int | None
    timeWindowSource: TimeWindowSource
    equipmentValue: int | None
    roundType: str | None
    path: list[PathPoint]
    grenades: list[GrenadeEvent]


class ParserMeta(BaseModel):
    name: str
    version: str


class Meta(BaseModel):
    demoFile: str
    game: Literal["CS2"]
    map: str
    targetSteam64: str
    targetName: str | None
    windowSeconds: int
    tickRate: float | None
    parser: ParserMeta


class GrenadeSummary(BaseModel):
    smoke: int = 0
    flash: int = 0
    he: int = 0
    molotov: int = 0
    incendiary: int = 0
    unknown: int = 0


class Summary(BaseModel):
    totalRounds: int
    validRounds: int
    tRounds: int
    ctRounds: int
    grenades: GrenadeSummary


class Player(BaseModel):
    name: str
    steam64: str


class AnalysisResult(BaseModel):
    meta: Meta
    summary: Summary
    players: list[Player]
    rounds: list[RoundAnalysis]

