"""
Data models for analysis results following the standard output structure.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorldCoordinates(BaseModel):
    """3D world coordinates."""
    x: float
    y: float
    z: float


class MapCoordinates(BaseModel):
    """2D map radar coordinates."""
    x: float
    y: float
    layer: str = "default"


class PathPoint(BaseModel):
    """A single point on a player's path."""
    tick: int
    time_from_freeze_end: float = Field(..., alias="timeFromFreezeEnd")
    world: WorldCoordinates
    map: MapCoordinates
    alive: bool
    velocity: Optional[float] = None

    class Config:
        populate_by_name = True


class TrajectoryPoint(BaseModel):
    """A single point on a grenade trajectory."""
    time_from_throw: float = Field(..., alias="timeFromThrow")
    world: WorldCoordinates
    map: MapCoordinates

    class Config:
        populate_by_name = True


class Position(BaseModel):
    """A position with both world and map coordinates."""
    world: WorldCoordinates
    map: MapCoordinates


class Grenade(BaseModel):
    """A single grenade throw."""
    round_number: int = Field(..., alias="roundNumber")
    side: str  # T or CT
    type: str  # smoke, flash, he, molotov, incendiary, unknown
    throw_tick: int = Field(..., alias="throwTick")
    throw_time_from_freeze_end: float = Field(..., alias="throwTimeFromFreezeEnd")
    throw_position: Position = Field(..., alias="throwPosition")
    detonate_position: Position = Field(..., alias="detonatePosition")
    trajectory: List[TrajectoryPoint]

    class Config:
        populate_by_name = True


class Round(BaseModel):
    """A single round's analysis data."""
    round_number: int = Field(..., alias="roundNumber")
    side: str  # T, CT, or UNKNOWN
    valid: bool
    freeze_end_tick: int = Field(..., alias="freezeEndTick")
    equipment_value: Optional[int] = Field(None, alias="equipmentValue")
    round_type: Optional[str] = Field(None, alias="roundType")
    path: List[PathPoint]
    grenades: List[Grenade]

    class Config:
        populate_by_name = True


class GrenadeStats(BaseModel):
    """Grenade usage statistics."""
    smoke: int = 0
    flash: int = 0
    he: int = 0
    molotov: int = 0
    incendiary: int = 0
    unknown: int = 0


class Summary(BaseModel):
    """Summary statistics for the analysis."""
    total_rounds: int = Field(..., alias="totalRounds")
    valid_rounds: int = Field(..., alias="validRounds")
    t_rounds: int = Field(..., alias="tRounds")
    ct_rounds: int = Field(..., alias="ctRounds")
    grenades: GrenadeStats

    class Config:
        populate_by_name = True


class Meta(BaseModel):
    """Metadata about the analysis."""
    demo_file: str = Field(..., alias="demoFile")
    game: str = "CS2"
    map: str
    target_steam64: str = Field(..., alias="targetSteam64")
    target_name: str = Field(..., alias="targetName")
    window_seconds: int = Field(..., alias="windowSeconds")
    tick_rate: int = Field(..., alias="tickRate")

    class Config:
        populate_by_name = True


class AnalysisResult(BaseModel):
    """Complete analysis result with all extracted data."""
    meta: Meta
    summary: Summary
    rounds: List[Round]

    class Config:
        populate_by_name = True

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override to use alias names in output."""
        return super().model_dump(by_alias=True, **kwargs)

    def json(self, **kwargs) -> str:
        """Override to use alias names in JSON output."""
        return super().model_dump_json(by_alias=True, **kwargs)


class Player(BaseModel):
    """A player info response."""
    name: str
    steam64: str


class ErrorResponse(BaseModel):
    """Error response format."""
    detail: str
    players: Optional[List[Player]] = None


class AnalyzeRequest(BaseModel):
    """Request body for demo analysis."""
    steam64: str
    map_name: str = "de_dust2"
    window_seconds: int = 30


class AnalyzeResponse(BaseModel):
    """Response for demo analysis."""
    task_id: str = Field(..., alias="taskId")
    result: AnalysisResult

    class Config:
        populate_by_name = True
