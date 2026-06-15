"""
Tests for player path extraction module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.core.player_path import PlayerPathExtractor


@pytest.fixture
def mock_demo_loader():
    """Create a mock DemoLoader for testing."""
    loader = Mock()
    loader.get_tick_rate.return_value = 64
    return loader


@pytest.fixture
def mock_map_mapper():
    """Create a mock MapMapper for testing."""
    mapper = Mock()
    mapper.world_to_map.return_value = (256.0, 256.0, "default")
    return mapper


class TestPlayerPathExtractorInitialization:
    """Tests for PlayerPathExtractor initialization."""
    
    def test_initialization(self, mock_demo_loader, mock_map_mapper):
        """Test that extractor initializes correctly."""
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        assert extractor.demo_loader == mock_demo_loader
        assert extractor.map_mapper == mock_map_mapper
        assert extractor.tick_rate == 64
    
    def test_initialization_different_tick_rate(self, mock_demo_loader, mock_map_mapper):
        """Test initialization with different tick rate."""
        mock_demo_loader.get_tick_rate.return_value = 128
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        assert extractor.tick_rate == 128


class TestPlayerPathExtractorExtractPath:
    """Tests for extracting player path for a round."""
    
    def test_extract_path_empty_frames(self, mock_demo_loader, mock_map_mapper):
        """Test extracting path with no frames."""
        mock_demo_loader.get_frames.return_value = []
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert path == []
    
    def test_extract_path_frames_outside_window(self, mock_demo_loader, mock_map_mapper):
        """Test that frames outside window are ignored."""
        frame = Mock()
        frame.get.return_value = 500  # Before freeze_end_tick
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert path == []
    
    def test_extract_path_single_point(self, mock_demo_loader, mock_map_mapper):
        """Test extracting a single path point."""
        frame = Mock()
        frame.get.return_value = 1100  # tick > freeze_end_tick
        
        player_state = {
            "steamID": "12345",
            "x": 100.0,
            "y": 200.0,
            "z": 64.0,
            "alive": True,
            "velocity": 150.0,
        }
        frame.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert len(path) == 1
        assert path[0]["tick"] == 1100
        assert path[0]["world_x"] == 100.0
        assert path[0]["world_y"] == 200.0
        assert path[0]["alive"] is True
        assert path[0]["velocity"] == 150.0
        # Map conversion should have been called
        mock_map_mapper.world_to_map.assert_called()
    
    def test_extract_path_multiple_players(self, mock_demo_loader, mock_map_mapper):
        """Test that only target player is extracted."""
        frame = Mock()
        frame.get.return_value = 1100
        
        player_state_1 = {
            "steamID": "12345",
            "x": 100.0,
            "y": 200.0,
            "z": 64.0,
            "alive": True,
        }
        player_state_2 = {
            "steamID": "67890",
            "x": 200.0,
            "y": 300.0,
            "z": 64.0,
            "alive": True,
        }
        frame.player_states = [player_state_1, player_state_2]
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        # Should only extract target player
        assert len(path) == 1
        assert path[0]["world_x"] == 100.0
    
    def test_extract_path_time_calculation(self, mock_demo_loader, mock_map_mapper):
        """Test that time_from_freeze_end is calculated correctly."""
        frame = Mock()
        frame.get.return_value = 1064  # 1 second after freeze_end (64 ticks)
        
        player_state = {
            "steamID": "12345",
            "x": 100.0,
            "y": 200.0,
        }
        frame.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame]
        mock_demo_loader.get_tick_rate.return_value = 64
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert len(path) == 1
        # (1064 - 1000) / 64 = 1.0 second
        assert path[0]["time_from_freeze_end"] == pytest.approx(1.0)
    
    def test_extract_path_sampling_interval(self, mock_demo_loader, mock_map_mapper):
        """Test that sampling interval is respected."""
        # Create multiple frames in sequence
        frames = []
        for i in range(5):
            frame = Mock()
            frame.get.return_value = 1000 + i * 10  # 10 ticks apart
            player_state = {
                "steamID": "12345",
                "x": 100.0 + i,
                "y": 200.0,
            }
            frame.player_states = [player_state]
            frames.append(frame)
        
        mock_demo_loader.get_frames.return_value = frames
        
        # Mock config with sample_interval_seconds
        with patch('app.core.player_path.settings') as mock_settings:
            mock_settings.sample_interval_seconds = 0.25  # 16 ticks at 64 Hz
            
            extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
            path = extractor.extract_path_for_round("12345", 1000, 30)
            
            # Should sample approximately every 16 ticks (0.25 seconds)
            # Frames at: 1000, 1010, 1020, 1030, 1040
            # Sampling every 16 ticks would give: 1000, 1016, 1032, 1048 (but 1048+ out of window)
            # This depends on implementation details, so just verify sampling occurs
            assert len(path) > 0
            assert len(path) < 5  # Not all frames should be sampled


class TestPlayerPathExtractorGetPlayerSide:
    """Tests for getting player side."""
    
    def test_get_player_side_returns_unknown(self, mock_demo_loader, mock_map_mapper):
        """Test that get_player_side returns UNKNOWN (placeholder)."""
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        side = extractor.get_player_side("12345", {})
        
        # Current implementation returns UNKNOWN as placeholder
        assert side == "UNKNOWN"


class TestPlayerPathExtractorEdgeCases:
    """Tests for edge cases in path extraction."""
    
    def test_extract_path_missing_player_state(self, mock_demo_loader, mock_map_mapper):
        """Test handling of None player state."""
        frame = Mock()
        frame.get.return_value = 1100
        frame.player_states = [None, None]  # None player states
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert path == []
    
    def test_extract_path_missing_coordinates(self, mock_demo_loader, mock_map_mapper):
        """Test handling of missing coordinates."""
        frame = Mock()
        frame.get.return_value = 1100
        
        player_state = {
            "steamID": "12345",
            "x": 100.0,
            # Missing y coordinate
        }
        frame.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        # Should skip this frame due to missing y
        assert path == []
    
    def test_extract_path_steam64_alternative_fields(self, mock_demo_loader, mock_map_mapper):
        """Test handling of alternative steam64 field names."""
        frame = Mock()
        frame.get.return_value = 1100
        
        player_state = {
            "steam64": "12345",  # Alternative field name
            "x": 100.0,
            "y": 200.0,
            "alive": True,
        }
        frame.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert len(path) == 1
        assert path[0]["world_x"] == 100.0
    
    def test_extract_path_missing_z_coordinate(self, mock_demo_loader, mock_map_mapper):
        """Test that missing z coordinate defaults to 0."""
        frame = Mock()
        frame.get.return_value = 1100
        
        player_state = {
            "steamID": "12345",
            "x": 100.0,
            "y": 200.0,
            # No z coordinate
            "alive": True,
        }
        frame.player_states = [player_state]
        mock_demo_loader.get_frames.return_value = [frame]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert len(path) == 1
        assert path[0]["world_z"] == 0
    
    def test_extract_path_none_frame(self, mock_demo_loader, mock_map_mapper):
        """Test handling of None frames."""
        mock_demo_loader.get_frames.return_value = [None, None]
        
        extractor = PlayerPathExtractor(mock_demo_loader, mock_map_mapper)
        
        path = extractor.extract_path_for_round("12345", 1000, 30)
        
        assert path == []
