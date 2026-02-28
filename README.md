# YouTube Transcript API & Web UI

A lightweight FastAPI microservice and Next.js web interface that extracts transcripts (with timestamps) from YouTube videos. Extracted transcripts can be exported as JSON, TXT, or SRT formats for research, summarization, and video workflows.

## Features

- **REST API**: FastAPI backend with `/health`, `/transcript`, and `/transcript/export` endpoints
- **Web UI**: Next.js interface for fetching, viewing, and exporting transcripts
- **Built-in API proxy**: The Next.js frontend proxies API calls to the backend — only one port needs to be exposed
- **Video Metadata**: Title, channel, upload date, duration, view count, and description
- **Export formats**: JSON (machine-readable), TXT (human-readable), SRT (subtitle format)
- **Input**: YouTube URL or video ID, optional language codes, segment merging threshold
- **Output**: Structured JSON with video metadata and timestamped segments
- **Performance**: In-memory caching with TTL, rate limiting, timeout handling
- **Production-ready**: Single Docker image, single exposed port

## Quick Start

### Docker (Recommended)

Pull from GitLab Container Registry:

```bash
docker run -d --name youtube-transcript \
  -p 3000:3000 \
  --restart unless-stopped \
  registry.gitlab.com/vikeshmalhi/youtube-transcripter:latest
```

Or build locally:

```bash
git clone https://github.com/voltar656/youtube-transcript.git
cd youtube-transcript
docker build -t youtube-transcript .
docker run -d --name youtube-transcript -p 3000:3000 --restart unless-stopped youtube-transcript
```

Open **http://localhost:3000** — the web UI and API are both served from this single port.

### Docker Compose

```bash
docker-compose up --build
```

## Architecture

The frontend proxies all `/api/*` requests to the FastAPI backend server-side. This means:

- **Single port**: Only port 3000 needs to be exposed publicly
- **No CORS issues**: The browser only talks to its own origin
- **No build-time config**: No `NEXT_PUBLIC_*` env vars needed
- **Flexible deployment**: Works in Docker, Kubernetes, or bare metal without URL configuration

```
Browser ──▶ Next.js (:3000)
              │
              ├── /           → Web UI
              ├── /api/*      → Proxy to FastAPI backend
              │                   │
              │                   ▼
              │               FastAPI (:8000, internal)
              │                   ├── /health
              │                   ├── /transcript
              │                   └── /transcript/export
              │
              └── (static assets)
```

```
.
├── app/
│   ├── main.py          # FastAPI app + routes
│   ├── models.py        # Pydantic schemas
│   └── service.py       # YouTube transcript + metadata logic
├── web/
│   ├── app/
│   │   ├── api/[...path]/ # API proxy route handler
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/      # React components
│   └── lib/             # API client, types
├── transcript.py        # Standalone CLI transcript downloader
├── Dockerfile           # Combined image
├── supervisord.conf     # Process manager config
├── docker-compose.yml   # Local deployment
└── pyproject.toml       # Python dependencies
```

## Local Development

### Backend (FastAPI)

**Prerequisites**: Python 3.11+, `uv` (recommended) or `pip`

```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)

**Prerequisites**: Node.js 20+

```bash
cd web

# Install dependencies
npm install

# Run dev server (proxies to backend at localhost:8000 by default)
npm run dev
```

During local development, the frontend dev server proxies `/api/*` to `BACKEND_URL` (default: `http://localhost:8000`).

### Running Tests

```bash
uv run pytest
```

### CLI Tool

A standalone CLI transcript downloader is also included:

```bash
# Plain text output
uv run python transcript.py "https://youtu.be/dQw4w9WgXcQ"

# JSONL output (pipe-friendly)
uv run python transcript.py dQw4w9WgXcQ --format jsonl | jq -r .text

# Multiple languages, merged segments
uv run python transcript.py dQw4w9WgXcQ --lang en --lang es --merge-threshold-seconds 1.5
```

## API Usage

All API endpoints are available through the proxy at `/api/...`, or directly on the backend at port 8000.

### Fetch Transcript

```bash
curl -X POST "http://localhost:3000/api/transcript" \
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
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "channel": "Rick Astley",
    "channel_url": "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "upload_date": "2009-10-25",
    "duration": 213,
    "view_count": 1730999238,
    "description": "The official video for..."
  },
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
curl "http://localhost:3000/api/transcript/export?video_id=dQw4w9WgXcQ&format=json" -o transcript.json

# TXT export (human-readable)
curl "http://localhost:3000/api/transcript/export?video_id=dQw4w9WgXcQ&format=txt" -o transcript.txt

# SRT export (subtitle format)
curl "http://localhost:3000/api/transcript/export?video_id=dQw4w9WgXcQ&format=srt" -o transcript.srt
```

### Health Check

```bash
curl http://localhost:3000/api/health
```

## Kubernetes Deployment

In Kubernetes, set `BACKEND_URL` on the frontend container to point to the backend service:

```yaml
env:
  - name: BACKEND_URL
    value: "http://youtube-transcript-backend:8000"
```

Only the frontend service needs an Ingress — the backend stays cluster-internal.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated) |
| `CACHE_TTL_SECONDS` | `86400` | Cache duration (default: 24 hours) |
| `RATE_LIMIT_PER_MINUTE` | `30` | Rate limit per IP address |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL for the frontend proxy (server-side only) |

## Notes

- **IP Blocking**: YouTube may block requests from cloud provider IPs. For reliable use, run on a homelab with a residential IP.
- **Merge Threshold**: Combines adjacent transcript segments when gaps are ≤ threshold. Useful for creating cleaner subtitles. For LLM processing, use raw segments (threshold = 0).

## License

MIT
