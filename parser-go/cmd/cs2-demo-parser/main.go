package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"cs2-opening-analyzer/parser-go/internal/analyzer"
	"cs2-opening-analyzer/parser-go/internal/mapper"
	"cs2-opening-analyzer/parser-go/internal/output"
)

type cliArgs struct {
	demoPath      string
	mapName       string
	steam64       string
	windowSeconds int
	mapConfigPath string
	outputPath    string
	debug         bool
}

func main() {
	args := parseFlags()
	if args.mapName != "de_dust2" {
		exitWithError("UNSUPPORTED_MAP", "MVP only supports de_dust2", nil)
	}
	if args.demoPath == "" || args.steam64 == "" || args.mapConfigPath == "" || args.outputPath == "" {
		exitWithError("INVALID_ARGUMENT", "Required flags: --demo, --map, --steam64, --map-config, --out", nil)
	}

	mapConfig, err := mapper.LoadMapConfig(args.mapConfigPath)
	if err != nil {
		exitWithError("MAP_CONFIG_ERROR", err.Error(), nil)
	}

	result, err := analyzer.Analyze(analyzer.Options{
		DemoPath:       args.demoPath,
		MapName:        args.mapName,
		Steam64:        args.steam64,
		WindowSeconds:  args.windowSeconds,
		MapConfig:      mapConfig,
		Debug:          args.debug,
	})
	if err != nil {
		if coded, ok := err.(*analyzer.CodedError); ok {
			exitWithError(coded.Code, coded.Message, coded.Extra)
		}
		exitWithError("UNKNOWN_ERROR", err.Error(), nil)
	}

	if err := output.WriteJSON(args.outputPath, result); err != nil {
		exitWithError("OUTPUT_ERROR", err.Error(), nil)
	}
	fmt.Fprintf(os.Stdout, "wrote result to %s\n", args.outputPath)
}

func parseFlags() cliArgs {
	var args cliArgs
	flag.StringVar(&args.demoPath, "demo", "", "CS2 demo file path")
	flag.StringVar(&args.mapName, "map", "de_dust2", "map name")
	flag.StringVar(&args.steam64, "steam64", "", "target player Steam64")
	flag.IntVar(&args.windowSeconds, "window", 30, "analysis window in seconds after freeze end")
	flag.StringVar(&args.mapConfigPath, "map-config", "", "map config JSON path")
	flag.StringVar(&args.outputPath, "out", "", "output result JSON path")
	flag.BoolVar(&args.debug, "debug", false, "enable debug logging")
	flag.Parse()
	return args
}

func exitWithError(code string, message string, extra map[string]any) {
	payload := map[string]any{"code": code, "message": message}
	for key, value := range extra {
		payload[key] = value
	}
	encoded, _ := json.Marshal(payload)
	fmt.Fprintln(os.Stderr, string(encoded))
	os.Exit(1)
}

