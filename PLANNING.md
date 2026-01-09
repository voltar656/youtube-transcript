# PLANNING.md

## 📌 Purpose

This document outlines the high-level vision, architecture, constraints, tech stack, tools, and conventions for the project.

> **AI Usage Prompt**
> Use the structure and decisions outlined in `PLANNING.md`.
> Reference this file at the beginning of any new conversation or coding session.

---

## 🧭 Project Overview

**Goal**: Provide a lightweight, production-ready microservice that extracts YouTube transcripts (with timestamps) for downstream automation (workflows, research, summarization).

**Scope**:

- Expose stable transcript extraction APIs (`/health`, `POST /transcript`, optional `GET /transcript`).
- Return transcript segments with timestamps and metadata (`video_id`, `language_code`, `is_generated`).
- Package as a Docker container.

Non-goals (for initial version):

- Full user authentication/authorization.
- Persistent storage/database.
- Complex multi-tenant rate limiting beyond basic controls.

---

## 🏗️ Architecture

- **Transport Layer**: HTTP
- **Protocol**: REST (JSON)
- **Framework**: FastAPI (Python 3.11+) served by Uvicorn
- **Database**: None (in-memory caching for repeated requests)
- **Caching**: Simple in-memory cache with TTL (transcripts don't change frequently)

**Core libraries**:

- Transcript library: `youtube-transcript-api`
- Data validation: Pydantic (via FastAPI)
- Caching: `cachetools` (TTL-based LRU cache)
- Rate limiting: `slowapi` (prevent accidental abuse)

**Deployment target**:

- Docker container (via Docker Compose for easy local development)

---

## 🧩 Components

### Component 1: API Service (FastAPI)

Responsibilities:

- Provide `/health` for liveness/readiness checks.
- Provide `/transcript` endpoint(s) to fetch and optionally merge transcript segments.
- Provide export endpoints: `/transcript/export` (JSON, TXT, SRT formats).
- Translate library errors into meaningful HTTP responses.
- Serve OpenAPI docs at `/docs` (FastAPI default).
- Implement in-memory caching to avoid repeated YouTube API calls.

### Component 2: Transcript Extraction (Service Layer)

Located in `app/service.py`.

**Caching implementation** (in-memory with 24-hour TTL):

```python
from cachetools import TTLCache

transcript_cache = TTLCache(maxsize=100, ttl=86400)  # 100 items, 24 hours

def fetch_transcript(video_id: str, language_codes: list[str] | None = None):
    cache_key = f"{video_id}:{','.join(language_codes or ['en'])}"
    if cache_key in transcript_cache:
        return transcript_cache[cache_key]

    result = YouTubeTranscriptApi().fetch(video_id, languages=language_codes)
    transcript_cache[cache_key] = result
    return result
```

**Timeout handling**:

```python
import concurrent.futures

def fetch_with_timeout(video_id: str, timeout: int = 30):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(YouTubeTranscriptApi().fetch, video_id)
        return future.result(timeout=timeout)
```

Key functions:

- `extract_video_id(video_url_or_id: str) -> str`
  - Robust extraction from full YouTube URLs, short URLs, embed URLs, and raw IDs.

- `fetch_transcript(video_id: str, language_codes: list[str] | None = None)`
  - Default `language_codes = ["en"]`.
  - Use `YouTubeTranscriptApi().fetch(video_id, languages=language_codes)`.
  - Add 30-second timeout to prevent hanging requests.
  - Convert results to normalized list of dicts/segments with `text`, `start`, `duration`.

- `merge_segments(segments, threshold: float) -> list[dict]`
  - Optional merging when gap between consecutive segments is `<= threshold`.
  - Recompute `start`, `duration`, and merged `text`.

- `format_export(segments: list[dict], format: str, video_id: str) -> str`
  - Convert segments to TXT, SRT, or JSON format.
  - TXT format: `[HH:MM:SS.mmm] Transcript text`
  - SRT format: Standard subtitle format with sequential numbering

Error mapping (service → API):

- `TranscriptsDisabled` → HTTP 403
- `NoTranscriptFound` → HTTP 404
- `VideoUnavailable` → HTTP 404
- Other unexpected errors → HTTP 500

### Component 3: Web UI (Next.js + Tailwind)

Responsibilities:

- Provide a simple web interface for fetching and viewing YouTube transcripts.
- Allow users to input video URL/ID, select language, and configure merge threshold.
- Display transcript segments with timestamps.
- Call the FastAPI `/transcript` endpoint.

Tech stack:

- Framework: Next.js (App Router)
- Styling: Tailwind CSS
- HTTP client: native `fetch` API

Key features:

- Input form with video URL/ID field.
- Language selector (default: English).
- Optional merge threshold slider/input.
- Transcript display with clickable timestamps (copy to clipboard, jump to video time).
- Export buttons for JSON, TXT, and SRT formats.
- Error handling with user-friendly messages.
- Loading states during transcript fetch.

---

## 🎨 Web UI Architecture

### Frontend structure

```text
web/
├── app/
│   ├── layout.tsx        # Root layout + ErrorBoundary
│   ├── page.tsx          # Main transcript page
│   └── globals.css       # Tailwind directives
├── components/
│   ├── ErrorBoundary.tsx       # Error boundary component
│   ├── TranscriptForm.tsx      # Input form
│   ├── TranscriptDisplay.tsx   # Segments display
│   ├── Segment.tsx             # Individual segment
│   └── ExportButtons.tsx       # Export format buttons
├── lib/
│   ├── api.ts            # API client functions
│   └── formatters.ts     # Export format formatters
└── package.json
```

**Error Boundary** (`ErrorBoundary.tsx`):

```tsx
"use client";

class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h2 className="text-red-800 font-bold">Something went wrong</h2>
          <p className="text-red-600">{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

Wrap main page in `layout.tsx`.

### API integration

- Base URL configurable via `NEXT_PUBLIC_API_URL` environment variable.
- `POST /transcript` endpoint called from client components.
- `GET /transcript/export` endpoint for downloads.
- Response type matches `TranscriptResponse` schema.

**Export buttons component** (`ExportButtons.tsx`):

```tsx
const ExportButtons = ({ videoId, segments }) => {
  const handleExport = async (format: "json" | "txt" | "srt") => {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/transcript/export?video_id=${videoId}&format=${format}`;
    window.open(url, "_blank");
  };

  return (
    <div className="flex gap-2 mb-4">
      <button onClick={() => handleExport("json")}>JSON</button>
      <button onClick={() => handleExport("txt")}>TXT</button>
      <button onClick={() => handleExport("srt")}>SRT</button>
    </div>
  );
};
```

### Development commands

- Install deps: `cd web && npm install`
- Run dev: `cd web && npm run dev`
- Build: `cd web && npm run build`
- Start prod: `cd web && npm start`
- Run both services: `docker-compose up --build` (from root)

---

## ⚙️ Environment Configuration

### Backend (FastAPI)

Expected environment variables (if/when needed):

- `LOG_LEVEL`: logging level (e.g., `INFO`, `DEBUG`).
- `ALLOWED_ORIGINS`: CORS origins (comma-separated) for web UI access.
- `CACHE_TTL_SECONDS`: cache duration (default: 86400).
- `RATE_LIMIT_PER_MINUTE`: requests per minute (default: 10).

**Structured logging implementation**:

```python
import logging
import uuid
import json
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "request_id": request_id_ctx.get(),
            "message": record.getMessage(),
            **getattr(record, "extra", {})
        }
        return json.dumps(log_data)

# Middleware to set request ID
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)

    logger.info("Request started", extra={
        "path": request.url.path,
        "method": request.method
    })

    response = await call_next(request)

    logger.info("Request completed", extra={
        "status_code": response.status_code
    })

    return response
```

Include `video_id` and `segment_count` in logs when available.

### Frontend (Next.js)

- `NEXT_PUBLIC_API_URL`: Backend API base URL (default: `http://localhost:8000`).

Secrets management:

- Prefer environment variables or `.env` files (add to `.gitignore`).
- No secrets should be committed into the repo.
- For Docker Compose, use `.env` file or `docker-compose.override.yml`.

### Example `.env.example`

```bash
# Backend
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📁 File Structure

Intended directory structure:

```text
.
├── app/
│   ├── main.py          # FastAPI entrypoint + routes
│   ├── models.py        # Pydantic request/response schemas
│   └── service.py       # YouTube transcript logic
├── web/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── TranscriptForm.tsx
│   │   ├── TranscriptDisplay.tsx
│   │   └── Segment.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts     # TypeScript types matching API schemas
│   ├── Dockerfile
│   └── package.json
├── .env.example         # Example environment variables
├── Dockerfile
├── pyproject.toml       # preferred (uv/poetry) OR requirements.txt
└── tests/
    ├── test_extract_video_id.py
    ├── test_merge_segments.py
    └── test_fetch_transcript.py
```

---

## 🧾 API Contracts

**Note**: The API must include CORS headers to allow the web UI to make requests.

Configure CORS middleware in `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Set `ALLOWED_ORIGINS` in `.env` or environment:

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://your-internal-domain.com
```

**Rate limiting** (using `slowapi`):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/transcript")
@limiter.limit("10/minute")  # Adjust based on your needs
async def get_transcript(request: Request, ...):
    ...
```

Configure limits based on expected usage (e.g., 10 requests/minute is generous for 20 requests/week).

**Input validation** (in `app/models.py`):

```python
from pydantic import BaseModel, HttpUrl, field_validator

class TranscriptRequest(BaseModel):
    video_url: str | None = None
    video_id: str | None = None
    language_codes: list[str] | None = None
    merge_threshold_seconds: float | None = None

    @field_validator("video_url", "video_id")
    @classmethod
    def validate_video_identifier(cls, v, info):
        if not v:
            raise ValueError("Either video_url or video_id must be provided")
        if v and len(v) > 500:
            raise ValueError("Video identifier too long")
        return v
```

**Sanitization** (in `app/service.py`):

```python
import re

def sanitize_video_id(video_id: str) -> str:
    """Extract and validate YouTube video ID."""
    # Allow only alphanumeric, dash, underscore (11 char video IDs)
    video_id = re.sub(r"[^a-zA-Z0-9_-]", "", video_id)
    if len(video_id) not in [11, 12]:  # Most IDs are 11 chars
        raise ValueError("Invalid video ID format")
    return video_id
```

### Request model: `TranscriptRequest`

- `video_url: str | None`
- `video_id: str | None`
- `language_codes: list[str] | None` (default: `["en"]`)
- `merge_threshold_seconds: float | None`

### Response model: `TranscriptResponse`

- `video_id: str`
- `language_code: str`
- `is_generated: bool`
- `segments: list[Segment]`

### Segment model: `Segment`

- `start: float` (seconds)
- `duration: float`
- `text: str`

Optional (recommended):

- `end: float` (computed as `start + duration`)
- `index: int`

### Error model: `ErrorResponse`

- `error: str` (error type, e.g., "TranscriptsDisabled")
- `message: str` (user-friendly message)
- `video_id: str | None` (if available)

### Endpoints

- `GET /health` → `{ "status": "ok" }`
- `POST /transcript` → request body `TranscriptRequest`, response `TranscriptResponse`
- `GET /transcript/export` → query params `video_id`, `format` (json/txt/srt), returns downloadable file

#### Export formats

- **JSON**: Full `TranscriptResponse` as downloadable `.json` file
- **TXT**: Plain text with timestamps, format: `[00:00:00.000] Transcript text`
- **SRT**: Subtitle format for video players
  ```
  1
  00:00:00,000 --> 00:00:04,500
  Transcript text here
  ```

---

## 🐳 Containerization (Docker)

- Base image: `python:3.11-slim`
- Create non-root user, `WORKDIR /app`
- Copy dependency files and install (prefer `uv` or `poetry`, fallback to `pip`)
- Copy application source
- Expose port `8000`
- Entrypoint:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## 🚀 Deployment

### Docker Compose (recommended for local dev)

Create `docker-compose.yml`:

```yaml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - ALLOWED_ORIGINS=http://localhost:3000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
```

Run with:

```bash
docker-compose up --build
```

### Single container (manual deployment)

```bash
docker build -t yt-transcript-api .
docker run -p 8000:8000 -e ALLOWED_ORIGINS=http://localhost:3000 yt-transcript-api
```

---

## 📝 Implementation Notes

### YouTube Library Volatility

The `youtube-transcript-api` breaks periodically when YouTube changes their API:

- **Monitor**: Check the library's GitHub issues monthly
- **Fallback**: Have a backup plan (e.g., AssemblyAI) if it breaks during critical research
- **Graceful degradation**: Return helpful error messages when transcripts are unavailable
- **Version pinning**: Pin to a working version in `pyproject.toml`

### Cache Strategy

With 20 requests/week, a simple in-memory cache (100 items, 24-hour TTL) is sufficient:

- Reduces YouTube API calls significantly
- Avoids rate limiting issues
- Fast responses for repeated video requests
- No complex infrastructure needed

### Export Formats

Research use cases benefit from specific formats:

- **JSON**: Machine-readable for data analysis (pandas, Excel)
- **TXT**: Human-readable with timestamps for manual review
- **SRT**: Subtitle format for adding captions to videos

Consider adding timestamp format options (HH:MM:SS vs seconds) based on user preference.

### Error Handling Best Practices

```python
# Map library errors to user-friendly messages
error_messages = {
    TranscriptsDisabled: "Transcripts are disabled for this video",
    NoTranscriptFound: "No transcript available in the requested language",
    VideoUnavailable: "This video is unavailable or private",
}
```

### Performance Optimization

- Pre-merge segments on backend to reduce frontend payload size
- Use `gzip` compression in FastAPI: `app.add_middleware(GZipMiddleware, minimum_size=1000)`
- Set reasonable merge threshold defaults (1.0-2.0 seconds works well for research)

### Security Considerations (Internal Use)

- Keep API behind internal network or require VPN access
- Add simple API key in header if exposed publicly
- Log all requests for audit trail (helpful for research tracking)

---

## 🎨 Style Guidelines

- Follow **PEP 8** and prefer explicit naming over short names.
- Use **type hints** throughout.
- Prefer Pydantic models for request/response validation.
- Keep logic split by responsibility:
  - HTTP & error translation in `app/main.py`
  - transcript logic in `app/service.py`
  - schemas in `app/models.py`

---

## 📦 Dependencies

### Backend

Declare dependencies in `pyproject.toml` (preferred via `uv` or `poetry`) or `requirements.txt`.

Required runtime deps:

- `fastapi[standard]`
- `uvicorn[standard]`
- `youtube-transcript-api`
- `pydantic` (if not already pulled in via FastAPI)
- `cachetools` (in-memory caching with TTL)
- `slowapi` (rate limiting)
- `python-multipart` (for export file downloads)

Test deps (suggested):

- `pytest`

### Frontend

Declare in `web/package.json`:

- `next` (latest)
- `react` and `react-dom`
- `tailwindcss`, `postcss`, `autoprefixer`
- `typescript`, `@types/react`, `@types/node`
- `vitest` (dev dependency for testing)

### TypeScript Types (`web/lib/types.ts`)

```typescript
// Matches backend Pydantic models
export interface Segment {
  start: number;
  duration: number;
  text: string;
  end?: number;
  index?: number;
}

export interface TranscriptResponse {
  video_id: string;
  language_code: string;
  is_generated: boolean;
  segments: Segment[];
}

export interface TranscriptRequest {
  video_url?: string;
  video_id?: string;
  language_codes?: string[];
  merge_threshold_seconds?: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  video_id?: string;
}

export type ExportFormat = "json" | "txt" | "srt";
```

### Frontend Dockerfile (`web/Dockerfile`)

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

---

## 🛠️ Tooling

- Dependency management: `uv` (preferred) or `poetry`, fallback to `pip`
- Container builds: Docker
- Docker Compose for local development with hot reload
- Observability:
  - Structured JSON logs including request ID and video ID
  - Health check endpoint for uptime monitoring
  - Optional request logging for research analytics

---

## 🔍 Monitoring & Maintenance

### Health Monitoring

Use the `/health` endpoint to check service uptime:

```bash
curl http://localhost:8000/health
# Response: { "status": "ok" }
```

Set up simple monitoring (UptimeRobot, Pingdom) to alert if the service goes down.

### Request Logging (Optional)

For research analytics, log each transcript request:

```python
import csv
from datetime import datetime

def log_request(video_id: str, segment_count: int, success: bool, language: str):
    """Log requests for research analytics."""
    with open("requests.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            video_id,
            segment_count,
            language,
            "success" if success else "failed"
        ])
```

Benefits:
- Track which videos are accessed frequently
- Identify problematic transcripts (failures)
- Generate usage reports for stakeholders

### Library Updates

Check monthly for `youtube-transcript-api` updates:

```bash
# Check current version
pip show youtube-transcript-api

# Test upgrade in dev environment
uv pip install --upgrade youtube-transcript-api
uv run pytest
```

Have a fallback plan (AssemblyAI, Speechmatics) if the library breaks during critical research.

### Log Analysis

Use simple scripts to analyze logs:

```bash
# Count requests by video (most accessed)
awk -F',' '{print $3}' requests.csv | sort | uniq -c | sort -rn | head -10

# Count failures
awk -F',' '$5 == "failed"' requests.csv | wc -l
```

---

## ✅ Constraints

- **Backend**: Python 3.11+, FastAPI + Uvicorn, `youtube-transcript-api`
- **Frontend**: Next.js (App Router), Tailwind CSS, TypeScript
- **Deployment**: Docker container (can run both services)
- **API stability**: response schema must remain stable for client workflows

Non-functional requirements:

- Add structured logging (JSON) including request ID and video ID.
- Add basic rate limiting support (slowapi).
- Add in-memory caching to reduce YouTube API calls.
- Add simple unit tests for:
  - `extract_video_id`
  - `merge_segments`
  - `fetch_transcript` (use a known public video ID)
  - `format_export` (test TXT, SRT, JSON formats)
- Add timeout handling for YouTube API calls (30-second default).
- Ensure OpenAPI works and `/docs` is accessible.
