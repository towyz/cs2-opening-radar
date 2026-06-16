package demo

import "cs2-opening-analyzer/parser-go/internal/analyzer"

func findPlayer(players []analyzer.Player, steam64 string) *analyzer.Player {
	for idx := range players {
		if players[idx].Steam64 == steam64 {
			return &players[idx]
		}
	}
	return nil
}

