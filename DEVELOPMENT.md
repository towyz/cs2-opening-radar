# CS2 Opening Analyzer MVP - Development Guide

This document outlines the CS2 Opening Analyzer MVP project structure, setup instructions, and development phases.

## Project Overview

The CS2 Opening Analyzer is a tool for analyzing Counter-Strike 2 demo files to extract and visualize a target player's opening behavior within the first 30 seconds after freeze time ends.

**MVP Scope:**
- Parse single CS2 demo files
- Support de_dust2 map only
- Extract player movement routes
- Extract grenade usage (type, throw position, detonation position, trajectory)
- Visualize on 2D map radar
- Show player summary card with statistics

## Project Structure

```
cs2-opening-analyzer/
├── backend/                          # Python backend (FastAPI)
│   ├── app/
│   │   ├── main.py                  # FastAPI application
│   │   ├── config.py                # Configuration
│   │   ├── api/
│   │   │   ├── routes.py            # API endpoints
│   │   │   └── schemas.py           # Request/response schemas
│   │   ├── core/
│   │   │   ├── analyzer.py          # Main analysis orchestration
│   │   │   ├── demo_loader.py       # Demo file loading
│   │   │   ├── round_extractor.py   # Round identification
│   │   │   ├── player_path.py       # Player path extraction
│   │   │   ├── grenade_extractor.py # Grenade extraction
│   │   │   ├── map_mapper.py        # Coordinate transformation
│   │   │   └── summary_builder.py   # Summary statistics
│   │   ├── models/
│   │   │   └── analysis_result.py   # Data schemas
│   │   ├── assets/
│   │   │   └── maps/de_dust2/
│   │   │       ├── map.json         # Map configuration
│   │   │       └── radar.png        # Radar image (placeholder)
│   │   └── storage/
│   │       ├── uploads/             # Uploaded demo files
│   │       └── results/             # Analysis results (JSON)
│   ├── scripts/
│   │   ├── spike_parse_demo.py
│   │   ├── spike_extract_player_path.py
│   │   └── spike_extract_grenades.py
│   ├── tests/
│   │   ├── test_map_mapper.py
│   │   └── test_analysis_schema.py
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts            # Backend API client
│   │   ├── components/
│   │   │   ├── UploadPanel.tsx      # File upload form
│   │   │   ├── OpponentCard.tsx     # Player info card
│   │   │   ├── MapViewer.tsx        # Map visualization
│   │   │   └── *.css
│   │   ├── types/
│   │   │   └── analysis.ts          # Type definitions
│   │   ├── App.tsx                  # Main App component
│   │   ├── App.css
│   │   └── main.tsx                 # Entry point
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── README.md
│
├── README.md                         # This file
└── .gitignore
```

## Getting Started

### Backend Setup

1. **Install Python 3.9+**

2. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run backend server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   API will be available at http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend Setup

1. **Install Node.js 16+**

2. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at http://localhost:5173

### Running Tests

**Backend tests:**
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app  # With coverage
```

## Development Phases

### Phase 1: Demo Parsing Validation ✓ Complete
- [x] Created backend project skeleton
- [x] Created data models (AnalysisResult)
- [x] Created map mapper module with coordinate transformation
- [x] Created map mapper tests
- [x] Created analysis schema tests
- [x] Created spike scripts for validation (spike_parse_demo.py, spike_extract_player_path.py, spike_extract_grenades.py)

**Next:** Test spike scripts with actual demo files to validate demo parsing capabilities.

### Phase 2: Core Analysis Modules (In Progress)
- [x] Created demo_loader.py
- [x] Created round_extractor.py
- [x] Created player_path.py
- [x] Created grenade_extractor.py
- [x] Created summary_builder.py
- [x] Created analyzer.py (main orchestration)
- [ ] Test all modules with real demo data
- [ ] Fix any issues with demo parsing library compatibility
- [ ] Implement missing features (player side detection, trajectory handling)

### Phase 3: FastAPI Implementation (In Progress)
- [x] Created FastAPI app structure
- [x] Created API routes and schemas
- [x] Implemented `/api/analyze` endpoint
- [x] Implemented `/api/results/{task_id}` endpoint
- [x] Implemented `/api/maps/de_dust2/config` endpoint
- [ ] Test endpoints with curl/Postman
- [ ] Add error handling and validation
- [ ] Test file upload handling

### Phase 4: Frontend Implementation (In Progress)
- [x] Created React + Vite + TypeScript project
- [x] Created type definitions
- [x] Created API client
- [x] Created UploadPanel component
- [x] Created OpponentCard component
- [x] Created MapViewer component
- [x] Created styling (CSS)
- [ ] Test frontend with backend
- [ ] Implement map image loading
- [ ] Add filtering and interactivity

### Phase 5: Integration & Polish (Pending)
- [ ] End-to-end testing
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] Documentation
- [ ] Deployment setup

## Key API Endpoints

### POST /api/analyze
Upload demo and analyze player behavior.

**Request:**
```
Content-Type: multipart/form-data

demo: File (.dem)
steam64: string (e.g., "76561198123456789")
map_name: string (default: "de_dust2")
window_seconds: number (default: 30)
```

**Response:**
```json
{
  "taskId": "uuid",
  "result": {
    "meta": {...},
    "summary": {...},
    "rounds": [...]
  }
}
```

### GET /api/results/{task_id}
Retrieve previously saved analysis result.

### GET /api/maps/de_dust2/config
Get map configuration (dimensions, coordinate system).

### GET /api/maps/de_dust2/radar
Get radar image.

## Data Structures

### AnalysisResult
```python
{
  "meta": {
    "demoFile": "example.dem",
    "game": "CS2",
    "map": "de_dust2",
    "targetSteam64": "76561198...",
    "targetName": "PlayerName",
    "windowSeconds": 30,
    "tickRate": 64
  },
  "summary": {
    "totalRounds": 24,
    "validRounds": 22,
    "tRounds": 11,
    "ctRounds": 11,
    "grenades": {
      "smoke": 4,
      "flash": 7,
      "he": 2,
      "molotov": 3,
      "incendiary": 1,
      "unknown": 0
    }
  },
  "rounds": [
    {
      "roundNumber": 1,
      "side": "T",
      "valid": true,
      "freezeEndTick": 12345,
      "equipmentValue": null,
      "roundType": null,
      "path": [...],
      "grenades": [...]
    }
  ]
}
```

## Important Notes

1. **Demo Parsing Library:** The project uses `awpy` for demo parsing. If it doesn't support certain features, fallback to `demoparser2`.

2. **Radar Image:** The de_dust2 radar image is not included in the repository. Place your radar image at `backend/app/assets/maps/de_dust2/radar.png` or the frontend will show a placeholder.

3. **Coordinate System:** 
   - World coordinates are from the demo (X, Y, Z in game units)
   - Map coordinates are radar positions (scaled to match radar image)
   - Transformation happens on backend; frontend just displays pre-computed coordinates

4. **Path Sampling:** Paths are sampled at 0.2-second intervals (configurable) to avoid sending too much data.

5. **Grenade Types:** smoke, flash, he, molotov, incendiary, unknown

## Testing

### Backend
```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_map_mapper.py -v

# Run spike scripts
python scripts/spike_parse_demo.py path/to/demo.dem
python scripts/spike_extract_player_path.py path/to/demo.dem <steam64>
python scripts/spike_extract_grenades.py path/to/demo.dem <steam64>
```

### Frontend
```bash
cd frontend

# Linting
npm run lint

# Build
npm run build

# Type checking
npm run type-check  # If available
```

## Deployment

### Backend
The backend can be deployed as a standard FastAPI application:
- Use gunicorn/uvicorn as the server
- Set environment variables for upload/results directories
- Ensure demo file size limits are appropriate for your server

### Frontend
Build the frontend and serve the static files:
```bash
npm run build
# Serve frontend/dist/ with any web server
```

Configure the API URL for production environment.

## Contributing

1. Follow the project structure
2. Add tests for new features
3. Run linting before committing
4. Keep components small and reusable
5. Use TypeScript for frontend, type hints for backend

## Troubleshooting

**Backend won't start:**
- Ensure Python 3.9+ is installed
- Check virtual environment is activated
- Run `pip install -e ".[dev]"` again

**Frontend can't connect to backend:**
- Ensure backend is running on http://localhost:8000
- Check CORS settings in `backend/app/main.py`
- Look at browser console for error messages

**Demo parsing fails:**
- Check demo file is valid CS2 format
- Verify demo file is not corrupted
- Run spike_parse_demo.py to debug

**Player not found in demo:**
- Check Steam64 ID is correct
- Run spike_parse_demo.py to see available players

## Resources

- [Awpy Documentation](https://github.com/pnxenopoulos/awpy)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
