package mapper

type MapPoint struct {
	X     float64 `json:"x"`
	Y     float64 `json:"y"`
	Layer string  `json:"layer"`
}

func WorldToMap(cfg MapConfig, worldX float64, worldY float64, worldZ float64) MapPoint {
	layer := "default"
	for _, candidate := range cfg.Layers {
		if worldZ >= candidate.ZMin && worldZ <= candidate.ZMax {
			layer = candidate.Name
			break
		}
	}
	return MapPoint{
		X:     (worldX - cfg.PosX) / cfg.Scale,
		Y:     (cfg.PosY - worldY) / cfg.Scale,
		Layer: layer,
	}
}

