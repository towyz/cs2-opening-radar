"""
Main analyzer module that orchestrates demo analysis.
"""

import uuid
from pathlib import Path
from typing import Optional, List

from app.core.demo_loader import DemoLoader
from app.core.round_extractor import RoundExtractor
from app.core.player_path import PlayerPathExtractor
from app.core.grenade_extractor import GrenadeExtractor
from app.core.map_mapper import MapMapper
from app.core.summary_builder import SummaryBuilder
from app.models.analysis_result import (
    AnalysisResult,
    Meta,
    Round,
    PathPoint,
    Grenade,
    WorldCoordinates,
    MapCoordinates,
    Position,
    TrajectoryPoint,
)
from app.config import settings


def analyze_demo(
    demo_path: str,
    map_name: str,
    target_steam64: str,
    window_seconds: int = 30,
) -> AnalysisResult:
    """Main analysis function.
    
    Args:
        demo_path: Path to .dem file
        map_name: Map name (e.g., "de_dust2")
        target_steam64: Target player Steam64 ID
        window_seconds: Analysis window duration in seconds
        
    Returns:
        AnalysisResult object
        
    Raises:
        ValueError: If map not supported or demo is invalid
        FileNotFoundError: If demo file not found
    """
    # Validate map
    if map_name not in settings.supported_maps:
        raise ValueError(f"Map {map_name} not supported. Supported: {settings.supported_maps}")
    
    # Load demo
    demo_loader = DemoLoader(demo_path)
    
    # Verify map
    demo_map = demo_loader.get_map_name()
    if demo_map != map_name.lower():
        raise ValueError(
            f"Demo map {demo_map} does not match requested map {map_name.lower()}"
        )
    
    # Load map configuration
    map_config_path = settings.maps_dir / map_name / "map.json"
    if not map_config_path.exists():
        raise FileNotFoundError(f"Map config not found: {map_config_path}")
    
    map_mapper = MapMapper(str(map_config_path))
    
    # Find target player
    target_player = demo_loader.get_player_by_steam64(target_steam64)
    if target_player is None:
        players = demo_loader.get_players()
        raise ValueError(f"Player {target_steam64} not found in demo. Available players: {players}")
    
    target_name = target_player.get("name", "Unknown")
    
    # Extract rounds
    round_extractor = RoundExtractor(demo_loader)
    valid_rounds_tuples = round_extractor.get_valid_rounds(target_steam64)
    
    # Extract paths and grenades for each round
    path_extractor = PlayerPathExtractor(demo_loader, map_mapper)
    grenade_extractor = GrenadeExtractor(demo_loader, map_mapper)
    
    rounds_data = []
    all_grenades = []
    
    for round_number, round_raw_data, freeze_end_tick in valid_rounds_tuples:
        # Extract path for this round
        path_points_raw = path_extractor.extract_path_for_round(
            target_steam64, freeze_end_tick, window_seconds
        )
        
        # Convert to PathPoint objects
        path_points = []
        for point in path_points_raw:
            path_point = PathPoint(
                tick=point["tick"],
                time_from_freeze_end=point["time_from_freeze_end"],
                world=WorldCoordinates(
                    x=point["world_x"],
                    y=point["world_y"],
                    z=point["world_z"],
                ),
                map=MapCoordinates(
                    x=point["map_x"],
                    y=point["map_y"],
                    layer=point["layer"],
                ),
                alive=point["alive"],
                velocity=point.get("velocity"),
            )
            path_points.append(path_point)
        
        # Extract grenades for this round
        grenades_raw = grenade_extractor.extract_grenades_for_round(
            target_steam64, freeze_end_tick, window_seconds
        )
        
        # Convert to Grenade objects
        grenades = []
        for gren in grenades_raw:
            grenade_obj = Grenade(
                round_number=round_number,
                side="T",  # TODO: Determine from round data
                type=gren["type"],
                throw_tick=gren["throw_tick"],
                throw_time_from_freeze_end=gren["time_from_freeze_end"],
                throw_position=Position(
                    world=WorldCoordinates(
                        x=gren["throw_world_x"],
                        y=gren["throw_world_y"],
                        z=gren["throw_world_z"],
                    ),
                    map=MapCoordinates(
                        x=gren["throw_map_x"],
                        y=gren["throw_map_y"],
                        layer=gren["throw_layer"],
                    ),
                ),
                detonate_position=Position(
                    world=WorldCoordinates(
                        x=gren["detonate_world_x"],
                        y=gren["detonate_world_y"],
                        z=gren["detonate_world_z"],
                    ),
                    map=MapCoordinates(
                        x=gren["detonate_map_x"],
                        y=gren["detonate_map_y"],
                        layer=gren["detonate_layer"],
                    ),
                ),
                trajectory=gren.get("trajectory", []),
            )
            grenades.append(grenade_obj)
            all_grenades.append(grenades)
        
        # Get player side
        side = path_extractor.get_player_side(target_steam64, round_raw_data)
        
        # Create Round object
        round_obj = Round(
            round_number=round_number,
            side=side,
            valid=True,
            freeze_end_tick=freeze_end_tick,
            equipment_value=None,  # TODO: Extract from demo
            round_type=None,  # TODO: Classify round type
            path=path_points,
            grenades=grenades,
        )
        rounds_data.append(round_obj)
    
    # Build summary
    summary_builder = SummaryBuilder()
    # TODO: Fix summary builder to work with Round objects
    summary = summary_builder.build_summary(
        [{"valid": r.valid, "side": r.side} for r in rounds_data],
        all_grenades,
    )
    
    # Build metadata
    meta = Meta(
        demo_file=Path(demo_path).name,
        game=settings.supported_game,
        map=map_name,
        target_steam64=target_steam64,
        target_name=target_name,
        window_seconds=window_seconds,
        tick_rate=demo_loader.get_tick_rate(),
    )
    
    # Create result
    result = AnalysisResult(
        meta=meta,
        summary=summary,
        rounds=rounds_data,
    )
    
    return result


def save_result(result: AnalysisResult, output_dir: Optional[Path] = None) -> Path:
    """Save analysis result to JSON file.
    
    Args:
        result: AnalysisResult object
        output_dir: Directory to save to (defaults to settings.results_dir)
        
    Returns:
        Path to saved JSON file
    """
    if output_dir is None:
        output_dir = settings.results_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    task_id = str(uuid.uuid4())
    output_path = output_dir / f"{task_id}.json"
    
    # Write JSON
    with open(output_path, "w") as f:
        f.write(result.json())
    
    return output_path
