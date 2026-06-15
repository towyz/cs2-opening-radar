"""
Player path extraction module for analyzing player movement.
"""

from typing import Optional, List, Dict, Any
from app.core.demo_loader import DemoLoader
from app.core.map_mapper import MapMapper
from app.config import settings


class PlayerPathExtractor:
    """Extracts player movement paths from demo data."""
    
    def __init__(self, demo_loader: DemoLoader, map_mapper: MapMapper):
        """Initialize with demo loader and map mapper.
        
        Args:
            demo_loader: Initialized DemoLoader instance
            map_mapper: Initialized MapMapper instance
        """
        self.demo_loader = demo_loader
        self.map_mapper = map_mapper
        self.tick_rate = demo_loader.get_tick_rate()
    
    def extract_path_for_round(
        self,
        target_steam64: str,
        freeze_end_tick: int,
        window_seconds: int,
    ) -> List[Dict[str, Any]]:
        """Extract player path for a round window.
        
        Args:
            target_steam64: Target player's Steam64 ID
            freeze_end_tick: Tick when freeze ended
            window_seconds: Duration of window in seconds
            
        Returns:
            List of path point dictionaries
        """
        frames = self.demo_loader.get_frames()
        window_ticks = int(window_seconds * self.tick_rate)
        end_tick = freeze_end_tick + window_ticks
        
        tick_duration = 1.0 / self.tick_rate
        sample_interval_ticks = int(settings.sample_interval_seconds * self.tick_rate)
        
        path_points = []
        last_sampled_tick = None
        
        for frame in frames:
            if frame is None:
                continue
            
            frame_tick = frame.get("tick") if hasattr(frame, "get") else None
            if frame_tick is None:
                continue
            
            # Only process frames within the window
            if frame_tick < freeze_end_tick or frame_tick > end_tick:
                continue
            
            # Sample at regular intervals
            if last_sampled_tick is not None:
                if frame_tick - last_sampled_tick < sample_interval_ticks:
                    continue
            
            last_sampled_tick = frame_tick
            
            # Extract player position
            if hasattr(frame, "player_states"):
                for player_state in frame.player_states:
                    if player_state is not None:
                        player_steam64 = player_state.get("steamID") or player_state.get("steam64")
                        
                        if player_steam64 == target_steam64:
                            world_x = player_state.get("x")
                            world_y = player_state.get("y")
                            world_z = player_state.get("z")
                            alive = player_state.get("alive", True)
                            velocity = player_state.get("velocity")
                            
                            if world_x is not None and world_y is not None:
                                # Convert to map coordinates
                                map_x, map_y, layer = self.map_mapper.world_to_map(
                                    world_x, world_y, world_z or 0
                                )
                                
                                time_from_freeze_end = (frame_tick - freeze_end_tick) * tick_duration
                                
                                path_points.append({
                                    "tick": frame_tick,
                                    "time_from_freeze_end": time_from_freeze_end,
                                    "world_x": world_x,
                                    "world_y": world_y,
                                    "world_z": world_z or 0,
                                    "map_x": map_x,
                                    "map_y": map_y,
                                    "layer": layer,
                                    "alive": alive,
                                    "velocity": velocity,
                                })
        
        return path_points
    
    def get_player_side(self, target_steam64: str, round_data: Dict[str, Any]) -> str:
        """Determine player's side (T or CT) for a round.
        
        Args:
            target_steam64: Target player's Steam64 ID
            round_data: Round data dictionary
            
        Returns:
            "T", "CT", or "UNKNOWN"
        """
        # This would need to be extracted from frame data
        # For now, return UNKNOWN as placeholder
        # Real implementation would check frame.teams or similar
        return "UNKNOWN"
