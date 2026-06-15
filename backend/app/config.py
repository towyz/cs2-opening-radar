"""
Application configuration.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App metadata
    app_name: str = "CS2 Opening Analyzer"
    app_version: str = "0.1.0"
    
    # Storage paths
    upload_dir: Path = Path(__file__).parent / "storage" / "uploads"
    results_dir: Path = Path(__file__).parent / "storage" / "results"
    
    # Maps
    maps_dir: Path = Path(__file__).parent / "assets" / "maps"
    
    # API
    api_prefix: str = "/api"
    
    # Demo analysis
    supported_maps: list[str] = ["de_dust2"]
    supported_game: str = "CS2"
    default_window_seconds: int = 30
    max_demo_size_mb: int = 500
    
    # Demo parsing
    tick_rate_fallback: int = 64  # Fallback if tick rate can't be determined
    
    # Path sampling
    sample_interval_seconds: float = 0.2  # Sample one point per 0.2 seconds
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
