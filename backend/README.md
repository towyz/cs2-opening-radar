# CS2 Opening Analyzer - Backend

This is the Python backend for the CS2 Opening Analyzer, built with FastAPI and demo parsing libraries.

## Development Setup

### Prerequisites

- Python 3.9 or later
- pip or uv for package management

### Installation

1. Install dependencies:

```bash
cd backend
pip install -e ".[dev]"
```

Or with uv:

```bash
uv pip install -e ".[dev]"
```

2. Create `.env` file if needed (optional for MVP):

```bash
# .env
UPLOAD_DIR=./app/storage/uploads
RESULTS_DIR=./app/storage/results
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API endpoints
│   │   └── schemas.py       # Request/response schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── analyzer.py      # Main orchestration logic
│   │   ├── demo_loader.py   # Demo loading and parsing
│   │   ├── round_extractor.py
│   │   ├── player_path.py
│   │   ├── grenade_extractor.py
│   │   ├── map_mapper.py    # Coordinate transformation
│   │   └── summary_builder.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── analysis_result.py
│   ├── assets/
│   │   └── maps/
│   │       └── de_dust2/
│   │           ├── map.json
│   │           └── radar.png
│   └── storage/
│       ├── uploads/
│       └── results/
├── scripts/
│   ├── spike_parse_demo.py
│   ├── spike_extract_player_path.py
│   └── spike_extract_grenades.py
├── tests/
│   ├── __init__.py
│   ├── test_map_mapper.py
│   └── test_analysis_schema.py
├── pyproject.toml
└── README.md
```

## Running the Development Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The server will be available at http://localhost:8000

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Spike Scripts

Before implementing the full system, run spike scripts to validate demo parsing:

```bash
# Parse demo and print basic info
python scripts/spike_parse_demo.py path/to/demo.dem

# Extract player path
python scripts/spike_extract_player_path.py path/to/demo.dem <steam64>

# Extract grenades
python scripts/spike_extract_grenades.py path/to/demo.dem <steam64>
```

## Running Tests

```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

## Notes

- MVP only supports CS2 demo files on de_dust2 map
- All coordinate transformations are done server-side
- Frontend receives pre-computed map coordinates
