from pydantic import BaseModel

from app.models.analysis_result import AnalysisResult


class AnalyzeResponse(BaseModel):
    taskId: str
    result: AnalysisResult


class LocalDemoItem(BaseModel):
    path: str
    name: str
    size: int
    modifiedTime: str
    kind: str


class LocalDemoListResponse(BaseModel):
    configPath: str
    demos: list[LocalDemoItem]


class AnalyzeLocalRequest(BaseModel):
    path: str
    steam64: str
    map_name: str = "de_dust2"
    window_seconds: int = 30


class PerfectWorldRecentRequest(BaseModel):
    uid: str | None = None
    steam64: str | None = None
    access_token: str | None = None
    pwa_jt: str | None = None
    login_steam64: str | None = None
    limit: int = 5
    window_seconds: int = 30
