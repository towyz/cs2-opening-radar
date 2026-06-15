"""
Grenade extraction module for analyzing grenade usage.
"""

from typing import Optional, List, Dict, Any
from app.core.demo_loader import DemoLoader
from app.core.map_mapper import MapMapper
from app.config import settings


class GrenadeExtractor:
    """Extracts grenade data from demo."""
    
    # Grenade type classification
    GRENADE_TYPES = {
        "smoke": ["smokegrenade", "smoke"],
        "flash": ["flashbang", "flash"],
        "he": ["hegrenade", "he"],
        "molotov": ["molotov"],
        "incendiary": ["incendiary"],
    }
    
    def __init__(self, demo_loader: DemoLoader, map_mapper: MapMapper):
        """Initialize with demo loader and map mapper.
        
        Args:
            demo_loader: Initialized DemoLoader instance
            map_mapper: Initialized MapMapper instance
        """
        self.demo_loader = demo_loader
        self.map_mapper = map_mapper
        self.tick_rate = demo_loader.get_tick_rate()
    
    @classmethod
    def classify_grenade(cls, weapon_name: Optional[str]) -> str:
        """Classify grenade type from weapon name.
        
        Args:
            weapon_name: Weapon name from demo
            
        Returns:
            Grenade type: smoke, flash, he, molotov, incendiary, or unknown
        """
        if weapon_name is None:
            return "unknown"
        
        weapon_lower = weapon_name.lower()
        
        for gtype, keywords in cls.GRENADE_TYPES.items():
            for keyword in keywords:
                if keyword in weapon_lower:
                    return gtype
        
        return "unknown"
    
    def extract_grenades_for_round(
        self,
        target_steam64: str,
        freeze_end_tick: int,
        window_seconds: int,
    ) -> List[Dict[str, Any]]:
        """Extract grenades thrown by player in a round window.
        
        Args:
            target_steam64: Target player's Steam64 ID
            freeze_end_tick: Tick when freeze ended
            window_seconds: Duration of window in seconds
            
        Returns:
            List of grenade dictionaries
        """
        grenades_list = self.demo_loader.get_grenades()
        window_ticks = int(window_seconds * self.tick_rate)
        end_tick = freeze_end_tick + window_ticks
        
        tick_duration = 1.0 / self.tick_rate
        grenades = []
        
        for grenade in grenades_list:
            if grenade is None:
                continue
            
            # Check if thrown by target player
            thrower_steam64 = grenade.get("throwerSteamID") or grenade.get("thrower_steam64")
            if thrower_steam64 != target_steam64:
                continue
            
            # Check if within time window
            throw_tick = grenade.get("tick") or grenade.get("throw_tick")
            if throw_tick is None or throw_tick < freeze_end_tick or throw_tick > end_tick:
                continue
            
            # Extract grenade data
            grenade_type = self.classify_grenade(grenade.get("weapon"))
            
            # Throw position
            throw_x = grenade.get("throwX") or grenade.get("throw_x") or grenade.get("x")
            throw_y = grenade.get("throwY") or grenade.get("throw_y") or grenade.get("y")
            throw_z = grenade.get("throwZ") or grenade.get("throw_z") or grenade.get("z", 0)
            
            # Detonate position
            det_x = grenade.get("detonateX") or grenade.get("detonate_x") or grenade.get("detonX")
            det_y = grenade.get("detonateY") or grenade.get("detonate_y") or grenade.get("detonY")
            det_z = grenade.get("detonateZ") or grenade.get("detonate_z") or grenade.get("detonZ", 0)
            
            # Only include if we have both positions
            if (throw_x is None or throw_y is None or 
                det_x is None or det_y is None):
                continue
            
            # Convert to map coordinates
            throw_map_x, throw_map_y, throw_layer = self.map_mapper.world_to_map(
                throw_x, throw_y, throw_z
            )
            det_map_x, det_map_y, det_layer = self.map_mapper.world_to_map(
                det_x, det_y, det_z
            )
            
            time_from_freeze_end = (throw_tick - freeze_end_tick) * tick_duration
            
            grenades.append({
                "type": grenade_type,
                "throw_tick": throw_tick,
                "time_from_freeze_end": time_from_freeze_end,
                "throw_world_x": throw_x,
                "throw_world_y": throw_y,
                "throw_world_z": throw_z,
                "throw_map_x": throw_map_x,
                "throw_map_y": throw_map_y,
                "throw_layer": throw_layer,
                "detonate_world_x": det_x,
                "detonate_world_y": det_y,
                "detonate_world_z": det_z,
                "detonate_map_x": det_map_x,
                "detonate_map_y": det_map_y,
                "detonate_layer": det_layer,
                "trajectory": [],  # Will be populated if available
            })
        
        return grenades
