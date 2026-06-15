# CS2 Opening Analyzer - Frontend

React + TypeScript + Vite frontend for the CS2 demo analysis tool.

## Development Setup

### Prerequisites

- Node.js 16+ and npm/pnpm

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

The dev server is configured to proxy `/api` requests to http://localhost:8000 (the backend).

### Build

```bash
npm run build
```

Builds the frontend to `frontend/dist/`

### Linting

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts        # API client for backend communication
│   ├── components/
│   │   ├── UploadPanel.tsx   # File upload and analysis form
│   │   ├── OpponentCard.tsx  # Player info display
│   │   ├── MapViewer.tsx     # Main map visualization
│   │   └── *.css
│   ├── types/
│   │   └── analysis.ts       # Type definitions
│   ├── assets/               # Static assets
│   ├── App.tsx              # Main App component
│   ├── App.css              # App styles
│   └── main.tsx             # Entry point
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── package.json
```

## Key Features

### Upload Panel
- Drag-and-drop or click to upload `.dem` file
- Enter target player Steam64 ID
- Select map (currently only de_dust2)
- Set analysis window duration

### Opponent Card
- Display player information
- Show round statistics (total, valid, T/CT split)
- Display grenade usage statistics

### Map Viewer
- Canvas-based visualization of de_dust2 radar
- Draw player movement paths
- Draw grenade throws and detonations
- Draw grenade trajectories
- Filter by grenadeType and rounds

### Filters
- Show/hide player path
- Show/hide grenades
- Filter grenades by type

## Types

All TypeScript types are defined in `src/types/analysis.ts` and match the backend API response structure.

## API Integration

The frontend communicates with the backend API at `/api`:

- `POST /api/analyze` - Upload demo and analyze
- `GET /api/results/{task_id}` - Get previous results
- `GET /api/maps/de_dust2/config` - Get map configuration
- `GET /api/maps/de_dust2/radar` - Get radar image

See `src/api/client.ts` for the API client implementation.

## Notes

- The radar image is loaded from the backend but requires an actual image file at `backend/app/assets/maps/de_dust2/radar.png`
- Without the radar image, the map viewer shows a placeholder grid
- All coordinate transformations are done on the backend; frontend only draws pre-computed map coordinates
