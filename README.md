# YouTube Transcript API & Web UI

A lightweight FastAPI microservice and Next.js web interface that extracts transcripts (with timestamps) from YouTube videos. Extracted transcripts can be exported as JSON, TXT, or SRT formats for research, summarization, and video workflows.

## Features

- **REST API**: FastAPI backend with `/health`, `/transcript`, and `/transcript/export` endpoints
- **Web UI**: Next.js interface for fetching, viewing, and exporting transcripts
- **Export formats**: JSON (machine-readable), TXT (human-readable), SRT (subtitle format)
- **Input**: YouTube URL or video ID, optional language codes, segment merging threshold
- **Output**: Structured JSON with `video_id`, `language_code`, `is_generated`, and timestamped segments
- **Performance**: In-memory caching with TTL, rate limiting, timeout handling
- **Production-ready**: Dockerized, Docker Compose for local dev

## Quick Start

Run the full stack (backend + frontend) with Docker Compose:

```bash
docker-compose up --build
```

- Backend: http://localhost:8000 (API docs at `/docs`)
- Frontend: http://localhost:3000

## Local Development

### Backend (FastAPI)

**Prerequisites**: Python 3.11+, `uv` (recommended) or `pip`

```bash
# Install dependencies
uv sync

# Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)

**Prerequisites**: Node.js 18+

```bash
cd web

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Running Tests

```bash
# Backend tests
uv run pytest

# Run specific test
uv run pytest tests/test_service.py
```

## API Usage

### Fetch Transcript

```bash
curl -X POST "http://localhost:8000/transcript" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language_codes": ["en"],
    "merge_threshold_seconds": 1.5
  }'
```

**Response**:
```json
{
  "video_id": "dQw4w9WgXcQ",
  "language_code": "en",
  "is_generated": false,
  "segments": [
    {
      "index": 0,
      "start": 0.0,
      "duration": 4.2,
      "end": 4.2,
      "text": "We're no strangers to love..."
    }
  ]
}
```

### Export Transcript

```bash
# JSON export
curl "http://localhost:8000/transcript/export?video_id=dQw4w9WgXcQ&format=json" -o transcript.json

# TXT export (human-readable)
curl "http://localhost:8000/transcript/export?video_id=dQw4w9WgXcQ&format=txt" -o transcript.txt

# SRT export (subtitle format)
curl "http://localhost:8000/transcript/export?video_id=dQw4w9WgXcQ&format=srt" -o transcript.srt
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated) |
| `CACHE_TTL_SECONDS` | `86400` | Cache duration (default: 24 hours) |
| `RATE_LIMIT_PER_MINUTE` | `30` | Rate limit per IP address |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL (frontend) |

## Directory Structure

```
.
├── app/
│   ├── main.py          # FastAPI app + routes
│   ├── models.py        # Pydantic schemas
│   └── service.py       # YouTube transcript logic
├── web/
│   ├── app/             # Next.js App Router
│   ├── components/      # React components
│   └── lib/             # API client, types
├── tests/               # Backend tests
├── Dockerfile           # Backend Dockerfile
├── docker-compose.yml   # Full stack compose
└── pyproject.toml       # Backend dependencies
```

## License

MIT
