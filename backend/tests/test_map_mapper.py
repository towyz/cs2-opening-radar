"""
Tests for map coordinate mapper.
"""

import pytest
import json
from pathlib import Path
import tempfile
from app.core.map_mapper import MapMapper


@pytest.fixture
def map_config_file():
    """Create a temporary map config file for testing."""
    config = {
        "map": "de_dust2",
        "radarImage": "radar.png",
        "width": 1024,
        "height": 1024,
        "posX": -2476,
        "posY": 3239,
        "scale": 4.4,
        "layers": [
            {
                "name": "default",
                "zMin": -99999,
                "zMax": 99999
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


def test_map_mapper_initialization(map_config_file):
    """Test that MapMapper initializes correctly."""
    mapper = MapMapper(map_config_file)
    assert mapper.config.map_name == "de_dust2"
    assert mapper.config.width == 1024
    assert mapper.config.height == 1024
    assert mapper.config.pos_x == -2476
    assert mapper.config.pos_y == 3239
    assert mapper.config.scale == 4.4


def test_map_mapper_file_not_found():
    """Test that MapMapper raises error for missing config."""
    with pytest.raises(FileNotFoundError):
        MapMapper("/nonexistent/path/to/map.json")


def test_world_to_map_basic(map_config_file):
    """Test basic coordinate transformation."""
    mapper = MapMapper(map_config_file)
    
    # Test with origin-like coordinates
    map_x, map_y, layer = mapper.world_to_map(world_x=-2476, world_y=3239, world_z=0)
    
    # Should be close to (0, 0) in map space
    assert abs(map_x - 0) < 0.1
    assert abs(map_y - 0) < 0.1
    assert layer == "default"


def test_world_to_map_transformation(map_config_file):
    """Test coordinate transformation with known values."""
    mapper = MapMapper(map_config_file)
    
    # Test with different coordinates
    world_x = -2476 + 442  # 100 units right
    world_y = 3239 - 442   # 100 units down (in world coords)
    
    map_x, map_y, layer = mapper.world_to_map(world_x, world_y, 0)
    
    # Formula: map_x = (world_x - pos_x) / scale
    expected_x = (world_x - (-2476)) / 4.4
    expected_y = (3239 - world_y) / 4.4
    
    assert abs(map_x - expected_x) < 0.01
    assert abs(map_y - expected_y) < 0.01
    assert layer == "default"


def test_world_to_map_layer_detection(map_config_file):
    """Test that correct layer is detected based on z coordinate."""
    mapper = MapMapper(map_config_file)
    
    # Test with z in range
    _, _, layer = mapper.world_to_map(0, 0, 500)
    assert layer == "default"
    
    # Test with z outside bounds should still return default
    _, _, layer = mapper.world_to_map(0, 0, 100000)
    assert layer == "default"


def test_get_map_info(map_config_file):
    """Test getting map information."""
    mapper = MapMapper(map_config_file)
    info = mapper.get_map_info()
    
    assert info["map"] == "de_dust2"
    assert info["width"] == 1024
    assert info["height"] == 1024
    assert info["posX"] == -2476
    assert info["posY"] == 3239
    assert info["scale"] == 4.4
    assert len(info["layers"]) == 1
    assert info["layers"][0]["name"] == "default"


def test_invalid_config():
    """Test that invalid config raises ValueError."""
    invalid_config = {
        "map": "de_dust2",
        # Missing required fields
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            MapMapper(temp_path)
    finally:
        Path(temp_path).unlink()
