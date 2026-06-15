"""
API routes for demo analysis.
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.api.schemas import AnalyzeRequestSchema, PlayerSchema, ErrorDetailSchema
from app.models.analysis_result import AnalyzeResponse
from app.core.analyzer import analyze_demo, save_result
from app.core.demo_loader import DemoLoader
from app.core.map_mapper import MapMapper


router = APIRouter(tags=["analysis"])


@router.post("/analyze")
async def analyze_uploaded_demo(
    demo: UploadFile = File(...),
    steam64: str = Form(...),
    map_name: str = Form(default="de_dust2"),
    window_seconds: int = Form(default=30),
):
    """Upload demo and analyze player behavior.
    
    Args:
        demo: Demo file (.dem)
        steam64: Target player Steam64
        map_name: Map name (default: de_dust2)
        window_seconds: Analysis window in seconds (default: 30)
        
    Returns:
        Analysis result with task ID
    """
    # Validate file
    if not demo.filename or not demo.filename.endswith(".dem"):
        raise HTTPException(status_code=400, detail="File must be a .dem file")
    
    # Validate map
    if map_name not in settings.supported_maps:
        raise HTTPException(
            status_code=400,
            detail=f"Map {map_name} not supported. Supported: {settings.supported_maps}",
        )
    
    # Save uploaded file
    upload_path = settings.upload_dir / f"{uuid.uuid4()}.dem"
    
    try:
        contents = await demo.read()
        
        # Check file size
        if len(contents) > settings.max_demo_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max {settings.max_demo_size_mb} MB",
            )
        
        with open(upload_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save demo: {str(e)}")
    
    # Analyze demo
    try:
        result = analyze_demo(
            str(upload_path),
            map_name,
            steam64,
            window_seconds,
        )
        
        # Save result
        result_path = save_result(result)
        task_id = result_path.stem
        
        return AnalyzeResponse(
            task_id=task_id,
            result=result,
        )
        
    except ValueError as e:
        # Check if it's a player not found error
        if "not found in demo" in str(e):
            try:
                loader = DemoLoader(str(upload_path))
                players = loader.get_players()
                raise HTTPException(
                    status_code=404,
                    detail={
                        "detail": str(e),
                        "players": [
                            PlayerSchema(name=p["name"], steam64=p["steam64"])
                            for p in players
                        ],
                    },
                )
            except Exception:
                pass
        
        raise HTTPException(status_code=400, detail=str(e))
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Clean up uploaded file
        try:
            upload_path.unlink()
        except Exception:
            pass


@router.get("/results/{task_id}")
async def get_result(task_id: str):
    """Get analysis result by task ID.
    
    Args:
        task_id: Task UUID
        
    Returns:
        Analysis result JSON
    """
    result_path = settings.results_dir / f"{task_id}.json"
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail=f"Result not found: {task_id}")
    
    return FileResponse(result_path, media_type="application/json")


@router.get("/maps/de_dust2/config")
async def get_map_config():
    """Get de_dust2 map configuration.
    
    Returns:
        Map configuration with radar image path and coordinates
    """
    try:
        map_config_path = settings.maps_dir / "de_dust2" / "map.json"
        mapper = MapMapper(str(map_config_path))
        return mapper.get_map_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load map config: {str(e)}")


@router.get("/maps/de_dust2/radar")
async def get_map_radar():
    """Get de_dust2 radar image.
    
    Returns:
        Radar image file
    """
    radar_path = settings.maps_dir / "de_dust2" / "radar.png"
    
    if not radar_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Radar image not found. Place radar.png in backend/app/assets/maps/de_dust2/",
        )
    
    return FileResponse(radar_path, media_type="image/png")
