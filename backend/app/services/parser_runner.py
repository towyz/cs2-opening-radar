import json
import subprocess
from pathlib import Path


class ParserRunError(Exception):
    def __init__(self, message: str, detail: dict[str, object] | None = None):
        super().__init__(message)
        self.detail = detail or {"code": "UNKNOWN_ERROR", "message": message}


def run_parser(
    parser_bin: Path,
    demo_path: Path,
    steam64: str,
    map_name: str,
    map_config_path: Path,
    output_path: Path,
    window_seconds: int = 30,
) -> None:
    if not parser_bin.exists():
        raise ParserRunError(
            "Go parser binary is missing",
            {
                "code": "DEMO_PARSE_FAILED",
                "message": f"Go parser binary not found at {parser_bin}",
            },
        )

    cmd = [
        str(parser_bin),
        "--demo",
        str(demo_path),
        "--map",
        map_name,
        "--steam64",
        steam64,
        "--window",
        str(window_seconds),
        "--map-config",
        str(map_config_path),
        "--out",
        str(output_path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        try:
            detail = json.loads(stderr)
        except json.JSONDecodeError:
            detail = {"code": "DEMO_PARSE_FAILED", "message": stderr or "Go parser failed"}
        raise ParserRunError("Go parser failed", detail=detail)

