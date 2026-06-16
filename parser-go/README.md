# Go Parser

CLI parser for CS2 demo files. It must use `github.com/markus-wa/demoinfocs-golang/v5` as the primary parser.

```powershell
go mod tidy
go build -o bin/cs2-demo-parser.exe ./cmd/cs2-demo-parser
```

Example:

```powershell
.\bin\cs2-demo-parser.exe --demo demo.dem --map de_dust2 --steam64 7656119 --window 30 --map-config ..\assets\maps\de_dust2\map.json --out result.json
```

Current implementation has the CLI, contract, map conversion, and parse entry point. Full event extraction still needs a real CS2 demo validation pass.

