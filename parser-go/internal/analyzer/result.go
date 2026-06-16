package analyzer

import "cs2-opening-analyzer/parser-go/internal/mapper"

type AnalysisResult struct {
	Meta    Meta            `json:"meta"`
	Summary Summary         `json:"summary"`
	Players []Player        `json:"players"`
	Rounds  []RoundAnalysis `json:"rounds"`
}

type Meta struct {
	DemoFile      string     `json:"demoFile"`
	Game          string     `json:"game"`
	Map           string     `json:"map"`
	TargetSteam64 string     `json:"targetSteam64"`
	TargetName    *string    `json:"targetName"`
	WindowSeconds int        `json:"windowSeconds"`
	TickRate      *float64   `json:"tickRate"`
	Parser        ParserMeta `json:"parser"`
}

type ParserMeta struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

type Summary struct {
	TotalRounds int            `json:"totalRounds"`
	ValidRounds int            `json:"validRounds"`
	TRounds     int            `json:"tRounds"`
	CTRounds    int            `json:"ctRounds"`
	Grenades    GrenadeSummary `json:"grenades"`
}

type GrenadeSummary struct {
	Smoke       int `json:"smoke"`
	Flash       int `json:"flash"`
	HE          int `json:"he"`
	Molotov     int `json:"molotov"`
	Incendiary  int `json:"incendiary"`
	Unknown     int `json:"unknown"`
}

type Player struct {
	Name    string `json:"name"`
	Steam64 string `json:"steam64"`
}

type RoundAnalysis struct {
	RoundNumber      int             `json:"roundNumber"`
	Side             string          `json:"side"`
	Valid            bool            `json:"valid"`
	InvalidReason    *string         `json:"invalidReason"`
	FreezeEndTick    *int            `json:"freezeEndTick"`
	WindowEndTick    *int            `json:"windowEndTick"`
	TimeWindowSource string          `json:"timeWindowSource"`
	EquipmentValue   *int            `json:"equipmentValue"`
	RoundType         *string         `json:"roundType"`
	Path             []PathPoint     `json:"path"`
	Grenades         []GrenadeEvent  `json:"grenades"`
}

type WorldPoint struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type PathPoint struct {
	Tick              int             `json:"tick"`
	TimeFromFreezeEnd float64         `json:"timeFromFreezeEnd"`
	World             WorldPoint      `json:"world"`
	Map               mapper.MapPoint `json:"map"`
	Alive             bool            `json:"alive"`
	Velocity          *float64        `json:"velocity"`
}

type PositionedPoint struct {
	World WorldPoint      `json:"world"`
	Map   mapper.MapPoint `json:"map"`
}

type GrenadeEvent struct {
	RoundNumber             int                       `json:"roundNumber"`
	Side                    string                    `json:"side"`
	Type                    string                    `json:"type"`
	ThrowTick               int                       `json:"throwTick"`
	ThrowTimeFromFreezeEnd  float64                   `json:"throwTimeFromFreezeEnd"`
	ThrowPosition           PositionedPoint           `json:"throwPosition"`
	DetonatePosition        *PositionedPoint          `json:"detonatePosition"`
	TrajectorySource        string                    `json:"trajectorySource"`
	Trajectory              []GrenadeTrajectoryPoint  `json:"trajectory"`
}

type GrenadeTrajectoryPoint struct {
	Tick          int             `json:"tick"`
	TimeFromThrow float64         `json:"timeFromThrow"`
	World         WorldPoint      `json:"world"`
	Map           mapper.MapPoint `json:"map"`
}

