"""
Round extraction module for identifying and analyzing rounds.
"""

from typing import Optional, Dict, List, Any, Tuple
from app.core.demo_loader import DemoLoader


class RoundExtractor:
    """Extracts round information and freeze end ticks."""
    
    def __init__(self, demo_loader: DemoLoader):
        """Initialize with a demo loader.
        
        Args:
            demo_loader: Initialized DemoLoader instance
        """
        self.demo_loader = demo_loader
    
    def extract_rounds(self) -> List[Dict[str, Any]]:
        """Extract all rounds from the demo.
        
        Returns:
            List of round data dictionaries
        """
        rounds = self.demo_loader.get_rounds()
        result = []
        
        for round_idx, round_data in enumerate(rounds):
            if round_data is None:
                continue
            
            result.append({
                "round_number": round_idx + 1,
                "data": round_data,
            })
        
        return result
    
    def find_freeze_end_tick(self, round_data: Dict[str, Any]) -> Optional[int]:
        """Find the freeze end tick for a round.
        
        Args:
            round_data: Round data dictionary
            
        Returns:
            Tick number when freeze ends, or None if not found
        """
        # Try common field names
        candidates = [
            "freezeEndTick",
            "freeze_end_tick",
            "startTick",
            "start_tick",
            "tick",
        ]
        
        for field_name in candidates:
            if field_name in round_data:
                return round_data[field_name]
        
        # Try to compute from round start + freeze time
        # This is a fallback - freeze time is typically ~3 seconds at 64 tick rate
        start_tick = round_data.get("start_tick") or round_data.get("startTick")
        if start_tick is not None:
            # Assume ~3 seconds freeze time
            freeze_duration_ticks = int(3.0 * self.demo_loader.get_tick_rate())
            return start_tick + freeze_duration_ticks
        
        return None
    
    def get_valid_rounds(self, target_steam64: str) -> List[Tuple[int, Dict[str, Any], int]]:
        """Get valid rounds for a target player.
        
        A round is valid if we can find position data for the player after freeze ends.
        
        Args:
            target_steam64: Target player's Steam64 ID
            
        Returns:
            List of (round_number, round_data, freeze_end_tick) tuples
        """
        rounds = self.extract_rounds()
        frames = self.demo_loader.get_frames()
        
        valid_rounds = []
        
        for round_info in rounds:
            round_number = round_info["round_number"]
            round_data = round_info["data"]
            
            freeze_end_tick = self.find_freeze_end_tick(round_data)
            if freeze_end_tick is None:
                continue
            
            # Check if we have position data for player after freeze end
            has_position_data = False
            
            for frame in frames:
                if frame is None:
                    continue
                
                frame_tick = frame.get("tick") if hasattr(frame, "get") else None
                if frame_tick is None:
                    continue
                
                if frame_tick < freeze_end_tick:
                    continue
                
                # Check if player has position in this frame
                if hasattr(frame, "player_states"):
                    for player_state in frame.player_states:
                        if player_state is not None:
                            player_steam64 = player_state.get("steamID") or player_state.get("steam64")
                            if player_steam64 == target_steam64:
                                pos_x = player_state.get("x")
                                pos_y = player_state.get("y")
                                if pos_x is not None and pos_y is not None:
                                    has_position_data = True
                                    break
                
                if has_position_data:
                    break
            
            if has_position_data:
                valid_rounds.append((round_number, round_data, freeze_end_tick))
        
        return valid_rounds
