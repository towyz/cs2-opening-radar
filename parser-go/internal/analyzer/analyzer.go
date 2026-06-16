package analyzer

import (
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"

	demoinfocs "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs"
	"github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/common"
	"github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/events"
)

type parseState struct {
	result          *AnalysisResult
	currentRound    int
	activeRound     *RoundAnalysis
	activeEndFrame  int
	nextSampleFrame int
	sampleStep      int
	seenPlayers     map[string]bool
	target          *common.Player
	activeGrenades  map[int64]trackedGrenade
}

type trackedGrenade struct {
	roundNumber            int
	side                   string
	grenadeType            string
	throwTick              int
	freezeEndTick          int
	tickRate               float64
	throwTimeFromFreezeEnd float64
	throwPosition          PositionedPoint
}

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
	state := &parseState{
		result:         result,
		seenPlayers:    map[string]bool{},
		activeGrenades: map[int64]trackedGrenade{},
	}

	err := demoinfocs.ParseFile(opts.DemoPath, func(parser demoinfocs.Parser) error {
		rate := parser.TickRate()
		if rate > 0 {
			result.Meta.TickRate = &rate
			state.sampleStep = sampleTickStep(rate)
		}
		if state.sampleStep == 0 {
			state.sampleStep = 13
		}
		parser.RegisterEventHandler(func(events.RoundStart) {
			state.currentRound++
			state.activeRound = nil
		})
		parser.RegisterEventHandler(func(events.RoundFreezetimeEnd) {
			collectPlayers(parser, result, state.seenPlayers)
			target := findTargetPlayer(parser, opts.Steam64)
			if target == nil {
				return
			}
			state.target = target
			startFrame := parser.CurrentFrame()
			tickRate := parser.TickRate()
			if tickRate <= 0 {
				tickRate = 64
			}
			windowEnd := startFrame + int(math.Round(tickRate*float64(opts.WindowSeconds)))
			freezeEnd := startFrame
			roundNumber := state.currentRound
			if roundNumber == 0 {
				roundNumber = len(result.Rounds) + 1
			}
			round := RoundAnalysis{
				RoundNumber:      roundNumber,
				Side:             sideFromTeam(target.Team),
				Valid:            false,
				InvalidReason:    nil,
				FreezeEndTick:    &freezeEnd,
				WindowEndTick:    &windowEnd,
				TimeWindowSource: "freeze_end_event",
				EquipmentValue:   nil,
				RoundType:        nil,
				Path:             []PathPoint{},
				Grenades:         []GrenadeEvent{},
			}
			result.Rounds = append(result.Rounds, round)
			state.activeRound = &result.Rounds[len(result.Rounds)-1]
			state.activeEndFrame = windowEnd
			state.nextSampleFrame = startFrame
		})
		parser.RegisterEventHandler(func(events.FrameDone) {
			collectPlayers(parser, result, state.seenPlayers)
			rate := parser.TickRate()
			if rate > 0 {
				result.Meta.TickRate = &rate
				state.sampleStep = sampleTickStep(rate)
			}
			samplePathPoint(parser, opts, state)
		})
		parser.RegisterEventHandler(func(e events.GrenadeProjectileThrow) {
			recordGrenadeThrow(parser, opts, state, e.Projectile)
		})
		parser.RegisterEventHandler(func(e events.GrenadeProjectileDestroy) {
			recordGrenadeDestroy(parser, opts, state, e.Projectile)
		})
		// TODO: Enrich round invalid reasons.
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
	buildSummary(result)
	return result, nil
}

func recordGrenadeThrow(parser demoinfocs.Parser, opts Options, state *parseState, projectile *common.GrenadeProjectile) {
	if state.activeRound == nil || projectile == nil || projectile.Thrower == nil {
		return
	}
	if fmt.Sprintf("%d", projectile.Thrower.SteamID64) != opts.Steam64 {
		return
	}
	frame := parser.CurrentFrame()
	if frame > state.activeEndFrame {
		return
	}
	rate := parser.TickRate()
	if rate <= 0 {
		rate = 64
	}
	freezeEnd := 0
	if state.activeRound.FreezeEndTick != nil {
		freezeEnd = *state.activeRound.FreezeEndTick
	}
	pos := projectile.Position()
	state.activeGrenades[projectile.UniqueID()] = trackedGrenade{
		roundNumber:            state.activeRound.RoundNumber,
		side:                   sideFromTeam(projectile.Thrower.Team),
		grenadeType:            grenadeType(projectile),
		throwTick:              frame,
		freezeEndTick:          freezeEnd,
		tickRate:               rate,
		throwTimeFromFreezeEnd: float64(frame-freezeEnd) / rate,
		throwPosition: PositionedPoint{
			World: WorldPoint{X: pos.X, Y: pos.Y, Z: pos.Z},
			Map:   opts.MapConfig.WorldToMap(pos.X, pos.Y, pos.Z),
		},
	}
}

func recordGrenadeDestroy(parser demoinfocs.Parser, opts Options, state *parseState, projectile *common.GrenadeProjectile) {
	if projectile == nil {
		return
	}
	tracked, ok := state.activeGrenades[projectile.UniqueID()]
	if !ok {
		return
	}
	delete(state.activeGrenades, projectile.UniqueID())
	round := findRoundByNumber(state.result, tracked.roundNumber)
	if round == nil {
		return
	}
	tracked = normalizeGrenadeStart(opts, tracked, projectile.Trajectory)
	trajectory := grenadeTrajectory(opts, tracked, projectile.Trajectory)
	detonate := detonatePosition(opts, projectile, trajectory)
	round.Grenades = append(round.Grenades, GrenadeEvent{
		RoundNumber:            tracked.roundNumber,
		Side:                   tracked.side,
		Type:                   tracked.grenadeType,
		ThrowTick:              tracked.throwTick,
		ThrowTimeFromFreezeEnd: tracked.throwTimeFromFreezeEnd,
		ThrowPosition:          tracked.throwPosition,
		DetonatePosition:       detonate,
		TrajectorySource:       trajectorySource(trajectory),
		Trajectory:             trajectory,
	})
}

func normalizeGrenadeStart(opts Options, tracked trackedGrenade, entries []common.TrajectoryEntry) trackedGrenade {
	if len(entries) == 0 {
		return tracked
	}
	first := entries[0]
	tick := trajectoryTick(first, tracked.throwTick)
	if tick == 0 || tick >= tracked.throwTick {
		return tracked
	}
	rate := tracked.tickRate
	if rate <= 0 {
		rate = 64
	}
	pos := first.Position
	tracked.throwTick = tick
	tracked.throwTimeFromFreezeEnd = float64(tick-tracked.freezeEndTick) / rate
	tracked.throwPosition = PositionedPoint{
		World: WorldPoint{X: pos.X, Y: pos.Y, Z: pos.Z},
		Map:   opts.MapConfig.WorldToMap(pos.X, pos.Y, pos.Z),
	}
	return tracked
}

func grenadeType(projectile *common.GrenadeProjectile) string {
	if projectile == nil || projectile.WeaponInstance == nil {
		return "unknown"
	}
	switch projectile.WeaponInstance.Type {
	case common.EqSmoke:
		return "smoke"
	case common.EqFlash:
		return "flash"
	case common.EqHE:
		return "he"
	case common.EqMolotov:
		return "molotov"
	case common.EqIncendiary:
		return "incendiary"
	default:
		return "unknown"
	}
}

func grenadeTrajectory(opts Options, tracked trackedGrenade, entries []common.TrajectoryEntry) []GrenadeTrajectoryPoint {
	points := make([]GrenadeTrajectoryPoint, 0, len(entries))
	rate := tracked.tickRate
	if rate <= 0 {
		rate = 64
	}
	for idx, entry := range entries {
		tick := trajectoryTick(entry, tracked.throwTick+idx)
		pos := entry.Position
		points = append(points, GrenadeTrajectoryPoint{
			Tick:          tick,
			TimeFromThrow: float64(tick-tracked.throwTick) / rate,
			World:         WorldPoint{X: pos.X, Y: pos.Y, Z: pos.Z},
			Map:           opts.MapConfig.WorldToMap(pos.X, pos.Y, pos.Z),
		})
	}
	return points
}

func trajectoryTick(entry common.TrajectoryEntry, fallback int) int {
	if entry.Tick != 0 {
		return entry.Tick
	}
	if entry.FrameID != 0 {
		return entry.FrameID
	}
	return fallback
}

func detonatePosition(opts Options, projectile *common.GrenadeProjectile, trajectory []GrenadeTrajectoryPoint) *PositionedPoint {
	if len(trajectory) > 0 {
		last := trajectory[len(trajectory)-1]
		return &PositionedPoint{World: last.World, Map: last.Map}
	}
	if projectile == nil || projectile.Entity == nil {
		return nil
	}
	pos := projectile.Position()
	return &PositionedPoint{
		World: WorldPoint{X: pos.X, Y: pos.Y, Z: pos.Z},
		Map:   opts.MapConfig.WorldToMap(pos.X, pos.Y, pos.Z),
	}
}

func trajectorySource(trajectory []GrenadeTrajectoryPoint) string {
	if len(trajectory) == 0 {
		return "missing"
	}
	return "parsed"
}

func findRoundByNumber(result *AnalysisResult, roundNumber int) *RoundAnalysis {
	for idx := range result.Rounds {
		if result.Rounds[idx].RoundNumber == roundNumber {
			return &result.Rounds[idx]
		}
	}
	return nil
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

func samplePathPoint(parser demoinfocs.Parser, opts Options, state *parseState) {
	if state.activeRound == nil {
		return
	}
	frame := parser.CurrentFrame()
	if frame > state.activeEndFrame {
		state.activeRound = nil
		return
	}
	if frame < state.nextSampleFrame {
		return
	}
	target := findTargetPlayer(parser, opts.Steam64)
	if target == nil {
		target = state.target
	}
	if target == nil {
		return
	}
	state.target = target
	rate := parser.TickRate()
	if rate <= 0 {
		rate = 64
	}
	freezeEnd := 0
	if state.activeRound.FreezeEndTick != nil {
		freezeEnd = *state.activeRound.FreezeEndTick
	}
	pos := target.Position()
	mapPoint := opts.MapConfig.WorldToMap(pos.X, pos.Y, pos.Z)
	point := PathPoint{
		Tick:              frame,
		TimeFromFreezeEnd: float64(frame-freezeEnd) / rate,
		World:             WorldPoint{X: pos.X, Y: pos.Y, Z: pos.Z},
		Map:               mapPoint,
		Alive:             target.IsAlive(),
		Velocity:          nil,
	}
	state.activeRound.Path = append(state.activeRound.Path, point)
	state.activeRound.Side = sideFromTeam(target.Team)
	state.activeRound.Valid = true
	step := state.sampleStep
	if step <= 0 {
		step = sampleTickStep(rate)
	}
	state.nextSampleFrame = frame + step
}

func findTargetPlayer(parser demoinfocs.Parser, steam64 string) *common.Player {
	for _, player := range parser.GameState().Participants().All() {
		if player == nil || player.SteamID64 == 0 {
			continue
		}
		if fmt.Sprintf("%d", player.SteamID64) == steam64 {
			return player
		}
	}
	return nil
}

func sideFromTeam(team common.Team) string {
	switch team {
	case common.TeamTerrorists:
		return "T"
	case common.TeamCounterTerrorists:
		return "CT"
	default:
		return "UNKNOWN"
	}
}

func sampleTickStep(tickRate float64) int {
	step := int(math.Round(tickRate * 0.2))
	if step < 1 {
		return 1
	}
	return step
}

func buildSummary(result *AnalysisResult) {
	result.Summary.TotalRounds = len(result.Rounds)
	result.Summary.ValidRounds = 0
	result.Summary.TRounds = 0
	result.Summary.CTRounds = 0
	result.Summary.Grenades = GrenadeSummary{}
	for idx := range result.Rounds {
		round := &result.Rounds[idx]
		if round.Valid {
			result.Summary.ValidRounds++
		}
		switch round.Side {
		case "T":
			result.Summary.TRounds++
		case "CT":
			result.Summary.CTRounds++
		}
		for _, grenade := range round.Grenades {
			switch grenade.Type {
			case "smoke":
				result.Summary.Grenades.Smoke++
			case "flash":
				result.Summary.Grenades.Flash++
			case "he":
				result.Summary.Grenades.HE++
			case "molotov":
				result.Summary.Grenades.Molotov++
			case "incendiary":
				result.Summary.Grenades.Incendiary++
			default:
				result.Summary.Grenades.Unknown++
			}
		}
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
