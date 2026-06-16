package mapper

import (
	"encoding/json"
	"os"
)

type MapConfig struct {
	Map        string     `json:"map"`
	RadarImage string     `json:"radarImage"`
	Width      int        `json:"width"`
	Height     int        `json:"height"`
	PosX       float64    `json:"posX"`
	PosY       float64    `json:"posY"`
	Scale      float64    `json:"scale"`
	Layers     []MapLayer `json:"layers"`
}

type MapLayer struct {
	Name string  `json:"name"`
	ZMin float64 `json:"zMin"`
	ZMax float64 `json:"zMax"`
}

func LoadMapConfig(path string) (MapConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return MapConfig{}, err
	}
	var cfg MapConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return MapConfig{}, err
	}
	return cfg, nil
}

