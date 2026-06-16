package analyzer

import "cs2-opening-analyzer/parser-go/internal/mapper"

type Options struct {
	DemoPath       string
	MapName        string
	Steam64        string
	WindowSeconds  int
	MapConfig      mapper.MapConfig
	Debug          bool
}

type CodedError struct {
	Code    string
	Message string
	Extra   map[string]any
}

func (e *CodedError) Error() string {
	return e.Message
}

