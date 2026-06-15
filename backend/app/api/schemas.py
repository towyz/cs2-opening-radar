"""
API request and response schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class AnalyzeRequestSchema(BaseModel):
    """Schema for demo analysis request."""
    steam64: str = Field(..., description="Target player Steam64 ID")
    map_name: str = Field(default="de_dust2", description="Map name")
    window_seconds: int = Field(default=30, description="Analysis window in seconds")


class PlayerSchema(BaseModel):
    """Schema for player info."""
    name: str
    steam64: str


class ErrorDetailSchema(BaseModel):
    """Schema for error details."""
    detail: str
    players: Optional[List[PlayerSchema]] = None


class HealthCheckSchema(BaseModel):
    """Schema for health check response."""
    status: str
