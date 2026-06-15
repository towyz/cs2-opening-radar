"""
Tests for grenade extraction module.
"""

import pytest
from app.core.grenade_extractor import GrenadeExtractor


class TestGrenadeClassification:
    """Tests for grenade type classification."""
    
    def test_classify_smoke_grenade(self):
        """Test smoke grenade classification."""
        assert GrenadeExtractor.classify_grenade("smokegrenade") == "smoke"
        assert GrenadeExtractor.classify_grenade("smoke") == "smoke"
        assert GrenadeExtractor.classify_grenade("Smoke_Grenade") == "smoke"
        assert GrenadeExtractor.classify_grenade("SMOKEGRENADE") == "smoke"
    
    def test_classify_flash_grenade(self):
        """Test flash grenade classification."""
        assert GrenadeExtractor.classify_grenade("flashbang") == "flash"
        assert GrenadeExtractor.classify_grenade("flash") == "flash"
        assert GrenadeExtractor.classify_grenade("Flashbang") == "flash"
        assert GrenadeExtractor.classify_grenade("FLASH") == "flash"
    
    def test_classify_he_grenade(self):
        """Test HE grenade classification."""
        assert GrenadeExtractor.classify_grenade("hegrenade") == "he"
        assert GrenadeExtractor.classify_grenade("he") == "he"
        assert GrenadeExtractor.classify_grenade("HE_Grenade") == "he"
        assert GrenadeExtractor.classify_grenade("HEGRENADE") == "he"
    
    def test_classify_molotov_grenade(self):
        """Test Molotov grenade classification."""
        assert GrenadeExtractor.classify_grenade("molotov") == "molotov"
        assert GrenadeExtractor.classify_grenade("Molotov") == "molotov"
        assert GrenadeExtractor.classify_grenade("MOLOTOV") == "molotov"
    
    def test_classify_incendiary_grenade(self):
        """Test incendiary grenade classification."""
        assert GrenadeExtractor.classify_grenade("incendiary") == "incendiary"
        assert GrenadeExtractor.classify_grenade("Incendiary") == "incendiary"
        assert GrenadeExtractor.classify_grenade("INCENDIARY") == "incendiary"
    
    def test_classify_unknown_grenade(self):
        """Test unknown grenade classification."""
        assert GrenadeExtractor.classify_grenade("unknown_type") == "unknown"
        assert GrenadeExtractor.classify_grenade("random_weapon") == "unknown"
        assert GrenadeExtractor.classify_grenade("") == "unknown"
    
    def test_classify_none_grenade(self):
        """Test None weapon name classification."""
        assert GrenadeExtractor.classify_grenade(None) == "unknown"
    
    def test_classify_case_insensitive(self):
        """Test case insensitive classification."""
        assert GrenadeExtractor.classify_grenade("SmokeGrenade") == "smoke"
        assert GrenadeExtractor.classify_grenade("FlashBang") == "flash"
        assert GrenadeExtractor.classify_grenade("HeGrenade") == "he"
        assert GrenadeExtractor.classify_grenade("MoLoToV") == "molotov"
