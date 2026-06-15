"""
Tests for analysis result schemas.
"""

import pytest
from app.models.analysis_result import (
    AnalysisResult,
    Meta,
    Summary,
    Round,
    PathPoint,
    Grenade,
    GrenadeStats,
    WorldCoordinates,
    MapCoordinates,
    Position,
)


def test_world_coordinates():
    """Test WorldCoordinates model."""
    coords = WorldCoordinates(x=100.5, y=200.3, z=64.0)
    assert coords.x == 100.5
    assert coords.y == 200.3
    assert coords.z == 64.0


def test_map_coordinates():
    """Test MapCoordinates model."""
    coords = MapCoordinates(x=512.0, y=256.0)
    assert coords.x == 512.0
    assert coords.y == 256.0
    assert coords.layer == "default"


def test_path_point():
    """Test PathPoint model."""
    world = WorldCoordinates(x=100, y=200, z=64)
    map_coords = MapCoordinates(x=512, y=256)
    
    point = PathPoint(
        tick=1000,
        time_from_freeze_end=2.5,
        world=world,
        map=map_coords,
        alive=True,
        velocity=150.0,
    )
    
    assert point.tick == 1000
    assert point.time_from_freeze_end == 2.5
    assert point.world.x == 100
    assert point.alive is True
    assert point.velocity == 150.0


def test_path_point_alias():
    """Test PathPoint model with field aliases."""
    data = {
        "tick": 1000,
        "timeFromFreezeEnd": 2.5,
        "world": {"x": 100, "y": 200, "z": 64},
        "map": {"x": 512, "y": 256},
        "alive": True,
    }
    
    point = PathPoint(**data)
    assert point.tick == 1000
    assert point.time_from_freeze_end == 2.5


def test_grenade_stats():
    """Test GrenadeStats model."""
    stats = GrenadeStats(smoke=3, flash=5, he=1)
    assert stats.smoke == 3
    assert stats.flash == 5
    assert stats.he == 1
    assert stats.molotov == 0  # Default value


def test_meta():
    """Test Meta model."""
    meta = Meta(
        demo_file="test.dem",
        game="CS2",
        map="de_dust2",
        target_steam64="12345678",
        target_name="TestPlayer",
        window_seconds=30,
        tick_rate=64,
    )
    
    assert meta.demo_file == "test.dem"
    assert meta.map == "de_dust2"
    assert meta.tick_rate == 64


def test_summary():
    """Test Summary model."""
    grenades = GrenadeStats(smoke=2, flash=4)
    summary = Summary(
        total_rounds=24,
        valid_rounds=22,
        t_rounds=11,
        ct_rounds=11,
        grenades=grenades,
    )
    
    assert summary.total_rounds == 24
    assert summary.valid_rounds == 22


def test_round():
    """Test Round model with minimal data."""
    path_point = PathPoint(
        tick=1000,
        time_from_freeze_end=0.5,
        world=WorldCoordinates(x=100, y=200, z=64),
        map=MapCoordinates(x=512, y=256),
        alive=True,
    )
    
    round_data = Round(
        round_number=1,
        side="T",
        valid=True,
        freeze_end_tick=500,
        path=[path_point],
        grenades=[],
    )
    
    assert round_data.round_number == 1
    assert round_data.side == "T"
    assert len(round_data.path) == 1


def test_grenade():
    """Test Grenade model."""
    throw_pos = Position(
        world=WorldCoordinates(x=100, y=200, z=64),
        map=MapCoordinates(x=512, y=256),
    )
    detonate_pos = Position(
        world=WorldCoordinates(x=300, y=400, z=70),
        map=MapCoordinates(x=600, y=200),
    )
    
    grenade = Grenade(
        round_number=1,
        side="T",
        type="smoke",
        throw_tick=1000,
        throw_time_from_freeze_end=3.0,
        throw_position=throw_pos,
        detonate_position=detonate_pos,
        trajectory=[],
    )
    
    assert grenade.type == "smoke"
    assert grenade.round_number == 1


def test_analysis_result():
    """Test complete AnalysisResult model."""
    meta = Meta(
        demo_file="test.dem",
        game="CS2",
        map="de_dust2",
        target_steam64="12345678",
        target_name="TestPlayer",
        window_seconds=30,
        tick_rate=64,
    )
    
    summary = Summary(
        total_rounds=1,
        valid_rounds=1,
        t_rounds=1,
        ct_rounds=0,
        grenades=GrenadeStats(),
    )
    
    round_data = Round(
        round_number=1,
        side="T",
        valid=True,
        freeze_end_tick=500,
        path=[],
        grenades=[],
    )
    
    result = AnalysisResult(
        meta=meta,
        summary=summary,
        rounds=[round_data],
    )
    
    assert result.meta.map == "de_dust2"
    assert len(result.rounds) == 1
    assert result.summary.valid_rounds == 1


def test_analysis_result_json_serialization():
    """Test that AnalysisResult serializes correctly."""
    meta = Meta(
        demo_file="test.dem",
        game="CS2",
        map="de_dust2",
        target_steam64="12345678",
        target_name="TestPlayer",
        window_seconds=30,
        tick_rate=64,
    )
    
    summary = Summary(
        total_rounds=1,
        valid_rounds=1,
        t_rounds=1,
        ct_rounds=0,
        grenades=GrenadeStats(),
    )
    
    round_data = Round(
        round_number=1,
        side="T",
        valid=True,
        freeze_end_tick=500,
        path=[],
        grenades=[],
    )
    
    result = AnalysisResult(
        meta=meta,
        summary=summary,
        rounds=[round_data],
    )
    
    # Should serialize with alias names
    json_str = result.json()
    assert isinstance(json_str, str)
    assert "taskId" not in json_str  # Should not have this field
    assert "demoFile" in json_str  # Should have alias name
    
    # Should deserialize correctly
    import json as json_lib
    data = json_lib.loads(json_str)
    assert data["meta"]["demoFile"] == "test.dem"
    assert data["summary"]["totalRounds"] == 1
