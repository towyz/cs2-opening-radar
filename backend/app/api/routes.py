from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models.analysis_result import AnalysisResult
from app.services.parser_runner import ParserRunError, run_parser
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
    if map_name != settings.supported_map:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNSUPPORTED_MAP", "message": "MVP only supports de_dust2"},
        )
    if not demo.filename or Path(demo.filename).suffix.lower() != ".dem":
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "Uploaded file must be a .dem file"},
        )
    if not steam64.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_ARGUMENT", "message": "steam64 is required"},
        )

    task_id = str(uuid4())
    upload_path = settings.uploads_dir / f"{task_id}.dem"
    output_path = settings.results_dir / f"{task_id}.json"

    with upload_path.open("wb") as out:
        while chunk := await demo.read(1024 * 1024):
            out.write(chunk)

    try:
        run_parser(
            parser_bin=settings.parser_bin,
            demo_path=upload_path,
            steam64=steam64.strip(),
            map_name=map_name,
            map_config_path=settings.map_config_path,
            output_path=output_path,
            window_seconds=window_seconds,
        )
    except ParserRunError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    result = AnalysisResult.model_validate(read_result(output_path))
    return {"taskId": task_id, "result": result.model_dump(mode="json")}

