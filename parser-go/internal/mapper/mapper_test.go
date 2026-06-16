package mapper

import "testing"

func TestWorldToMap(t *testing.T) {
	cfg := MapConfig{
		PosX:  -2476,
		PosY:  3239,
		Scale: 4.4,
		Layers: []MapLayer{
			{Name: "default", ZMin: -99999, ZMax: 99999},
		},
	}

	point := WorldToMap(cfg, -123.4, 456.7, 64)
	if point.Layer != "default" {
		t.Fatalf("expected default layer, got %s", point.Layer)
	}
	if point.X < 534 || point.X > 535 {
		t.Fatalf("unexpected x: %f", point.X)
	}
	if point.Y < 632 || point.Y > 633 {
		t.Fatalf("unexpected y: %f", point.Y)
	}
}

