package analyzer

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	demoinfocs "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs"
	"github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/events"
)

func Analyze(opts Options) (*AnalysisResult, error) {
	if opts.WindowSeconds <= 0 {
		return nil, &CodedError{Code: "INVALID_ARGUMENT", Message: "window must be greater than zero"}
	}
	if _, err := os.Stat(opts.DemoPath); err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, &CodedError{Code: "DEMO_FILE_NOT_FOUND", Message: "Demo file was not found"}
		}
		return nil, &CodedError{Code: "DEMO_PARSE_FAILED", Message: err.Error()}
	}

	result, err := parseDemo(opts)
	if err != nil {
		return nil, err
	}
	if result.Meta.DemoFile == "" {
		result.Meta.DemoFile = filepath.Base(opts.DemoPath)
	}
	return result, nil
}

func parseDemo(opts Options) (*AnalysisResult, error) {
	result := newEmptyResult(opts)
	seenPlayers := map[string]bool{}

	err := demoinfocs.ParseFile(opts.DemoPath, func(parser demoinfocs.Parser) error {
		rate := parser.TickRate()
		if rate > 0 {
			result.Meta.TickRate = &rate
		}
		parser.RegisterEventHandler(func(events.FrameDone) {
			collectPlayers(parser, result, seenPlayers)
			rate := parser.TickRate()
			if rate > 0 {
				result.Meta.TickRate = &rate
			}
		})
		// TODO: Register round, tick, and grenade handlers against demoinfocs events.
		// This scaffold deliberately avoids fabricating data before real demo validation.
		return nil
	})
	if err != nil {
		return nil, &CodedError{Code: "DEMO_PARSE_FAILED", Message: fmt.Sprintf("failed to parse demo: %v", err)}
	}

	target := findPlayer(result.Players, opts.Steam64)
	if target == nil {
		players := make([]map[string]string, 0, len(result.Players))
		for _, player := range result.Players {
			players = append(players, map[string]string{"name": player.Name, "steam64": player.Steam64})
		}
		return nil, &CodedError{
			Code:    "TARGET_PLAYER_NOT_FOUND",
			Message: "Target Steam64 was not found in this demo",
			Extra:   map[string]any{"players": players},
		}
	}
	result.Meta.TargetName = &target.Name
	return result, nil
}

func collectPlayers(parser demoinfocs.Parser, result *AnalysisResult, seen map[string]bool) {
	participants := parser.GameState().Participants()
	for _, player := range participants.All() {
		if player == nil || player.SteamID64 == 0 {
			continue
		}
		steam64 := fmt.Sprintf("%d", player.SteamID64)
		if seen[steam64] {
			continue
		}
		seen[steam64] = true
		result.Players = append(result.Players, Player{
			Name:    player.Name,
			Steam64: steam64,
		})
	}
}

func newEmptyResult(opts Options) *AnalysisResult {
	return &AnalysisResult{
		Meta: Meta{
			DemoFile:      filepath.Base(opts.DemoPath),
			Game:          "CS2",
			Map:           opts.MapName,
			TargetSteam64: opts.Steam64,
			TargetName:    nil,
			WindowSeconds: opts.WindowSeconds,
			TickRate:      nil,
			Parser: ParserMeta{
				Name:    "demoinfocs-golang",
				Version: "v5",
			},
		},
		Summary: Summary{Grenades: GrenadeSummary{}},
		Players: []Player{},
		Rounds:  []RoundAnalysis{},
	}
}

func findPlayer(players []Player, steam64 string) *Player {
	for idx := range players {
		if players[idx].Steam64 == steam64 {
			return &players[idx]
		}
	}
	return nil
}
