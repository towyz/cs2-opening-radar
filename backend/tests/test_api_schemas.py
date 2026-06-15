"""
Tests for API request and response schemas.
"""

import pytest
from pydantic import ValidationError
from app.api.schemas import AnalyzeRequestSchema, PlayerSchema, ErrorDetailSchema, HealthCheckSchema


class TestAnalyzeRequestSchema:
    """Tests for AnalyzeRequestSchema."""
    
    def test_analyze_request_required_fields(self):
        """Test that steam64 is required."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequestSchema()
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('steam64',) for e in errors)
    
    def test_analyze_request_with_steam64_only(self):
        """Test creating request with only steam64."""
        request = AnalyzeRequestSchema(steam64="76561198123456789")
        
        assert request.steam64 == "76561198123456789"
        assert request.map_name == "de_dust2"  # default
        assert request.window_seconds == 30     # default
    
    def test_analyze_request_with_all_fields(self):
        """Test creating request with all fields."""
        request = AnalyzeRequestSchema(
            steam64="76561198123456789",
            map_name="de_inferno",
            window_seconds=60
        )
        
        assert request.steam64 == "76561198123456789"
        assert request.map_name == "de_inferno"
        assert request.window_seconds == 60
    
    def test_analyze_request_defaults(self):
        """Test default values."""
        request = AnalyzeRequestSchema(steam64="123")
        
        assert request.map_name == "de_dust2"
        assert request.window_seconds == 30
    
    def test_analyze_request_invalid_window_seconds(self):
        """Test with invalid window_seconds type."""
        with pytest.raises(ValidationError):
            AnalyzeRequestSchema(
                steam64="123",
                window_seconds="not_an_int"
            )
    
    def test_analyze_request_serialization(self):
        """Test request serialization."""
        request = AnalyzeRequestSchema(
            steam64="76561198123456789",
            map_name="de_mirage",
            window_seconds=45
        )
        
        data = request.model_dump()
        assert data["steam64"] == "76561198123456789"
        assert data["map_name"] == "de_mirage"
        assert data["window_seconds"] == 45


class TestPlayerSchema:
    """Tests for PlayerSchema."""
    
    def test_player_schema_creation(self):
        """Test creating player schema."""
        player = PlayerSchema(name="TestPlayer", steam64="12345678")
        
        assert player.name == "TestPlayer"
        assert player.steam64 == "12345678"
    
    def test_player_schema_required_fields(self):
        """Test that both fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerSchema(name="TestPlayer")
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('steam64',) for e in errors)
    
    def test_player_schema_serialization(self):
        """Test player schema serialization."""
        player = PlayerSchema(name="Player1", steam64="111")
        
        data = player.model_dump()
        assert data == {"name": "Player1", "steam64": "111"}


class TestErrorDetailSchema:
    """Tests for ErrorDetailSchema."""
    
    def test_error_detail_with_detail_only(self):
        """Test error detail with only detail message."""
        error = ErrorDetailSchema(detail="An error occurred")
        
        assert error.detail == "An error occurred"
        assert error.players is None
    
    def test_error_detail_with_players(self):
        """Test error detail with players list."""
        players = [
            PlayerSchema(name="Player1", steam64="111"),
            PlayerSchema(name="Player2", steam64="222"),
        ]
        error = ErrorDetailSchema(detail="Player not found", players=players)
        
        assert error.detail == "Player not found"
        assert len(error.players) == 2
        assert error.players[0].name == "Player1"
        assert error.players[1].name == "Player2"
    
    def test_error_detail_with_empty_players(self):
        """Test error detail with empty players list."""
        error = ErrorDetailSchema(detail="No players", players=[])
        
        assert error.detail == "No players"
        assert error.players == []
    
    def test_error_detail_required_detail(self):
        """Test that detail is required."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetailSchema()
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('detail',) for e in errors)


class TestHealthCheckSchema:
    """Tests for HealthCheckSchema."""
    
    def test_health_check_creation(self):
        """Test creating health check response."""
        response = HealthCheckSchema(status="ok")
        
        assert response.status == "ok"
    
    def test_health_check_different_status(self):
        """Test different status values."""
        response1 = HealthCheckSchema(status="healthy")
        response2 = HealthCheckSchema(status="degraded")
        response3 = HealthCheckSchema(status="error")
        
        assert response1.status == "healthy"
        assert response2.status == "degraded"
        assert response3.status == "error"
    
    def test_health_check_required_status(self):
        """Test that status is required."""
        with pytest.raises(ValidationError) as exc_info:
            HealthCheckSchema()
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('status',) for e in errors)
    
    def test_health_check_serialization(self):
        """Test health check serialization."""
        response = HealthCheckSchema(status="ok")
        
        data = response.model_dump()
        assert data == {"status": "ok"}
