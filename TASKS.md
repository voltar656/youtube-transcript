# TASKS.md

Tracks implementation tasks for the YouTube Transcript project.

## MVP (Script)

Goal: a pipe-friendly CLI that prints transcript *text only* to stdout.

- [x] Create `transcript.py` with args:
  - Positional: `url_or_id`
  - `--lang en` (repeatable; default `en`)
  - `--merge-threshold-seconds FLOAT` (optional; merge adjacent segments)
  - `--format {text,jsonl}` (default `text`)
- [x] `text` format prints a single plain-text transcript (no timestamps).
- [x] `jsonl` format prints one segment per line with `start`, `duration`, `text`.
- [x] Exit codes + messages:
  - 2: invalid URL/ID
  - 3: transcripts disabled/private
  - 4: no transcript found
  - 5: unexpected error
- [x] Usage examples:
  - `python3 transcript.py "https://youtu.be/VIDEO_ID"`
  - `python3 transcript.py VIDEO_ID --lang en --lang es`
  - `python3 transcript.py VIDEO_ID --format jsonl | jq -r .text | sed ...`
  - `python3 transcript.py VIDEO_ID | pbcopy`

## Backend Core Setup

- [ ] Initialize project with `uv` targeting Python 3.11+.
- [ ] Add dependencies: `fastapi[standard]`, `uvicorn[standard]`, `youtube-transcript-api`
- [ ] Add new dependencies: `cachetools`, `slowapi`, `python-multipart`
- [ ] Implement directory layout: `app/main.py`, `app/models.py`, `app/service.py`

## Backend Service Layer

- [ ] Implement `extract_video_id()` robustly (full URL, short URL, embed URL, raw ID)
- [ ] Implement `fetch_transcript(video_id, language_codes)` with 30s timeout
- [ ] Add in-memory caching with TTL (100 items, 24h)
- [ ] Implement optional `merge_segments(segments, threshold)`
- [ ] Implement `format_export(segments, format, video_id)` for JSON, TXT, SRT
- [ ] Add `sanitize_video_id()` validation (alphanumeric, dash, underscore only)
- [ ] Map `youtube-transcript-api` errors → stable HTTP status codes (403, 404, 500)

## Backend API Layer

- [ ] Define Pydantic models: `TranscriptRequest`, `TranscriptResponse`, `Segment`, `ErrorResponse`
- [ ] Add input validation with `field_validator` (length check, mutual exclusivity of url/id)
- [ ] Implement `/health` endpoint
- [ ] Implement `POST /transcript` with stable schema
- [ ] Implement `GET /transcript/export` (query params: `video_id`, `format`)
- [ ] Add CORS middleware with `ALLOWED_ORIGINS`
- [ ] Add GZip compression middleware (minimum_size=1000)
- [ ] Add rate limiting with `slowapi` (10 req/min default)
- [ ] Add structured JSON logging with request IDs (simple implementation)

## Backend Tests

- [ ] Unit tests for `extract_video_id`
- [ ] Unit tests for `merge_segments`
- [ ] Unit tests for `format_export` (JSON, TXT, SRT formats)
- [ ] Unit tests for `sanitize_video_id`
- [ ] Integration test for `fetch_transcript` using known public video ID

## Backend Deployment

- [ ] Add `Dockerfile` (python:3.11-slim, non-root user, uvicorn entrypoint)
- [ ] Add backend service to `docker-compose.yml`
- [ ] Configure environment variables in `docker-compose.yml`
- [ ] Add healthcheck to backend service
- [ ] Document build and run commands

## Frontend Core Setup

- [ ] Initialize Next.js project with TypeScript and App Router
- [ ] Add Tailwind CSS configuration
- [ ] Create directory structure: `app/`, `components/`, `lib/`
- [ ] Configure `NEXT_PUBLIC_API_URL` environment variable
- [ ] Add Vitest for testing

## Frontend Components

- [ ] Create `ErrorBoundary` component for error handling
- [ ] Create `TranscriptForm` component (URL/ID input, language selector, merge threshold)
- [ ] Create `TranscriptDisplay` component (segments list)
- [ ] Create `Segment` component (individual segment with timestamp)
- [ ] Create `ExportButtons` component (JSON, TXT, SRT buttons)

## Frontend Integration

- [ ] Implement API client functions in `lib/api.ts`
- [ ] Implement format formatters in `lib/formatters.ts`
- [ ] Integrate components in `page.tsx`
- [ ] Wrap main page with `ErrorBoundary` in `layout.tsx`
- [ ] Add loading states and error handling
- [ ] Add copy-to-clipboard functionality for timestamps

## Frontend Tests

- [ ] Add unit tests for API client functions
- [ ] Add unit tests for format formatters
- [ ] Add unit tests for utility functions
- [ ] Configure Vitest with TypeScript support

## Documentation

- [ ] Update README with quick start guide
- [ ] Document environment variables (backend and frontend)
- [ ] Document API endpoints (available at `/docs`)
- [ ] Document Docker Compose usage
- [ ] Document monitoring and maintenance procedures
- [ ] Document export formats and use cases
