"""
Demo loading and basic parsing module.
"""

from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import awpy
except ImportError:
    awpy = None

from app.config import settings


class DemoLoader:
    """Handles loading and basic parsing of CS2 demo files."""
    
    def __init__(self, demo_path: str):
        """Initialize with a demo file path.
        
        Args:
            demo_path: Path to .dem file
            
        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If file is not a .dem file
            RuntimeError: If awpy is not installed
        """
        if awpy is None:
            raise RuntimeError("awpy library is required. Install with: pip install awpy")
        
        self.demo_path = Path(demo_path)
        
        if not self.demo_path.exists():
            raise FileNotFoundError(f"Demo file not found: {demo_path}")
        
        if self.demo_path.suffix.lower() != ".dem":
            raise ValueError(f"File must be .dem, got {self.demo_path.suffix}")
        
        self.demo: Optional[awpy.Demo] = None
        self._load_demo()
    
    def _load_demo(self) -> None:
        """Load the demo file."""
        try:
            self.demo = awpy.Demo(str(self.demo_path))
        except Exception as e:
            raise RuntimeError(f"Failed to parse demo: {e}")
    
    def get_map_name(self) -> str:
        """Get the map name from the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        map_name = getattr(self.demo, "map", None)
        if map_name is None:
            raise ValueError("Could not determine map from demo")
        
        return str(map_name).lower()
    
    def get_tick_rate(self) -> int:
        """Get the tick rate from the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        tick_rate = getattr(self.demo, "tick_rate", None)
        if tick_rate is None:
            # Fallback to default
            return settings.tick_rate_fallback
        
        return int(tick_rate)
    
    def get_players(self) -> List[Dict[str, Any]]:
        """Get list of players in the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        players = getattr(self.demo, "players", [])
        if players is None:
            return []
        
        result = []
        for player in players:
            if player is not None:
                # Extract relevant fields
                result.append({
                    "name": player.get("name", "Unknown"),
                    "steam64": player.get("steam64", "Unknown"),
                    "team": player.get("team", "UNKNOWN"),
                })
        
        return result
    
    def get_player_by_steam64(self, steam64: str) -> Optional[Dict[str, Any]]:
        """Find a player by Steam64 ID."""
        players = self.get_players()
        for player in players:
            if player["steam64"] == steam64:
                return player
        return None
    
    def get_rounds(self) -> List[Dict[str, Any]]:
        """Get list of rounds from the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        rounds = getattr(self.demo, "rounds", [])
        if rounds is None:
            return []
        
        return list(rounds) if isinstance(rounds, (list, tuple)) else []
    
    def get_frames(self):
        """Get frames from the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        return getattr(self.demo, "frames", [])
    
    def get_grenades(self) -> List[Dict[str, Any]]:
        """Get grenades from the demo."""
        if self.demo is None:
            raise RuntimeError("Demo not loaded")
        
        grenades = getattr(self.demo, "grenades", [])
        if grenades is None:
            return []
        
        return list(grenades) if isinstance(grenades, (list, tuple)) else []
