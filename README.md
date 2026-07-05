# CS2 Opening Analyzer

MVP tool for analyzing a single Counter-Strike 2 `de_dust2` demo for one target Steam64.

The parsing boundary is intentional:

1. React uploads a `.dem` and Steam64.
2. Python FastAPI saves the upload and invokes the Go CLI.
3. The Go CLI uses `github.com/markus-wa/demoinfocs-golang/v5` and writes stable `result.json`.
4. FastAPI returns the result to the frontend.
5. React renders the opponent card, player path, and grenade trajectories on the Dust2 radar.

Current status: project scaffold plus contract code. A real CS2 demo and a local Go toolchain are still required to validate the parser against `demoinfocs-golang/v5`.

## Structure

```text
backend/      Python FastAPI API and parser runner
parser-go/    Go CLI, result contract, mapper, parser entry point
frontend/     React + TypeScript + Vite UI
assets/       Shared map assets
```

## MVP Scope

- One uploaded CS2 `.dem`
- Map: `de_dust2` only
- One target Steam64
- Per-round window: freeze end to freeze end + 30 seconds
- Path samples around every 0.2 seconds
- Grenade L2 data: throw point, detonation/landing point, trajectory
- Standard `result.json` consumed by Python and frontend

## Requirements

- Go 1.22+
- Python 3.12+
- Node.js 20+
- Real `assets/maps/de_dust2/radar.png`

## Run Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

## Build Parser

```powershell
cd parser-go
go mod tidy
go build -o bin/cs2-demo-parser.exe ./cmd/cs2-demo-parser
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Local Demo Import

Create `backend/local_demo_config.json` from `backend/local_demo_config.example.json` and fill in the directories that contain your local `.dem` or `.zip` demo files.

Example:

```json
{
  "demoDirectories": [
    "C:/Users/your-name/AppData/Roaming/Wmpvp/demo",
    "D:/csgodemocache"
  ]
}
```

The backend only scans and analyzes files under these configured directories. Zip files are supported when they contain a `.dem` entry.
