from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas import AnalyzeLocalRequest, AnalyzePlayerRequest, ImportLocalDemoRequest
from app.config import get_settings
from app.models.analysis_result import AnalysisResult
from app.services.local_demo_store import list_local_demos, prepare_local_demo
from app.services.parser_runner import ParserRunError, run_parser, run_player_scan
from app.services.result_store import read_result

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze")
async def analyze(
    demo: UploadFile = File(...),
    steam64: str = Form(...),
    map_name: str = Form("de_dust2"),
    window_seconds: int = Form(30),
) -> dict[str, object]:
    settings = get_settings()
    validate_analysis_request(map_name, steam64, window_seconds)
    if not demo.filename or Path(demo.filename).suffix.lower() != ".dem":
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "Uploaded file must be a .dem file"},
        )

    task_id = str(uuid4())
    upload_path = settings.uploads_dir / f"{task_id}.dem"
    with upload_path.open("wb") as out:
        while chunk := await demo.read(1024 * 1024):
            out.write(chunk)

    return run_analysis(task_id, upload_path, steam64.strip(), map_name, window_seconds)


@router.post("/import-demo")
async def import_demo(
    demo: UploadFile = File(...),
    map_name: str = Form("de_dust2"),
) -> dict[str, object]:
    settings = get_settings()
    validate_map_request(map_name)
    if not demo.filename or Path(demo.filename).suffix.lower() != ".dem":
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "Uploaded file must be a .dem file"},
        )

    demo_id = str(uuid4())
    upload_path = settings.uploads_dir / imported_demo_filename(demo_id, demo.filename)
    with upload_path.open("wb") as out:
        while chunk := await demo.read(1024 * 1024):
            out.write(chunk)

    players = scan_demo_players(demo_id, upload_path, map_name)
    return {"demo": {"id": demo_id, "name": demo.filename}, "players": players}


@router.get("/local-demos")
async def local_demos() -> dict[str, object]:
    settings = get_settings()
    demos = list_local_demos(settings.local_demo_config_path)
    return {
        "configPath": str(settings.local_demo_config_path),
        "demos": [
            {
                "path": str(demo.path),
                "name": demo.name,
                "size": demo.size,
                "modifiedTime": demo.modifiedTime,
                "kind": demo.kind,
            }
            for demo in demos
        ],
    }


@router.post("/analyze-local")
async def analyze_local(request: AnalyzeLocalRequest) -> dict[str, object]:
    settings = get_settings()
    validate_analysis_request(request.map_name, request.steam64, request.window_seconds)
    task_id = str(uuid4())
    upload_path = settings.uploads_dir / f"{task_id}.dem"
    try:
        prepare_local_demo(
            source_path=Path(request.path),
            config_path=settings.local_demo_config_path,
            upload_path=upload_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "DEMO_FILE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": str(exc)},
        ) from exc

    return run_analysis(
        task_id,
        upload_path,
        request.steam64.strip(),
        request.map_name,
        request.window_seconds,
    )


@router.post("/import-local-demo")
async def import_local_demo(request: ImportLocalDemoRequest) -> dict[str, object]:
    settings = get_settings()
    validate_map_request(request.map_name)
    source_path = Path(request.path)
    demo_id = str(uuid4())
    upload_path = settings.uploads_dir / imported_demo_filename(demo_id, source_path.name)
    try:
        prepare_local_demo(
            source_path=source_path,
            config_path=settings.local_demo_config_path,
            upload_path=upload_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "DEMO_FILE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": str(exc)},
        ) from exc

    players = scan_demo_players(demo_id, upload_path, request.map_name)
    return {"demo": {"id": demo_id, "name": source_path.name}, "players": players}


@router.post("/analyze-player")
async def analyze_player(request: AnalyzePlayerRequest) -> dict[str, object]:
    settings = get_settings()
    validate_analysis_request(request.map_name, request.steam64, request.window_seconds)
    if not request.demo_ids:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "At least one imported demo is required"},
        )

    results: list[dict[str, object]] = []
    task_ids: list[str] = []
    for demo_id in request.demo_ids:
        demo_path = resolve_imported_demo_path(demo_id)
        task_id = str(uuid4())
        task_ids.append(task_id)
        output_path = settings.results_dir / f"{task_id}.json"
        try:
            run_parser(
                parser_bin=settings.parser_bin,
                demo_path=demo_path,
                steam64=request.steam64.strip(),
                map_name=request.map_name,
                map_config_path=settings.map_config_path,
                output_path=output_path,
                window_seconds=request.window_seconds,
            )
        except ParserRunError as exc:
            if isinstance(exc.detail, dict) and exc.detail.get("code") == "TARGET_PLAYER_NOT_FOUND":
                continue
            raise HTTPException(status_code=400, detail=exc.detail) from exc

        result = AnalysisResult.model_validate(read_result(output_path))
        results.append(result.model_dump(mode="json"))

    if not results:
        raise HTTPException(
            status_code=400,
            detail={"code": "TARGET_PLAYER_NOT_FOUND", "message": "Selected player was not found in the imported demos"},
        )
    return {"taskIds": task_ids, "results": results}


def validate_analysis_request(map_name: str, steam64: str, window_seconds: int) -> None:
    validate_map_request(map_name)
    if not steam64.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "steam64 is required"},
        )
    if window_seconds <= 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "window_seconds must be greater than zero"},
        )


def validate_map_request(map_name: str) -> None:
    settings = get_settings()
    if map_name != settings.supported_map:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNSUPPORTED_MAP", "message": "MVP only supports de_dust2"},
        )


def run_analysis(
    task_id: str,
    upload_path: Path,
    steam64: str,
    map_name: str,
    window_seconds: int,
) -> dict[str, object]:
    settings = get_settings()
    output_path = settings.results_dir / f"{task_id}.json"
    try:
        run_parser(
            parser_bin=settings.parser_bin,
            demo_path=upload_path,
            steam64=steam64,
            map_name=map_name,
            map_config_path=settings.map_config_path,
            output_path=output_path,
            window_seconds=window_seconds,
        )
    except ParserRunError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    result = AnalysisResult.model_validate(read_result(output_path))
    return {"taskId": task_id, "result": result.model_dump(mode="json")}


def scan_demo_players(demo_id: str, demo_path: Path, map_name: str) -> list[dict[str, str]]:
    settings = get_settings()
    output_path = settings.results_dir / f"{demo_id}-players.json"
    try:
        run_player_scan(
            parser_bin=settings.parser_bin,
            demo_path=demo_path,
            map_name=map_name,
            map_config_path=settings.map_config_path,
            output_path=output_path,
        )
    except ParserRunError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    payload = read_result(output_path)
    players = payload.get("players", [])
    if not isinstance(players, list):
        return []
    return [
        {"name": str(player.get("name", "")), "steam64": str(player.get("steam64", ""))}
        for player in players
        if isinstance(player, dict) and player.get("steam64")
    ]


def imported_demo_filename(demo_id: str, original_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(original_name).name).strip("._")
    if not safe_name:
        safe_name = "demo.dem"
    if Path(safe_name).suffix.lower() != ".dem":
        safe_name = f"{Path(safe_name).stem}.dem"
    return f"{demo_id}_{safe_name}"


def resolve_imported_demo_path(demo_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", demo_id):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "Invalid imported demo id"},
        )
    settings = get_settings()
    matches = list(settings.uploads_dir.glob(f"{demo_id}_*.dem"))
    if not matches:
        raise HTTPException(
            status_code=400,
            detail={"code": "DEMO_FILE_NOT_FOUND", "message": "Imported demo was not found"},
        )
    return matches[0]
