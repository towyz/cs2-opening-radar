# Backend

FastAPI service for uploading a CS2 demo, invoking the Go parser CLI, and returning the standard analysis result.

## Endpoints

- `GET /api/health`
- `POST /api/analyze`

`POST /api/analyze` expects multipart form data:

- `demo`: `.dem` file
- `steam64`: target Steam64
- `map_name`: defaults to `de_dust2`
- `window_seconds`: defaults to `30`

