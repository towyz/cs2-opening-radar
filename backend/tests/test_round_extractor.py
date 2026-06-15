"""
Tests for round extraction module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.core.round_extractor import RoundExtractor


@pytest.fixture
def mock_demo_loader():
    """Create a mock DemoLoader for testing."""
    loader = Mock()
    loader.get_tick_rate.return_value = 64
    return loader


class TestRoundExtractorFindFreezeEndTick:
    """Tests for finding freeze end ticks."""
    
    def test_find_freeze_end_tick_with_freezeEndTick(self, mock_demo_loader):
        """Test finding freeze end tick with camelCase field."""
        extractor = RoundExtractor(mock_demo_loader)
        round_data = {"freezeEndTick": 1000}
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick == 1000
    
    def test_find_freeze_end_tick_with_snake_case(self, mock_demo_loader):
        """Test finding freeze end tick with snake_case field."""
        extractor = RoundExtractor(mock_demo_loader)
        round_data = {"freeze_end_tick": 2000}
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick == 2000
    
    def test_find_freeze_end_tick_with_start_tick(self, mock_demo_loader):
        """Test finding freeze end tick with startTick field."""
        extractor = RoundExtractor(mock_demo_loader)
        round_data = {"startTick": 500}
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick == 500
    
    def test_find_freeze_end_tick_with_tick_field(self, mock_demo_loader):
        """Test finding freeze end tick with tick field."""
        extractor = RoundExtractor(mock_demo_loader)
        round_data = {"tick": 1500}
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick == 1500
    
    def test_find_freeze_end_tick_start_tick_returned_directly(self, mock_demo_loader):
        """Test that start_tick field is returned directly (not computed)."""
        extractor = RoundExtractor(mock_demo_loader)
        mock_demo_loader.get_tick_rate.return_value = 64
        round_data = {"start_tick": 1000}
        
        tick = extractor.find_freeze_end_tick(round_data)
        
        # start_tick should be returned directly from the candidates list
        assert tick == 1000
    
    def test_find_freeze_end_tick_priority_order(self, mock_demo_loader):
        """Test that fields are checked in correct priority order."""
        extractor = RoundExtractor(mock_demo_loader)
        
        # freezeEndTick should take priority
        round_data = {
            "freezeEndTick": 100,
            "freeze_end_tick": 200,
            "startTick": 300,
            "start_tick": 400,
            "tick": 500,
        }
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick == 100  # First priority
    
    def test_find_freeze_end_tick_not_found(self, mock_demo_loader):
        """Test when freeze end tick cannot be found."""
        extractor = RoundExtractor(mock_demo_loader)
        round_data = {"other_field": "value"}
        
        tick = extractor.find_freeze_end_tick(round_data)
        assert tick is None
    
    def test_find_freeze_end_tick_empty_dict(self, mock_demo_loader):
        """Test with empty round data."""
        extractor = RoundExtractor(mock_demo_loader)
        
        tick = extractor.find_freeze_end_tick({})
        assert tick is None


class TestRoundExtractorExtractRounds:
    """Tests for extracting rounds."""
    
    def test_extract_rounds_empty(self, mock_demo_loader):
        """Test extracting when no rounds available."""
        mock_demo_loader.get_rounds.return_value = []
        extractor = RoundExtractor(mock_demo_loader)
        
        rounds = extractor.extract_rounds()
        assert rounds == []
    
    def test_extract_rounds_single_round(self, mock_demo_loader):
        """Test extracting a single round."""
        round_data = {"some": "data"}
        mock_demo_loader.get_rounds.return_value = [round_data]
        extractor = RoundExtractor(mock_demo_loader)
        
        rounds = extractor.extract_rounds()
        
        assert len(rounds) == 1
        assert rounds[0]["round_number"] == 1
        assert rounds[0]["data"] == round_data
    
    def test_extract_rounds_multiple_rounds(self, mock_demo_loader):
        """Test extracting multiple rounds."""
        round_data_1 = {"data": 1}
        round_data_2 = {"data": 2}
        round_data_3 = {"data": 3}
        mock_demo_loader.get_rounds.return_value = [round_data_1, round_data_2, round_data_3]
        extractor = RoundExtractor(mock_demo_loader)
        
        rounds = extractor.extract_rounds()
        
        assert len(rounds) == 3
        assert rounds[0]["round_number"] == 1
        assert rounds[1]["round_number"] == 2
        assert rounds[2]["round_number"] == 3
    
    def test_extract_rounds_skips_none(self, mock_demo_loader):
        """Test that None rounds are skipped."""
        round_data_1 = {"data": 1}
        round_data_2 = None
        round_data_3 = {"data": 3}
        mock_demo_loader.get_rounds.return_value = [round_data_1, round_data_2, round_data_3]
        extractor = RoundExtractor(mock_demo_loader)
        
        rounds = extractor.extract_rounds()
        
        # Only non-None rounds should be returned, but indices should reflect original positions
        assert len(rounds) == 2
        assert rounds[0]["round_number"] == 1
        assert rounds[1]["round_number"] == 3
        assert rounds[0]["data"]["data"] == 1
        assert rounds[1]["data"]["data"] == 3


class TestRoundExtractorGetValidRounds:
    """Tests for getting valid rounds."""
    
    def test_get_valid_rounds_no_rounds(self, mock_demo_loader):
        """Test getting valid rounds when no rounds exist."""
        mock_demo_loader.get_rounds.return_value = []
        mock_demo_loader.get_frames.return_value = []
        extractor = RoundExtractor(mock_demo_loader)
        
        valid_rounds = extractor.get_valid_rounds("12345")
        assert valid_rounds == []
    
    def test_get_valid_rounds_no_freeze_end(self, mock_demo_loader):
        """Test that rounds without freeze end tick are skipped."""
        mock_demo_loader.get_rounds.return_value = [{"no": "freeze_end"}]
        mock_demo_loader.get_frames.return_value = []
        extractor = RoundExtractor(mock_demo_loader)
        
        valid_rounds = extractor.get_valid_rounds("12345")
        assert valid_rounds == []
    
    def test_get_valid_rounds_no_player_data(self, mock_demo_loader):
        """Test that rounds without player data are skipped."""
        round_data = {"freezeEndTick": 1000}
        mock_demo_loader.get_rounds.return_value = [round_data]
        
        frame = Mock()
        frame.get.return_value = 500  # tick < freeze_end_tick
        frame.player_states = []
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = RoundExtractor(mock_demo_loader)
        
        valid_rounds = extractor.get_valid_rounds("12345")
        assert valid_rounds == []
    
    def test_get_valid_rounds_with_valid_data(self, mock_demo_loader):
        """Test getting valid rounds with player position data."""
        round_data = {"freezeEndTick": 1000}
        mock_demo_loader.get_rounds.return_value = [round_data]
        
        # Create frames with player data
        frame1 = Mock()
        frame1.get.return_value = 1100  # tick > freeze_end_tick
        
        player_state = {
            "steamID": "12345",
            "x": 100.0,
            "y": 200.0,
            "alive": True,
        }
        frame1.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame1]
        
        extractor = RoundExtractor(mock_demo_loader)
        
        valid_rounds = extractor.get_valid_rounds("12345")
        
        assert len(valid_rounds) == 1
        assert valid_rounds[0][0] == 1  # round_number
        assert valid_rounds[0][1] == round_data
        assert valid_rounds[0][2] == 1000  # freeze_end_tick
    
    def test_get_valid_rounds_multiple_valid_rounds(self, mock_demo_loader):
        """Test getting multiple valid rounds."""
        round_data_1 = {"freezeEndTick": 1000}
        round_data_2 = {"freezeEndTick": 2000}
        mock_demo_loader.get_rounds.return_value = [round_data_1, round_data_2]
        
        # Create frames with player data for both rounds
        frame1 = Mock()
        frame1.get.return_value = 1100
        player_state1 = {"steamID": "12345", "x": 100, "y": 200}
        frame1.player_states = [player_state1]
        
        frame2 = Mock()
        frame2.get.return_value = 2100
        player_state2 = {"steamID": "12345", "x": 150, "y": 250}
        frame2.player_states = [player_state2]
        
        mock_demo_loader.get_frames.return_value = [frame1, frame2]
        
        extractor = RoundExtractor(mock_demo_loader)
        
        valid_rounds = extractor.get_valid_rounds("12345")
        
        assert len(valid_rounds) == 2
        assert valid_rounds[0][0] == 1
        assert valid_rounds[1][0] == 2
