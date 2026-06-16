from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    backend_dir: Path = Path(__file__).resolve().parents[1]
    repo_dir: Path = Path(__file__).resolve().parents[2]
    supported_map: str = "de_dust2"
    default_window_seconds: int = 30

    @property
    def storage_dir(self) -> Path:
        return self.backend_dir / "storage"

    @property
    def uploads_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.storage_dir / "results"

    @property
    def parser_bin(self) -> Path:
        return self.repo_dir / "parser-go" / "bin" / "cs2-demo-parser.exe"

    @property
    def map_config_path(self) -> Path:
        return self.repo_dir / "assets" / "maps" / "de_dust2" / "map.json"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    return settings
