"""
Map coordinate mapper for converting world coordinates to radar coordinates.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MapConfig:
    """Map configuration data."""
    map_name: str
    radar_image: str
    width: int
    height: int
    pos_x: float
    pos_y: float
    scale: float
    layers: Dict[str, Dict[str, float]]


class MapMapper:
    """Handles coordinate transformations between world and map (radar) coordinates."""

    def __init__(self, config_path: str):
        """Initialize mapper with map configuration.
        
        Args:
            config_path: Path to map.json configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Map config not found: {config_path}")
        
        with open(config_file, "r") as f:
            data = json.load(f)
        
        self.config = self._parse_config(data)
    
    @staticmethod
    def _parse_config(data: Dict[str, Any]) -> MapConfig:
        """Parse and validate map configuration."""
        try:
            layers = {}
            for layer in data.get("layers", []):
                layers[layer["name"]] = {
                    "zMin": layer["zMin"],
                    "zMax": layer["zMax"],
                }
            
            return MapConfig(
                map_name=data["map"],
                radar_image=data["radarImage"],
                width=data["width"],
                height=data["height"],
                pos_x=data["posX"],
                pos_y=data["posY"],
                scale=data["scale"],
                layers=layers,
            )
        except KeyError as e:
            raise ValueError(f"Missing required config field: {e}")
    
    def world_to_map(
        self, world_x: float, world_y: float, world_z: float
    ) -> Tuple[float, float, str]:
        """Convert world coordinates to map (radar) coordinates.
        
        Formula:
            map_x = (world_x - pos_x) / scale
            map_y = (pos_y - world_y) / scale
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            world_z: Z coordinate in world space (used for layer determination)
            
        Returns:
            Tuple of (map_x, map_y, layer_name)
        """
        map_x = (world_x - self.config.pos_x) / self.config.scale
        map_y = (self.config.pos_y - world_y) / self.config.scale
        
        # Determine layer based on z coordinate
        layer = self._get_layer_for_z(world_z)
        
        return map_x, map_y, layer
    
    def _get_layer_for_z(self, world_z: float) -> str:
        """Determine which layer a z coordinate belongs to.
        
        Args:
            world_z: Z coordinate in world space
            
        Returns:
            Layer name (default to "default" if no specific layer matches)
        """
        for layer_name, layer_info in self.config.layers.items():
            if layer_info["zMin"] <= world_z <= layer_info["zMax"]:
                return layer_name
        
        # Default to "default" layer if z doesn't match any layer bounds
        return "default"
    
    def get_map_info(self) -> Dict[str, Any]:
        """Get map information for API response."""
        return {
            "map": self.config.map_name,
            "radarImage": self.config.radar_image,
            "width": self.config.width,
            "height": self.config.height,
            "posX": self.config.pos_x,
            "posY": self.config.pos_y,
            "scale": self.config.scale,
            "layers": [
                {"name": name, "zMin": info["zMin"], "zMax": info["zMax"]}
                for name, info in self.config.layers.items()
            ],
        }
