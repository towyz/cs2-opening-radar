"""
Summary statistics builder module.
"""

from typing import Dict, List, Any
from app.models.analysis_result import Summary, GrenadeStats


class SummaryBuilder:
    """Builds summary statistics from analysis data."""
    
    @staticmethod
    def build_summary(
        rounds: List[Dict[str, Any]],
        grenades: List[List[Dict[str, Any]]],
    ) -> Summary:
        """Build summary from rounds and grenades data.
        
        Args:
            rounds: List of round dictionaries
            grenades: List of grenades per round
            
        Returns:
            Summary object
        """
        total_rounds = len(rounds)
        valid_rounds = sum(1 for r in rounds if r.get("valid", True))
        
        # Count T and CT rounds
        t_rounds = 0
        ct_rounds = 0
        for round_data in rounds:
            side = round_data.get("side", "UNKNOWN")
            if side == "T":
                t_rounds += 1
            elif side == "CT":
                ct_rounds += 1
        
        # Count grenades by type
        grenade_stats = GrenadeStats()
        all_grenades = []
        for round_grenades in grenades:
            all_grenades.extend(round_grenades)
        
        for grenade in all_grenades:
            gtype = grenade.get("type", "unknown")
            current_count = getattr(grenade_stats, gtype, 0)
            setattr(grenade_stats, gtype, current_count + 1)
        
        return Summary(
            total_rounds=total_rounds,
            valid_rounds=valid_rounds,
            t_rounds=t_rounds,
            ct_rounds=ct_rounds,
            grenades=grenade_stats,
        )
