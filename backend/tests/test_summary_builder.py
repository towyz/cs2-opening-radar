"""
Tests for summary builder module.
"""

import pytest
from app.core.summary_builder import SummaryBuilder
from app.models.analysis_result import GrenadeStats


class TestSummaryBuilder:
    """Tests for SummaryBuilder class."""
    
    def test_build_summary_empty_rounds(self):
        """Test building summary with empty rounds."""
        summary = SummaryBuilder.build_summary([], [])
        
        assert summary.total_rounds == 0
        assert summary.valid_rounds == 0
        assert summary.t_rounds == 0
        assert summary.ct_rounds == 0
        assert summary.grenades.smoke == 0
        assert summary.grenades.flash == 0
    
    def test_build_summary_single_t_round(self):
        """Test building summary with a single T round."""
        rounds = [
            {"side": "T", "valid": True}
        ]
        grenades = [[]]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 1
        assert summary.valid_rounds == 1
        assert summary.t_rounds == 1
        assert summary.ct_rounds == 0
    
    def test_build_summary_single_ct_round(self):
        """Test building summary with a single CT round."""
        rounds = [
            {"side": "CT", "valid": True}
        ]
        grenades = [[]]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 1
        assert summary.valid_rounds == 1
        assert summary.t_rounds == 0
        assert summary.ct_rounds == 1
    
    def test_build_summary_mixed_rounds(self):
        """Test building summary with mixed T and CT rounds."""
        rounds = [
            {"side": "T", "valid": True},
            {"side": "CT", "valid": True},
            {"side": "T", "valid": False},
            {"side": "CT", "valid": True},
        ]
        grenades = [[], [], [], []]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 4
        assert summary.valid_rounds == 3  # One is invalid
        assert summary.t_rounds == 2
        assert summary.ct_rounds == 2
    
    def test_build_summary_unknown_side(self):
        """Test building summary with unknown side."""
        rounds = [
            {"side": "UNKNOWN", "valid": True},
            {"valid": True},  # Missing side
        ]
        grenades = [[], []]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 2
        assert summary.t_rounds == 0
        assert summary.ct_rounds == 0
    
    def test_build_summary_with_grenades(self):
        """Test building summary with grenades."""
        rounds = [{"side": "T", "valid": True}]
        grenades = [[
            {"type": "smoke"},
            {"type": "smoke"},
            {"type": "flash"},
            {"type": "he"},
            {"type": "molotov"},
        ]]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.grenades.smoke == 2
        assert summary.grenades.flash == 1
        assert summary.grenades.he == 1
        assert summary.grenades.molotov == 1
        assert summary.grenades.incendiary == 0
    
    def test_build_summary_multiple_rounds_with_grenades(self):
        """Test building summary across multiple rounds."""
        rounds = [
            {"side": "T", "valid": True},
            {"side": "CT", "valid": True},
        ]
        grenades = [
            [
                {"type": "smoke"},
                {"type": "flash"},
            ],
            [
                {"type": "he"},
                {"type": "molotov"},
                {"type": "incendiary"},
            ]
        ]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 2
        assert summary.t_rounds == 1
        assert summary.ct_rounds == 1
        assert summary.grenades.smoke == 1
        assert summary.grenades.flash == 1
        assert summary.grenades.he == 1
        assert summary.grenades.molotov == 1
        assert summary.grenades.incendiary == 1
    
    def test_build_summary_unknown_grenade_type(self):
        """Test building summary with unknown grenade type."""
        rounds = [{"side": "T", "valid": True}]
        grenades = [[
            {"type": "unknown"},
            {"type": "unknown"},
        ]]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        # Unknown grenades should be counted in the unknown field
        assert summary.grenades.unknown == 2
    
    def test_build_summary_missing_grenade_type(self):
        """Test building summary with missing grenade type."""
        rounds = [{"side": "T", "valid": True}]
        grenades = [[
            {},  # No type
            {"other_field": "value"},
        ]]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        # Missing type should default to "unknown"
        assert summary.grenades.unknown == 2
    
    def test_build_summary_default_values(self):
        """Test that default values are set correctly."""
        rounds = [
            {"valid": True},  # No side, no explicit valid
            {"side": "T"},    # No explicit valid
        ]
        grenades = [[], []]
        
        summary = SummaryBuilder.build_summary(rounds, grenades)
        
        assert summary.total_rounds == 2
        # Both should be valid by default
        assert summary.valid_rounds == 2
