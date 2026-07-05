from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas import AnalyzeLocalRequest, PerfectWorldRecentRequest
from app.config import get_settings
from app.models.analysis_result import AnalysisResult
from app.services.local_demo_store import list_local_demos, prepare_local_demo
from app.services.parser_runner import ParserRunError, run_parser
from app.services.perfectworld_demo_importer import PerfectWorldCredentialsError, import_recent_dust2_demos
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


@router.post("/perfectworld/recent-dust2-demos")
async def perfectworld_recent_dust2_demos(request: PerfectWorldRecentRequest) -> dict[str, object]:
    settings = get_settings()
    if request.steam64:
        validate_analysis_request(settings.supported_map, request.steam64, request.window_seconds)
    if not (request.uid or request.steam64):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "uid or steam64 is required"},
        )
    if request.limit < 1 or request.limit > 10:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "limit must be between 1 and 10"},
        )

    try:
        target_uid = (request.steam64 or request.uid or "").strip()
        report = import_recent_dust2_demos(
            perfect_uid=target_uid,
            steam64=request.steam64.strip() if request.steam64 else None,
            access_token=request.access_token,
            pwa_jt=request.pwa_jt,
            login_steam64=request.login_steam64,
            limit=request.limit,
            window_seconds=request.window_seconds,
            uploads_dir=settings.uploads_dir,
            results_dir=settings.results_dir,
            download_dir=settings.perfectworld_demos_dir,
            parser_bin=settings.parser_bin,
            map_config_path=settings.map_config_path,
            signer_bridge_path=settings.perfectworld_signer_bridge_path,
        )
    except PerfectWorldCredentialsError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PERFECTWORLD_CREDENTIALS_REQUIRED",
                "message": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PERFECTWORLD_REQUEST_FAILED",
                "message": str(exc),
            },
        ) from exc
    return {
        "results": [item.result.model_dump(mode="json") for item in report.imported if item.result is not None],
        "imported": [
            {
                "matchId": item.match_id,
                "path": str(item.source_path),
                "demoFile": item.result.meta.demoFile if item.result is not None else item.source_path.name,
            }
            for item in report.imported
        ],
        "scanned": report.scanned,
        "downloaded": report.downloaded,
        "skipped": report.skipped,
        "source": report.source,
        "notice": report.notice,
    }


def validate_analysis_request(map_name: str, steam64: str, window_seconds: int) -> None:
    settings = get_settings()
    if map_name != settings.supported_map:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNSUPPORTED_MAP", "message": "MVP only supports de_dust2"},
        )
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
