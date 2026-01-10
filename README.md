# YouTube Transcript API & Web UI

A lightweight FastAPI microservice and Next.js web interface that extracts transcripts (with timestamps) from YouTube videos. Extracted transcripts can be exported as JSON, TXT, or SRT formats for research, summarization, and video workflows.

## Features

- **REST API**: FastAPI backend with `/health`, `/transcript`, and `/transcript/export` endpoints
- **Web UI**: Next.js interface for fetching, viewing, and exporting transcripts
- **Video Metadata**: Title, channel, upload date, duration, view count, and description
- **Export formats**: JSON (machine-readable), TXT (human-readable), SRT (subtitle format)
- **Input**: YouTube URL or video ID, optional language codes, segment merging threshold
- **Output**: Structured JSON with video metadata and timestamped segments
- **Performance**: In-memory caching with TTL, rate limiting, timeout handling
- **Production-ready**: Single Docker image with both frontend and backend

## Quick Start

### Docker (Recommended)

Pull from GitLab Container Registry:

```bash
docker run -d --name youtube-transcript \
  -p 3000:3000 -p 8000:8000 \
  --restart unless-stopped \
  registry.gitlab.com/vikeshmalhi/youtube-transcripter:latest
```

Or build locally:

```bash
git clone https://gitlab.com/vikeshmalhi/youtube-transcripter.git
cd youtube-transcripter
docker build -t youtube-transcript .
docker run -d --name youtube-transcript -p 3000:3000 -p 8000:8000 --restart unless-stopped youtube-transcript
```

- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Docker Compose

```bash
docker-compose up --build
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

# Run dev server
npm run dev
```

### Running Tests

```bash
uv run pytest
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

## Architecture

Single Docker image running:
- **Backend**: FastAPI + uvicorn on port 8000
- **Frontend**: Next.js on port 3000
- **Process Manager**: supervisord

```
.
├── app/
│   ├── main.py          # FastAPI app + routes
│   ├── models.py        # Pydantic schemas
│   └── service.py       # YouTube transcript + metadata logic
├── web/
│   ├── app/             # Next.js App Router
│   ├── components/      # React components
│   └── lib/             # API client, types
├── Dockerfile           # Combined image
├── supervisord.conf     # Process manager config
├── docker-compose.yml   # Local deployment
└── pyproject.toml       # Python dependencies
```

## Notes

- **IP Blocking**: YouTube may block requests from cloud provider IPs. For reliable use, run on a homelab with a residential IP.
- **Merge Threshold**: Combines adjacent transcript segments when gaps are ≤ threshold. Useful for creating cleaner subtitles. For LLM processing, use raw segments (threshold = 0).

## License

MIT
