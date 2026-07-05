import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SUPPORTED_SUFFIXES = {".dem", ".zip"}


@dataclass(frozen=True)
class LocalDemo:
    path: Path
    name: str
    size: int
    modifiedTime: str
    kind: str


def load_demo_directories(config_path: Path) -> list[Path]:
    if not config_path.exists():
        return []
    with config_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    directories = payload.get("demoDirectories", [])
    if not isinstance(directories, list):
        return []
    return [Path(str(item)).expanduser().resolve() for item in directories if str(item).strip()]


def list_local_demos(config_path: Path) -> list[LocalDemo]:
    demos: list[LocalDemo] = []
    for directory in load_demo_directories(config_path):
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            stat = path.stat()
            demos.append(
                LocalDemo(
                    path=path,
                    name=path.name,
                    size=stat.st_size,
                    modifiedTime=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    kind=path.suffix.lower().lstrip("."),
                )
            )
    return sorted(demos, key=lambda demo: demo.path.stat().st_mtime, reverse=True)


def is_configured_demo_path(path: Path, config_path: Path) -> bool:
    resolved = path.expanduser().resolve()
    for directory in load_demo_directories(config_path):
        try:
            resolved.relative_to(directory)
            return True
        except ValueError:
            continue
    return False


def prepare_local_demo(source_path: Path, config_path: Path, upload_path: Path) -> None:
    source_path = source_path.expanduser().resolve()
    if not is_configured_demo_path(source_path, config_path):
        raise ValueError("Selected demo is not under a configured demo directory")
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError("Selected demo file was not found")
    suffix = source_path.suffix.lower()
    if suffix == ".dem":
        shutil.copyfile(source_path, upload_path)
        return
    if suffix == ".zip":
        extract_dem_from_zip(source_path, upload_path)
        return
    raise ValueError("Selected file must be a .dem or .zip")


def extract_dem_from_zip(source_path: Path, upload_path: Path) -> None:
    with zipfile.ZipFile(source_path) as archive:
        dem_names = [name for name in archive.namelist() if name.lower().endswith(".dem")]
        if not dem_names:
            raise ValueError("Zip archive does not contain a .dem file")
        with archive.open(dem_names[0]) as src, upload_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
