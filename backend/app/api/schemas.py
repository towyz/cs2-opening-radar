from pydantic import BaseModel

from app.models.analysis_result import AnalysisResult


class AnalyzeResponse(BaseModel):
    taskId: str
    result: AnalysisResult

